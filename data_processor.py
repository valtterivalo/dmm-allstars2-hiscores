import pandas as pd
import numpy as np
from typing import Dict, List, Any
from collections import defaultdict

class DataProcessor:
    def __init__(self):
        self.team_prefixes = {
            'BB': 'B0aty Brawlers',
            'DN': 'Dino Nuggets', 
            'TT': 'Torvesta Titans',
            'SMO': 'SkillSpecs Smorcs',
            'OW': 'Odablock Warriors',
            'SNA': 'Solomission Snakes'
        }
        
        self.skills = [
            'overall', 'attack', 'defence', 'strength', 'hitpoints', 'ranged', 
            'prayer', 'magic', 'cooking', 'woodcutting', 'fletching', 'fishing',
            'firemaking', 'crafting', 'smithing', 'mining', 'herblore', 'agility',
            'thieving', 'slayer', 'farming', 'runecraft', 'hunter', 'construction'
        ]

    def get_team_from_name(self, name: str) -> str:
        """Extract team from player name based on prefix"""
        for prefix in self.team_prefixes.keys():
            if name.startswith(prefix):
                return prefix
        return "Unknown"

    def process_data(self, raw_data: Dict) -> Dict:
        """Process raw scraped data into organized team statistics"""
        # Validate input data
        if not raw_data:
            print("Warning: No raw data provided to process")
            return {}
        
        # Check if we have at least some skill data
        valid_skills = [skill for skill, data in raw_data.items() if data and len(data) > 0]
        if not valid_skills:
            print("Warning: No valid skill data found in raw data")
            return {}
        
        print(f"Processing data for {len(valid_skills)} skills with data: {', '.join(valid_skills)}")
        
        processed_data = {
            'teams': {},
            'leaderboards': {},
            'overall_stats': {},
            'last_updated': None
        }
        
        # Initialize team data structure
        for team_code, team_name in self.team_prefixes.items():
            processed_data['teams'][team_code] = {
                'name': team_name,
                'code': team_code,
                'players': [],
                'averages': {},
                'totals': {},
                'best_players': {},
                'rankings': {}
            }
        
        # Process each skill
        for skill, players_data in raw_data.items():
            if not players_data:
                print(f"Skipping {skill} - no data")
                continue
                
            # Initialize leaderboard for this skill
            processed_data['leaderboards'][skill] = []
            
            # Group players by team
            team_players = defaultdict(list)
            
            for player in players_data:
                team = self.get_team_from_name(player['name'])
                if team != "Unknown":
                    team_players[team].append(player)
                    
                    # Add to leaderboard
                    processed_data['leaderboards'][skill].append({
                        'name': player['name'],
                        'team': team,
                        'level': player['level'],
                        'xp': player['xp'],
                        'rank': player['rank']
                    })
            
            # Sort leaderboard by level first, then XP (both descending)
            processed_data['leaderboards'][skill].sort(key=lambda x: (x['level'], x['xp']), reverse=True)
            
            # Calculate team statistics for this skill
            for team_code, team_data in processed_data['teams'].items():
                players = team_players.get(team_code, [])
                
                if players:
                    # Store individual player data for this skill
                    if 'players_by_skill' not in team_data:
                        team_data['players_by_skill'] = {}
                    team_data['players_by_skill'][skill] = players
                    
                    # Update overall players list (unique players)
                    existing_names = {p.get('name') for p in team_data.get('players', [])}
                    for player in players:
                        if player['name'] not in existing_names:
                            team_data['players'].append({
                                'name': player['name'],
                                'team': team_code
                            })
                            existing_names.add(player['name'])
                    
                    # Calculate averages
                    avg_level = np.mean([p['level'] for p in players])
                    avg_xp = np.mean([p['xp'] for p in players])
                    total_xp = sum([p['xp'] for p in players])
                    total_level = sum([p['level'] for p in players])
                    
                    team_data['averages'][skill] = {
                        'level': round(avg_level, 2),
                        'xp': round(avg_xp, 0)
                    }
                    
                    team_data['totals'][skill] = {
                        'level': total_level,
                        'xp': total_xp,
                        'players': len(players)
                    }
                    
                    # Find best player in team for this skill (prioritize level, then XP)
                    best_player = max(players, key=lambda x: (x['level'], x['xp']))
                    team_data['best_players'][skill] = {
                        'name': best_player['name'],
                        'level': best_player['level'],
                        'xp': best_player['xp'],
                        'rank': best_player['rank']
                    }
                else:
                    # No players found for this team in this skill
                    team_data['averages'][skill] = {'level': 0, 'xp': 0}
                    team_data['totals'][skill] = {'level': 0, 'xp': 0, 'players': 0}
                    team_data['best_players'][skill] = None
        
        # Only proceed with rankings and stats if we have valid team data
        if any(team_data['players'] for team_data in processed_data['teams'].values()):
            # Calculate team rankings based on total XP
            self._calculate_team_rankings(processed_data)
            
            # Calculate overall statistics
            self._calculate_overall_stats(processed_data)
            
            print(f"Data processing completed successfully for {len(processed_data['teams'])} teams")
        else:
            print("Warning: No valid team data found after processing")
        
        return processed_data

    def _calculate_team_rankings(self, data: Dict):
        """Calculate team rankings for each skill"""
        for skill in self.skills:
            # Get team totals for this skill
            team_totals = []
            for team_code, team_data in data['teams'].items():
                total_level = team_data['totals'].get(skill, {}).get('level', 0)
                total_xp = team_data['totals'].get(skill, {}).get('xp', 0)
                team_totals.append((team_code, total_level, total_xp))
            
            # Sort by total level first, then total XP (both descending)
            team_totals.sort(key=lambda x: (x[1], x[2]), reverse=True)
            
            # Assign rankings
            for rank, (team_code, total_level, total_xp) in enumerate(team_totals, 1):
                data['teams'][team_code]['rankings'][skill] = rank

    def _calculate_overall_stats(self, data: Dict):
        """Calculate overall competition statistics"""
        overall_stats = {
            'total_players': 0,
            'total_teams': len(self.team_prefixes),
            'skill_leaders': {},
            'team_standings': []
        }
        
        # Determine which skill to use for overall stats
        # Prefer 'overall' but fallback to 'attack' if overall is missing/incomplete
        stats_skill = 'overall'
        if not data['leaderboards'].get('overall') or len(data['leaderboards']['overall']) < 5:
            if data['leaderboards'].get('attack') and len(data['leaderboards']['attack']) > 0:
                stats_skill = 'attack'
                print(f"Using '{stats_skill}' skill for overall stats (overall skill data insufficient)")
        
        # Count total players
        for team_data in data['teams'].values():
            # Use the determined skill to count unique players
            skill_players = team_data['totals'].get(stats_skill, {}).get('players', 0)
            overall_stats['total_players'] += skill_players
        
        # Find skill leaders (highest level first, then XP in each skill across all teams)
        for skill in self.skills:
            leaderboard = data['leaderboards'].get(skill, [])
            if leaderboard:
                leader = leaderboard[0]  # Already sorted by level then XP descending
                overall_stats['skill_leaders'][skill] = leader
        
        # Calculate team standings based on the determined skill's total level first, then total XP
        team_standings = []
        for team_code, team_data in data['teams'].items():
            total_level = team_data['totals'].get(stats_skill, {}).get('level', 0)
            total_xp = team_data['totals'].get(stats_skill, {}).get('xp', 0)
            avg_level = team_data['averages'].get(stats_skill, {}).get('level', 0)
            avg_xp = team_data['averages'].get(stats_skill, {}).get('xp', 0)
            team_standings.append({
                'team': team_code,
                'name': team_data['name'],
                'total_level': total_level,
                'total_xp': total_xp,
                'avg_level': avg_level,
                'avg_xp': avg_xp,
                'players': team_data['totals'].get(stats_skill, {}).get('players', 0)
            })
        
        team_standings.sort(key=lambda x: (x['total_level'], x['total_xp']), reverse=True)
        
        # Add rankings
        for rank, team in enumerate(team_standings, 1):
            team['rank'] = rank
        
        overall_stats['team_standings'] = team_standings
        overall_stats['stats_skill_used'] = stats_skill  # Track which skill was used
        data['overall_stats'] = overall_stats

    def compare_teams(self, teams_data: Dict, team1: str, team2: str) -> Dict:
        """Generate comparison data between two teams"""
        if team1 not in teams_data or team2 not in teams_data:
            return {'error': 'One or both teams not found'}
        
        team1_data = teams_data[team1]
        team2_data = teams_data[team2]
        
        comparison = {
            'team1': {
                'code': team1,
                'name': team1_data['name'],
                'data': team1_data
            },
            'team2': {
                'code': team2,
                'name': team2_data['name'],
                'data': team2_data
            },
            'skill_comparison': {},
            'summary': {}
        }
        
        # Compare each skill
        team1_wins = 0
        team2_wins = 0
        
        for skill in self.skills:
            team1_avg_level = team1_data['averages'].get(skill, {}).get('level', 0)
            team2_avg_level = team2_data['averages'].get(skill, {}).get('level', 0)
            team1_avg_xp = team1_data['averages'].get(skill, {}).get('xp', 0)
            team2_avg_xp = team2_data['averages'].get(skill, {}).get('xp', 0)
            
            team1_total_level = team1_data['totals'].get(skill, {}).get('level', 0)
            team2_total_level = team2_data['totals'].get(skill, {}).get('level', 0)
            team1_total_xp = team1_data['totals'].get(skill, {}).get('xp', 0)
            team2_total_xp = team2_data['totals'].get(skill, {}).get('xp', 0)
            
            winner = None
            # Compare by total level first, then total XP
            if team1_total_level > team2_total_level:
                winner = team1
                team1_wins += 1
            elif team2_total_level > team1_total_level:
                winner = team2
                team2_wins += 1
            elif team1_total_xp > team2_total_xp:
                winner = team1
                team1_wins += 1
            elif team2_total_xp > team1_total_xp:
                winner = team2
                team2_wins += 1
            
            comparison['skill_comparison'][skill] = {
                'team1_avg_level': team1_avg_level,
                'team2_avg_level': team2_avg_level,
                'team1_avg_xp': team1_avg_xp,
                'team2_avg_xp': team2_avg_xp,
                'team1_total_level': team1_total_level,
                'team2_total_level': team2_total_level,
                'team1_total_xp': team1_total_xp,
                'team2_total_xp': team2_total_xp,
                'winner': winner,
                'level_difference': abs(team1_total_level - team2_total_level),
                'xp_difference': abs(team1_total_xp - team2_total_xp)
            }
        
        # Summary
        comparison['summary'] = {
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
            'ties': len(self.skills) - team1_wins - team2_wins,
            'overall_winner': team1 if team1_wins > team2_wins else team2 if team2_wins > team1_wins else 'tie'
        }
        
        return comparison

    def get_heatmap_data(self, teams_data: Dict) -> Dict:
        """Generate heatmap data for team comparison visualization"""
        heatmap_data = {
            'teams': list(self.team_prefixes.keys()),
            'skills': self.skills,
            'data': []
        }
        
        # Create matrix of team averages for each skill
        for skill in self.skills:
            skill_row = []
            for team in heatmap_data['teams']:
                avg_xp = teams_data.get(team, {}).get('averages', {}).get(skill, {}).get('xp', 0)
                skill_row.append(avg_xp)
            heatmap_data['data'].append(skill_row)
        
        return heatmap_data 
    
    def _check_data_quality(self, raw_data: Dict) -> Dict:
        """Check if skill data is properly differentiated or if all skills show same data"""
        quality_info = {
            'skills_have_unique_data': True,
            'identical_skills': [],
            'warning_message': None
        }
        
        if not raw_data or len(raw_data) < 2:
            return quality_info
        
        # Compare overall vs other skills to see if they're identical
        overall_data = raw_data.get('overall', [])
        if not overall_data:
            return quality_info
        
        # Check if other skills have identical data to overall
        identical_skills = []
        for skill, skill_data in raw_data.items():
            if skill == 'overall' or not skill_data:
                continue
                
            # Compare first few players to see if data is identical
            if len(skill_data) >= 3 and len(overall_data) >= 3:
                # Check if the first 3 players have identical stats
                overall_sample = [(p['name'], p['level'], p['xp']) for p in overall_data[:3]]
                skill_sample = [(p['name'], p['level'], p['xp']) for p in skill_data[:3]]
                
                if overall_sample == skill_sample:
                    identical_skills.append(skill)
        
        if len(identical_skills) > 5:  # If more than 5 skills are identical, likely all are
            quality_info['skills_have_unique_data'] = False
            quality_info['identical_skills'] = identical_skills
            quality_info['warning_message'] = (
                "Tournament hiscores are currently displaying overall total levels "
                "and XP for all skill categories. Individual skill statistics are not available."
            )
        
        return quality_info