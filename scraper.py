import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Tuple
import urllib.parse

class DeadmanScraper:
    def __init__(self):
        self.base_url = "https://secure.runescape.com/m=hiscore_oldschool_tournament"
        self.skills = [
            'overall', 'attack', 'defence', 'strength', 'hitpoints', 'ranged', 
            'prayer', 'magic', 'cooking', 'woodcutting', 'fletching', 'fishing',
            'firemaking', 'crafting', 'smithing', 'mining', 'herblore', 'agility',
            'thieving', 'slayer', 'farming', 'runecraft', 'hunter', 'construction'
        ]
        
        # Team prefixes based on the competition
        self.team_prefixes = {
            'BB': 'B0aty Brawlers',
            'DN': 'Dino Nuggets', 
            'TT': 'Torvesta Titans',
            'SMO': 'SkillSpecs Smorcs',
            'OW': 'Odablock Warriors',
            'SNA': 'Solomission Snakes'
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_skill_table_id(self, skill: str) -> int:
        """Get the table ID for a specific skill"""
        skill_mapping = {
            'overall': 0, 'attack': 1, 'defence': 2, 'strength': 3, 'hitpoints': 4,
            'ranged': 5, 'prayer': 6, 'magic': 7, 'cooking': 8, 'woodcutting': 9,
            'fletching': 10, 'fishing': 11, 'firemaking': 12, 'crafting': 13,
            'smithing': 14, 'mining': 15, 'herblore': 16, 'agility': 17,
            'thieving': 18, 'slayer': 19, 'farming': 20, 'runecraft': 21,
            'hunter': 22, 'construction': 23
        }
        return skill_mapping.get(skill, 0)

    def get_all_player_names(self) -> List[str]:
        """Get all player names from the overall hiscores"""
        all_players = []
        
        # Scrape pages 1 and 2 of overall hiscores to get all player names
        for page in [1, 2]:
            table_id = self.get_skill_table_id('overall')
            url = f"{self.base_url}/overall?table={table_id}&page={page}"
            
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                rows = soup.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        try:
                            name_cell = cells[1]
                            
                            # Extract player name
                            name_link = name_cell.find('a')
                            if name_link:
                                name = name_link.get_text(strip=True)
                            else:
                                name = name_cell.get_text(strip=True)
                            
                            # Fix character encoding issues
                            name = name.replace('Ā', ' ').replace('ā', ' ').replace('\u0100', ' ').replace('\u0101', ' ').strip()
                            name = ''.join(c if ord(c) < 128 else ' ' for c in name)
                            name = ' '.join(name.split())
                            
                            # Skip if name is empty or contains headers
                            if not name or 'Rank' in name or 'Name' in name:
                                continue
                                
                            # Skip referees
                            if name.startswith('Ref'):
                                continue
                            
                            # Only include team players
                            if any(name.startswith(prefix) for prefix in self.team_prefixes.keys()):
                                all_players.append(name)
                                
                        except (ValueError, AttributeError):
                            continue
                            
                time.sleep(0.5)  # Be respectful
                
            except requests.RequestException as e:
                print(f"Error getting player names from page {page}: {e}")
        
        return list(set(all_players))  # Remove duplicates

    def scrape_player_stats(self, player_name: str) -> Dict[str, Dict]:
        """Scrape all stats for a specific player from their personal hiscore page"""
        # URL encode the player name
        encoded_name = urllib.parse.quote(player_name)
        url = f"{self.base_url}/hiscorepersonal?user1={encoded_name}"
        
        player_stats = {}
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the table with player stats
            rows = soup.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 4:
                    try:
                        skill_cell = cells[0]
                        rank_cell = cells[1]
                        level_cell = cells[2]
                        xp_cell = cells[3]
                        
                        # Extract skill name
                        skill_text = skill_cell.get_text(strip=True).lower()
                        
                        # Skip if not a valid skill
                        if skill_text not in self.skills:
                            continue
                        
                        # Extract rank, level, and XP
                        rank_text = rank_cell.get_text(strip=True)
                        level_text = level_cell.get_text(strip=True)
                        xp_text = xp_cell.get_text(strip=True)
                        
                        # Clean and convert values
                        rank = int(re.sub(r'[^\d]', '', rank_text)) if rank_text and rank_text != '-' else 0
                        level = int(re.sub(r'[^\d]', '', level_text)) if level_text else 1
                        xp = int(re.sub(r'[^\d]', '', xp_text)) if xp_text else 0
                        
                        player_stats[skill_text] = {
                            'rank': rank,
                            'name': player_name,
                            'level': level,
                            'xp': xp,
                            'skill': skill_text
                        }
                        
                    except (ValueError, AttributeError):
                        continue
            
        except requests.RequestException as e:
            print(f"Error scraping stats for {player_name}: {e}")
        
        return player_stats

    def scrape_all_data(self) -> Dict:
        """Scrape all skills data for all competitors using skill table approach with correct URLs"""
        all_data = {}
        successful_skills = 0
        failed_skills = []
        
        print("Starting to scrape all skills data using corrected skill table URLs...")
        
        for skill in self.skills:
            print(f"Scraping {skill}...")
            skill_data = []
            
            # Scrape pages 1 and 2 for each skill
            for page in [1, 2]:
                players = self.scrape_skill_page_alternative(skill, page)
                skill_data.extend(players)
                time.sleep(0.5)
            
            all_data[skill] = skill_data
            
            if len(skill_data) > 0:
                successful_skills += 1
                print(f"  {skill}: {len(skill_data)} players")
            else:
                failed_skills.append(skill)
                print(f"  {skill}: 0 players (FAILED)")
            
            time.sleep(1)  # Be respectful to the server
        
        print(f"Scraping completed. Successful skills: {successful_skills}/{len(self.skills)}")
        if failed_skills:
            print(f"Failed skills: {', '.join(failed_skills)}")
        
        # Return data even if some skills failed, as long as we have some data
        return all_data

    def scrape_skill_page_alternative(self, skill: str, page: int = 1) -> List[Dict]:
        """Alternative method: Scrape using the correct skill table URLs with retry logic"""
        table_id = self.get_skill_table_id(skill)
        url = f"{self.base_url}/overall?table={table_id}&page={page}"
        
        # Retry logic for connection issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                players = []
                rows = soup.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        try:
                            rank_text = cells[0].get_text(strip=True)
                            name_cell = cells[1]
                            level_text = cells[2].get_text(strip=True) if len(cells) > 2 else "1"
                            xp_text = cells[3].get_text(strip=True) if len(cells) > 3 else "0"
                            
                            # Extract rank
                            rank_match = re.search(r'\d+', rank_text)
                            if not rank_match:
                                continue
                            rank = int(rank_match.group())
                            
                            # Extract player name
                            name_link = name_cell.find('a')
                            if name_link:
                                name = name_link.get_text(strip=True)
                            else:
                                name = name_cell.get_text(strip=True)
                            
                            # Fix character encoding issues
                            name = name.replace('Ā', ' ').replace('ā', ' ').replace('\u0100', ' ').replace('\u0101', ' ').strip()
                            name = ''.join(c if ord(c) < 128 else ' ' for c in name)
                            name = ' '.join(name.split())
                            
                            # Skip if name is empty or contains headers
                            if not name or 'Rank' in name or 'Name' in name:
                                continue
                                
                            # Skip referees
                            if name.startswith('Ref'):
                                continue
                            
                            # Clean and convert level and XP
                            level = int(re.sub(r'[^\d]', '', level_text)) if level_text else 1
                            xp = int(re.sub(r'[^\d]', '', xp_text)) if xp_text else 0
                            
                            players.append({
                                'rank': rank,
                                'name': name,
                                'level': level,
                                'xp': xp,
                                'skill': skill
                            })
                            
                        except (ValueError, AttributeError):
                            continue
                
                # If we got here successfully, return the players
                return players
                
            except requests.RequestException as e:
                print(f"Error scraping {skill} page {page} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed to scrape {skill} page {page} after {max_retries} attempts")
                    return []
        
        return []

    def scrape_all_data_alternative(self) -> Dict:
        """Alternative method: Scrape using skill table approach with correct URLs"""
        all_data = {}
        
        print("Starting to scrape all skills data using table approach...")
        
        for skill in self.skills:
            print(f"Scraping {skill}...")
            skill_data = []
            
            # Scrape pages 1 and 2 for each skill
            for page in [1, 2]:
                players = self.scrape_skill_page_alternative(skill, page)
                skill_data.extend(players)
                time.sleep(0.5)
            
            all_data[skill] = skill_data
            time.sleep(1)  # Be respectful to the server
        
        print(f"Scraping completed. Total skills: {len(all_data)}")
        return all_data

    def get_team_from_name(self, name: str) -> str:
        """Extract team from player name based on prefix"""
        for prefix, team_name in self.team_prefixes.items():
            if name.startswith(prefix):
                return prefix
        return "Unknown"

    def get_team_display_name(self, team_code: str) -> str:
        """Get display name for team"""
        return self.team_prefixes.get(team_code, team_code) 