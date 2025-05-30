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
            
            # Sort leaderboard by XP (descending)
            processed_data['leaderboards'][skill].sort(key=lambda x: x['xp'], reverse=True)
            
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
                    
                    team_data['averages'][skill] = {
                        'level': round(avg_level, 2),
                        'xp': round(avg_xp, 0)
                    }
                    
                    team_data['totals'][skill] = {
                        'xp': total_xp,
                        'players': len(players)
                    }
                    
                    # Find best player in team for this skill
                    best_player = max(players, key=lambda x: x['xp'])
                    team_data['best_players'][skill] = {
                        'name': best_player['name'],
                        'level': best_player['level'],
                        'xp': best_player['xp'],
                        'rank': best_player['rank']
                    }
                else:
                    # No players found for this team in this skill
                    team_data['averages'][skill] = {'level': 0, 'xp': 0}
                    team_data['totals'][skill] = {'xp': 0, 'players': 0}
                    team_data['best_players'][skill] = None
        
        # Calculate team rankings based on total XP
        self._calculate_team_rankings(processed_data)
        
        # Calculate overall statistics
        self._calculate_overall_stats(processed_data)
        
        return processed_data

    def _calculate_team_rankings(self, data: Dict):
        """Calculate team rankings for each skill"""
        for skill in self.skills:
            # Get team totals for this skill
            team_totals = []
            for team_code, team_data in data['teams'].items():
                total_xp = team_data['totals'].get(skill, {}).get('xp', 0)
                team_totals.append((team_code, total_xp))
            
            # Sort by total XP (descending)
            team_totals.sort(key=lambda x: x[1], reverse=True)
            
            # Assign rankings
            for rank, (team_code, total_xp) in enumerate(team_totals, 1):
                data['teams'][team_code]['rankings'][skill] = rank

    def _calculate_overall_stats(self, data: Dict):
        """Calculate overall competition statistics"""
        overall_stats = {
            'total_players': 0,
            'total_teams': len(self.team_prefixes),
            'skill_leaders': {},
            'team_standings': []
        }
        
        # Count total players
        for team_data in data['teams'].values():
            # Use overall skill to count unique players
            overall_players = team_data['totals'].get('overall', {}).get('players', 0)
            overall_stats['total_players'] += overall_players
        
        # Find skill leaders (highest XP in each skill across all teams)
        for skill in self.skills:
            leaderboard = data['leaderboards'].get(skill, [])
            if leaderboard:
                leader = leaderboard[0]  # Already sorted by XP descending
                overall_stats['skill_leaders'][skill] = leader
        
        # Calculate team standings based on overall total XP
        team_standings = []
        for team_code, team_data in data['teams'].items():
            total_xp = team_data['totals'].get('overall', {}).get('xp', 0)
            avg_xp = team_data['averages'].get('overall', {}).get('xp', 0)
            team_standings.append({
                'team': team_code,
                'name': team_data['name'],
                'total_xp': total_xp,
                'avg_xp': avg_xp,
                'players': team_data['totals'].get('overall', {}).get('players', 0)
            })
        
        team_standings.sort(key=lambda x: x['total_xp'], reverse=True)
        
        # Add rankings
        for rank, team in enumerate(team_standings, 1):
            team['rank'] = rank
        
        overall_stats['team_standings'] = team_standings
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
            team1_avg = team1_data['averages'].get(skill, {}).get('xp', 0)
            team2_avg = team2_data['averages'].get(skill, {}).get('xp', 0)
            
            team1_total = team1_data['totals'].get(skill, {}).get('xp', 0)
            team2_total = team2_data['totals'].get(skill, {}).get('xp', 0)
            
            winner = None
            if team1_total > team2_total:
                winner = team1
                team1_wins += 1
            elif team2_total > team1_total:
                winner = team2
                team2_wins += 1
            
            comparison['skill_comparison'][skill] = {
                'team1_avg': team1_avg,
                'team2_avg': team2_avg,
                'team1_total': team1_total,
                'team2_total': team2_total,
                'winner': winner,
                'difference': abs(team1_total - team2_total)
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