from nba_api.stats.endpoints import leaguegamefinder, commonplayerinfo, PlayerGameLog, LeagueLeaders, PlayerDashboardByGeneralSplits
from nba_api.stats.static import players, teams
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging

class NBADataFetcher:
    def __init__(self):
        self.teams_dict = {team['id']: team['full_name'] for team in teams.get_teams()}
        self.logger = logging.getLogger(__name__)
        
    def get_active_players(self) -> list:
        """
        Get list of active NBA players
        """
        try:
            all_players = players.get_active_players()
            # Return the full player dictionaries instead of just names
            return all_players
        except Exception as e:
            self.logger.error(f"Error getting active players: {str(e)}")
            return []
        
    def get_player_stats(self, player_id):
        """Get player stats for the last three seasons"""
        try:
            seasons = ['2024-25', '2023-24', '2022-23']
            all_stats = []
            
            for season in seasons:
                self.logger.info(f"Making API call for player {player_id} - Season {season}")
                
                # Get game logs for the season
                gamelog = PlayerGameLog(
                    player_id=player_id,
                    season=season
                )
                
                # Get raw response
                raw_data = gamelog.get_normalized_dict()
                self.logger.info(f"Raw response keys: {list(raw_data.keys())}")
                
                if 'PlayerGameLog' in raw_data and raw_data['PlayerGameLog']:
                    games = raw_data['PlayerGameLog']
                    self.logger.info(f"Found {len(games)} games in PlayerGameLog")
                    
                    if games:
                        # Calculate season averages
                        season_stats = {
                            'games_played': len(games),
                            'points': sum(game['PTS'] for game in games) / len(games),
                            'rebounds': sum(game['REB'] for game in games) / len(games),
                            'assists': sum(game['AST'] for game in games) / len(games),
                            'steals': sum(game['STL'] for game in games) / len(games),
                            'blocks': sum(game['BLK'] for game in games) / len(games),
                            'fg_pct': sum(game['FG_PCT'] for game in games) / len(games),
                            'ft_pct': sum(game['FT_PCT'] for game in games) / len(games),
                            'three_pct': sum(game['FG3_PCT'] for game in games) / len(games),
                            'minutes': sum(float(game['MIN']) for game in games) / len(games)
                        }
                        all_stats.append(season_stats)
                        self.logger.info(f"Successfully processed {len(games)} games for player {player_id} in {season}")
                    else:
                        self.logger.warning(f"No games found for player {player_id} in {season}")
                else:
                    self.logger.warning(f"No data found for player {player_id} in {season}")
                
                # Add delay between API calls
                time.sleep(5)
            
            if all_stats:
                # Calculate averages across all seasons
                avg_stats = {}
                for key in all_stats[0].keys():
                    avg_stats[key] = sum(season[key] for season in all_stats) / len(all_stats)
                return avg_stats
            else:
                self.logger.warning(f"No valid stats found for player {player_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting stats for player {player_id}: {str(e)}")
            return None
        
    def get_team_performance(self, team_id, season='2023-24'):
        """
        Fetch team's win-loss record for a given season
        """
        gamefinder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team_id,
            season_nullable=season
        ).get_data_frames()[0]
        
        wins = len(gamefinder[gamefinder['WL'] == 'W'])
        total_games = len(gamefinder)
        
        return wins, total_games

    def get_top_scorers(self, season='2024-25', limit=150):
        try:
            # Get league leaders for points
            leaders = LeagueLeaders(
                season=season,
                stat_category_abbreviation='PTS',
                per_mode48='PerGame',
                league_id='00'
            )
            
            # Get the data as a DataFrame
            df = leaders.league_leaders.get_data_frame()
            
            # Sort by points in descending order and get top players
            top_scorers = df.sort_values('PTS', ascending=False).head(limit)
            
            # Convert to list of player dictionaries
            players = []
            for _, row in top_scorers.iterrows():
                players.append({
                    'id': row['PLAYER_ID'],
                    'name': row['PLAYER'],
                    'team': row['TEAM'],
                    'points': row['PTS']
                })
            
            self.logger.info(f"Found {len(players)} top scorers for {season}")
            return players
            
        except Exception as e:
            self.logger.error(f"Error fetching top scorers: {str(e)}")
            return []

    def get_bottom_scorers(self, season='2024-25', limit=75):
        try:
            # Get league leaders for points
            leaders = LeagueLeaders(
                season=season,
                stat_category_abbreviation='PTS',
                per_mode48='PerGame',
                league_id='00'
            )
            
            # Get the data as a DataFrame
            df = leaders.league_leaders.get_data_frame()
            
            # Filter out players with very few games played (e.g., less than 20 games)
            df = df[df['GP'] >= 20]
            
            # Sort by points in ascending order and get bottom players
            bottom_scorers = df.sort_values('PTS', ascending=True).head(limit)
            
            # Convert to list of player dictionaries
            players = []
            for _, row in bottom_scorers.iterrows():
                players.append({
                    'id': int(row['PLAYER_ID']),  # Convert to int to ensure consistent type
                    'name': row['PLAYER'],
                    'team': row['TEAM'],
                    'points': row['PTS']
                })
            
            self.logger.info(f"Found {len(players)} bottom scorers for {season}")
            return players
            
        except Exception as e:
            self.logger.error(f"Error fetching bottom scorers: {str(e)}")
            return []

def main():
    # Test the data fetcher
    fetcher = NBADataFetcher()
    
    # Example: Get stats for a player
    test_player = "LeBron James"
    stats = fetcher.get_player_stats(test_player)
    if stats is not None:
        print(f"{test_player}'s average stats:")
        print(stats)

if __name__ == "__main__":
    main() 
    