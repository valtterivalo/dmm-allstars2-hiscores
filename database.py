import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
import hashlib

class HistoryDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use persistent disk in production, local file in development
            if os.environ.get('RENDER'):
                self.db_path = '/opt/render/project/data/deadman_history.db'
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                self.is_production = True
            else:
                self.db_path = 'deadman_history.db'
                self.is_production = False
        else:
            self.db_path = db_path
            self.is_production = os.environ.get('RENDER') == 'true'
        
        self.init_database()
        
        # Log database info
        if self.is_production:
            print(f"Production database initialized at: {self.db_path}")
        else:
            print(f"Development database initialized at: {self.db_path}")
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create snapshots table for storing complete data snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                data TEXT NOT NULL,
                data_hash TEXT,
                source TEXT DEFAULT 'unknown'
            )
        ''')
        
        # Create player_history table for individual player tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                skill TEXT NOT NULL,
                level INTEGER NOT NULL,
                xp INTEGER NOT NULL,
                rank INTEGER NOT NULL,
                UNIQUE(timestamp, player_name, skill) ON CONFLICT IGNORE
            )
        ''')
        
        # Create team_history table for team aggregate tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                team TEXT NOT NULL,
                skill TEXT NOT NULL,
                avg_level REAL NOT NULL,
                avg_xp INTEGER NOT NULL,
                total_xp INTEGER NOT NULL,
                players_count INTEGER NOT NULL,
                UNIQUE(timestamp, team, skill) ON CONFLICT IGNORE
            )
        ''')
        
        # Migrate existing data if needed (add missing columns)
        try:
            # Check if data_hash column exists
            cursor.execute("PRAGMA table_info(snapshots)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'data_hash' not in columns:
                cursor.execute('ALTER TABLE snapshots ADD COLUMN data_hash TEXT')
                print("Added data_hash column to snapshots table")
            
            if 'source' not in columns:
                cursor.execute('ALTER TABLE snapshots ADD COLUMN source TEXT DEFAULT "unknown"')
                print("Added source column to snapshots table")
                
        except sqlite3.OperationalError as e:
            print(f"Migration warning: {e}")
        
        # Add indexes for better performance (after ensuring columns exist)
        try:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_player_history_name_skill ON player_history(player_name, skill)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_team_history_team_skill ON team_history(team, skill)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_hash ON snapshots(data_hash)')
        except sqlite3.OperationalError as e:
            print(f"Index creation warning: {e}")
        
        conn.commit()
        conn.close()
    
    def _calculate_data_hash(self, data: Dict) -> str:
        """Calculate a hash of the data for deduplication"""
        # Create a stable hash by sorting keys and using relevant data
        relevant_data = {
            'teams_count': len(data.get('teams', {})),
            'total_players': data.get('overall_stats', {}).get('total_players', 0),
            'team_standings': str(sorted([(t['team'], t['total_xp']) for t in data.get('overall_stats', {}).get('team_standings', [])]))
        }
        data_str = json.dumps(relevant_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def save_snapshot(self, data: Dict) -> int:
        """Save a complete data snapshot with deduplication"""
        if not data or not data.get('teams'):
            print("Skipping snapshot save - no valid data")
            return 0
        
        data_hash = self._calculate_data_hash(data)
        source = 'production' if self.is_production else 'development'
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we already have this exact data in the last hour
        cursor.execute('''
            SELECT id FROM snapshots 
            WHERE data_hash = ? AND timestamp > datetime('now', '-1 hour')
            ORDER BY timestamp DESC LIMIT 1
        ''', (data_hash,))
        
        existing = cursor.fetchone()
        if existing:
            print(f"Skipping duplicate snapshot (hash: {data_hash[:8]}...)")
            conn.close()
            return existing[0]
        
        # In development, don't save if we have recent production data
        if not self.is_production:
            cursor.execute('''
                SELECT COUNT(*) FROM snapshots 
                WHERE source = 'production' AND timestamp > datetime('now', '-2 hours')
            ''')
            recent_prod_count = cursor.fetchone()[0]
            
            if recent_prod_count > 0:
                print("Development mode: Skipping save due to recent production data")
                conn.close()
                return 0
        
        cursor.execute('''
            INSERT INTO snapshots (data, data_hash, source) 
            VALUES (?, ?, ?)
        ''', (json.dumps(data), data_hash, source))
        
        snapshot_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"Saved snapshot {snapshot_id} from {source} (hash: {data_hash[:8]}...)")
        return snapshot_id
    
    def save_player_data(self, players_data: Dict):
        """Save individual player data for historical tracking with deduplication"""
        if not players_data:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # In development, don't save if we have recent production data
        if not self.is_production:
            cursor.execute('''
                SELECT COUNT(*) FROM player_history 
                WHERE timestamp > datetime('now', '-2 hours')
            ''')
            recent_count = cursor.fetchone()[0]
            
            if recent_count > 100:  # Arbitrary threshold
                print("Development mode: Skipping player data save due to recent data")
                conn.close()
                return
        
        saved_count = 0
        # Extract player data from the processed data structure
        for skill, players in players_data.items():
            for player in players:
                # Determine team from player name
                team = self._get_team_from_name(player['name'])
                
                try:
                    cursor.execute('''
                        INSERT INTO player_history 
                        (player_name, team, skill, level, xp, rank)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        player['name'],
                        team,
                        skill,
                        player['level'],
                        player['xp'],
                        player['rank']
                    ))
                    saved_count += 1
                except sqlite3.IntegrityError:
                    # Duplicate entry, skip
                    pass
        
        conn.commit()
        conn.close()
        
        if saved_count > 0:
            print(f"Saved {saved_count} new player data points")
    
    def save_team_data(self, teams_data: Dict):
        """Save team aggregate data for historical tracking with deduplication"""
        if not teams_data:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # In development, don't save if we have recent production data
        if not self.is_production:
            cursor.execute('''
                SELECT COUNT(*) FROM team_history 
                WHERE timestamp > datetime('now', '-2 hours')
            ''')
            recent_count = cursor.fetchone()[0]
            
            if recent_count > 50:  # Arbitrary threshold
                print("Development mode: Skipping team data save due to recent data")
                conn.close()
                return
        
        saved_count = 0
        for team_code, team_info in teams_data.items():
            for skill, averages in team_info.get('averages', {}).items():
                totals = team_info.get('totals', {}).get(skill, {})
                
                try:
                    cursor.execute('''
                        INSERT INTO team_history 
                        (team, skill, avg_level, avg_xp, total_xp, players_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        team_code,
                        skill,
                        averages.get('level', 0),
                        averages.get('xp', 0),
                        totals.get('xp', 0),
                        totals.get('players', 0)
                    ))
                    saved_count += 1
                except sqlite3.IntegrityError:
                    # Duplicate entry, skip
                    pass
        
        conn.commit()
        conn.close()
        
        if saved_count > 0:
            print(f"Saved {saved_count} new team data points")
    
    def get_database_stats(self) -> Dict:
        """Get statistics about the database content"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Snapshot stats
        cursor.execute('SELECT COUNT(*) FROM snapshots')
        stats['total_snapshots'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM snapshots')
        result = cursor.fetchone()
        stats['snapshot_date_range'] = {
            'earliest': result[0],
            'latest': result[1]
        }
        
        cursor.execute('SELECT source, COUNT(*) FROM snapshots GROUP BY source')
        stats['snapshots_by_source'] = dict(cursor.fetchall())
        
        # Player history stats
        cursor.execute('SELECT COUNT(*) FROM player_history')
        stats['total_player_records'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT player_name) FROM player_history')
        stats['unique_players'] = cursor.fetchone()[0]
        
        # Team history stats
        cursor.execute('SELECT COUNT(*) FROM team_history')
        stats['total_team_records'] = cursor.fetchone()[0]
        
        # Recent activity
        cursor.execute('''
            SELECT COUNT(*) FROM snapshots 
            WHERE timestamp > datetime('now', '-24 hours')
        ''')
        stats['snapshots_last_24h'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def get_player_history(self, player_name: str, skill: str = 'overall') -> List[Dict]:
        """Get historical data for a specific player and skill"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, level, xp, rank
            FROM player_history
            WHERE player_name = ? AND skill = ?
            ORDER BY timestamp ASC
        ''', (player_name, skill))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'timestamp': row[0],
                'level': row[1],
                'xp': row[2],
                'rank': row[3]
            }
            for row in results
        ]
    
    def get_team_history(self, team: str, skill: str = 'overall') -> List[Dict]:
        """Get historical data for a specific team and skill"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, avg_level, avg_xp, total_xp, players_count
            FROM team_history
            WHERE team = ? AND skill = ?
            ORDER BY timestamp ASC
        ''', (team, skill))
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                'timestamp': row[0],
                'avg_level': row[1],
                'avg_xp': row[2],
                'total_xp': row[3],
                'players_count': row[4]
            }
            for row in results
        ]
    
    def get_latest_snapshot(self) -> Dict:
        """Get the most recent data snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT data FROM snapshots
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return {}
    
    def get_all_players(self) -> List[str]:
        """Get list of all unique player names"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT player_name
            FROM player_history
            ORDER BY player_name
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in results]
    
    def _get_team_from_name(self, name: str) -> str:
        """Extract team from player name based on prefix"""
        team_prefixes = {
            'BB': 'BB',
            'DN': 'DN', 
            'TT': 'TT',
            'SMO': 'SMO',
            'OW': 'OW',
            'SNA': 'SNA'
        }
        
        for prefix in team_prefixes.keys():
            if name.startswith(prefix):
                return prefix
        return "Unknown"
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Remove data older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM snapshots 
            WHERE timestamp < datetime('now', '-{} days')
        '''.format(days_to_keep))
        
        cursor.execute('''
            DELETE FROM player_history 
            WHERE timestamp < datetime('now', '-{} days')
        '''.format(days_to_keep))
        
        cursor.execute('''
            DELETE FROM team_history 
            WHERE timestamp < datetime('now', '-{} days')
        '''.format(days_to_keep))
        
        conn.commit()
        conn.close() 