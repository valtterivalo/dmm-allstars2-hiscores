import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any
import os

class HistoryDatabase:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use persistent disk in production, local file in development
            if os.environ.get('RENDER'):
                self.db_path = '/opt/render/project/data/deadman_history.db'
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            else:
                self.db_path = 'deadman_history.db'
        else:
            self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create snapshots table for storing complete data snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                data TEXT NOT NULL
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
                rank INTEGER NOT NULL
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
                players_count INTEGER NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_snapshot(self, data: Dict) -> int:
        """Save a complete data snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO snapshots (data) VALUES (?)',
            (json.dumps(data),)
        )
        
        snapshot_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return snapshot_id
    
    def save_player_data(self, players_data: Dict):
        """Save individual player data for historical tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract player data from the processed data structure
        for skill, players in players_data.items():
            for player in players:
                # Determine team from player name
                team = self._get_team_from_name(player['name'])
                
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
        
        conn.commit()
        conn.close()
    
    def save_team_data(self, teams_data: Dict):
        """Save team aggregate data for historical tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for team_code, team_info in teams_data.items():
            for skill, averages in team_info.get('averages', {}).items():
                totals = team_info.get('totals', {}).get(skill, {})
                
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
        
        conn.commit()
        conn.close()
    
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