from nba_api.stats.endpoints import BoxScoreTraditionalV2, LeagueGameFinder, CommonPlayerInfo, PlayerCareerStats
from nba_api.stats.static import teams
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import time
from data_fetcher import NBADataFetcher
from nba_api.stats.static import players

class GamePredictor:
    def __init__(self):
        self.data_fetcher = NBADataFetcher()
        self.model = None
        self.scaler = StandardScaler()
        
    def get_player_info(self, player_id):
        """
        Get additional player information like experience, height, weight
        """
        try:
            time.sleep(1)  # Rate limiting
            player_info = CommonPlayerInfo(player_id=player_id).get_data_frames()[0]
            career_stats = PlayerCareerStats(player_id=player_id).get_data_frames()[0]
            
            # Get years of experience
            experience = int(player_info['SEASON_EXP'].iloc[0]) if not pd.isna(player_info['SEASON_EXP'].iloc[0]) else 0
            
            # Get height in inches
            height_str = player_info['HEIGHT'].iloc[0]
            if isinstance(height_str, str) and '-' in height_str:
                feet, inches = map(int, height_str.split('-'))
                height = feet * 12 + inches
            else:
                height = 0
                
            # Get weight
            weight = float(player_info['WEIGHT'].iloc[0]) if not pd.isna(player_info['WEIGHT'].iloc[0]) else 0
            
            # Get position
            position = player_info['POSITION'].iloc[0] if not pd.isna(player_info['POSITION'].iloc[0]) else ''
            
            # Get career averages
            if not career_stats.empty:
                career_stats = career_stats.iloc[-1]  # Most recent season
                career_ppg = float(career_stats['PTS']) if not pd.isna(career_stats['PTS']) else 0
                career_games = int(career_stats['GP']) if not pd.isna(career_stats['GP']) else 0
            else:
                career_ppg = 0
                career_games = 0
            
            return {
                'experience': experience,
                'height': height,
                'weight': weight,
                'position': position,
                'career_ppg': career_ppg,
                'career_games': career_games
            }
        except Exception as e:
            print(f"Error getting player info: {str(e)}")
            return None
    
    def calculate_advanced_stats(self, basic_stats):
        """
        Calculate advanced statistics from basic stats
        """
        stats = pd.Series(basic_stats)
        
        # True Shooting Percentage (TS%)
        if stats['FGA'] > 0:
            ts_pct = stats['PTS'] / (2 * (stats['FGA'] + 0.44 * stats['FTA']))
        else:
            ts_pct = 0
            
        # Usage Rate (rough approximation)
        usg_rate = (stats['FGA'] + 0.44 * stats['FTA'] + stats['TOV']) / 100
        
        # Assist to Turnover ratio
        ast_to = stats['AST'] / stats['TOV'] if stats['TOV'] > 0 else stats['AST']
        
        # Stocks (Steals + Blocks)
        stocks = stats['STL'] + stats['BLK']
        
        return {
            'ts_pct': ts_pct,
            'usg_rate': usg_rate,
            'ast_to': ast_to,
            'stocks': stocks
        }
        
    def get_game_data(self, season='2023-24', n_games=100):
        """
        Fetch game data and starting lineups for training
        """
        try:
            # Get list of regular season games
            gamefinder = LeagueGameFinder(
                season_nullable=season,
                league_id_nullable='00',  # NBA
                season_type_nullable='Regular Season'  # Only regular season games
            ).get_data_frames()[0]
            
            if gamefinder.empty:
                print("No games found for the specified season")
                return pd.DataFrame()
            
            # Sort by game date to get most recent games
            if 'GAME_DATE' in gamefinder.columns:
                gamefinder = gamefinder.sort_values('GAME_DATE', ascending=False)
            
            # Take the most recent n_games
            recent_games = gamefinder.head(n_games)
            print(f"Found {len(recent_games)} games to process")
            
            game_data = []
            for idx, game in recent_games.iterrows():
                game_id = game['GAME_ID']
                print(f"Processing game {game_id} ({idx + 1}/{len(recent_games)})")
                
                # Add delay to avoid API rate limiting
                time.sleep(2)  # Increased delay to avoid rate limiting
                
                try:
                    # Get box score for the game
                    box_score_response = BoxScoreTraditionalV2(game_id=game_id)
                    box_score_dict = box_score_response.get_dict()
                    
                    if 'resultSets' not in box_score_dict:
                        print(f"No box score data for game {game_id}")
                        continue
                        
                    # Get player stats from the first result set
                    player_stats_data = box_score_dict['resultSets'][0]
                    if not player_stats_data or 'rowSet' not in player_stats_data:
                        print(f"No player stats for game {game_id}")
                        continue
                        
                    # Convert to DataFrame
                    columns = player_stats_data['headers']
                    rows = player_stats_data['rowSet']
                    player_stats = pd.DataFrame(rows, columns=columns)
                    
                    # Filter starters
                    starters = player_stats[player_stats['START_POSITION'].notna() & (player_stats['START_POSITION'] != '')]
                    
                    # Get team IDs from the game data
                    teams_in_game = player_stats['TEAM_ID'].unique()
                    if len(teams_in_game) != 2:
                        print(f"Invalid number of teams for game {game_id}")
                        continue
                        
                    # Determine home and away teams
                    team1_players = player_stats[player_stats['TEAM_ID'] == teams_in_game[0]]
                    team2_players = player_stats[player_stats['TEAM_ID'] == teams_in_game[1]]
                    
                    # The team with more home games in their recent history is likely the home team
                    team1_games = gamefinder[gamefinder['TEAM_ID'] == teams_in_game[0]].head(5)
                    team2_games = gamefinder[gamefinder['TEAM_ID'] == teams_in_game[1]].head(5)
                    
                    team1_home_games = len(team1_games[team1_games['MATCHUP'].str.contains(' vs. ')])
                    team2_home_games = len(team2_games[team2_games['MATCHUP'].str.contains(' vs. ')])
                    
                    if team1_home_games > team2_home_games:
                        home_team_id = teams_in_game[0]
                        away_team_id = teams_in_game[1]
                    else:
                        home_team_id = teams_in_game[1]
                        away_team_id = teams_in_game[0]
                    
                    home_starters = starters[starters['TEAM_ID'] == home_team_id]
                    away_starters = starters[starters['TEAM_ID'] == away_team_id]
                    
                    if len(home_starters) == 5 and len(away_starters) == 5:
                        # Get season averages and additional info for each starter
                        home_stats = []
                        away_stats = []
                        home_additional = []
                        away_additional = []
                        
                        # Process home team starters
                        for _, player in home_starters.iterrows():
                            time.sleep(1)  # Rate limiting
                            stats = self.data_fetcher.get_player_stats(player['PLAYER_NAME'], season)
                            if stats is not None:
                                home_stats.append(stats)
                                player_info = self.get_player_info(player['PLAYER_ID'])
                                if player_info:
                                    home_additional.append(player_info)
                                    
                        # Process away team starters
                        for _, player in away_starters.iterrows():
                            time.sleep(1)  # Rate limiting
                            stats = self.data_fetcher.get_player_stats(player['PLAYER_NAME'], season)
                            if stats is not None:
                                away_stats.append(stats)
                                player_info = self.get_player_info(player['PLAYER_ID'])
                                if player_info:
                                    away_additional.append(player_info)
                                    
                        if (len(home_stats) == 5 and len(away_stats) == 5 and 
                            len(home_additional) == 5 and len(away_additional) == 5):
                            # Calculate team metrics
                            home_df = pd.DataFrame(home_stats)
                            away_df = pd.DataFrame(away_stats)
                            home_add_df = pd.DataFrame(home_additional)
                            away_add_df = pd.DataFrame(away_additional)
                            
                            # Calculate advanced stats for each team
                            home_advanced = [self.calculate_advanced_stats(stats) for stats in home_stats]
                            away_advanced = [self.calculate_advanced_stats(stats) for stats in away_stats]
                            home_adv_df = pd.DataFrame(home_advanced)
                            away_adv_df = pd.DataFrame(away_advanced)
                            
                            # Calculate winner based on points
                            home_pts = float(player_stats[player_stats['TEAM_ID'] == home_team_id]['PTS'].sum())
                            away_pts = float(player_stats[player_stats['TEAM_ID'] == away_team_id]['PTS'].sum())
                            home_win = 1 if home_pts > away_pts else 0
                            
                            game_stats = {
                                # Basic stats - Home team
                                'home_pts': home_df['PTS'].sum(),
                                'home_ast': home_df['AST'].sum(),
                                'home_reb': home_df['REB'].sum(),
                                'home_stl': home_df['STL'].sum(),
                                'home_blk': home_df['BLK'].sum(),
                                'home_fg_pct': home_df['FG_PCT'].mean(),
                                'home_fg3_pct': home_df['FG3_PCT'].mean(),
                                'home_ft_pct': home_df['FT_PCT'].mean(),
                                'home_tov': home_df['TOV'].sum(),
                                
                                # Advanced stats - Home team
                                'home_ts_pct': home_adv_df['ts_pct'].mean(),
                                'home_usg_rate': home_adv_df['usg_rate'].sum(),
                                'home_ast_to': home_adv_df['ast_to'].mean(),
                                'home_stocks': home_adv_df['stocks'].sum(),
                                
                                # Player info - Home team
                                'home_avg_exp': home_add_df['experience'].mean(),
                                'home_avg_height': home_add_df['height'].mean(),
                                'home_avg_weight': home_add_df['weight'].mean(),
                                'home_career_ppg': home_add_df['career_ppg'].mean(),
                                'home_career_games': home_add_df['career_games'].mean(),
                                
                                # Basic stats - Away team
                                'away_pts': away_df['PTS'].sum(),
                                'away_ast': away_df['AST'].sum(),
                                'away_reb': away_df['REB'].sum(),
                                'away_stl': away_df['STL'].sum(),
                                'away_blk': away_df['BLK'].sum(),
                                'away_fg_pct': away_df['FG_PCT'].mean(),
                                'away_fg3_pct': away_df['FG3_PCT'].mean(),
                                'away_ft_pct': away_df['FT_PCT'].mean(),
                                'away_tov': away_df['TOV'].sum(),
                                
                                # Advanced stats - Away team
                                'away_ts_pct': away_adv_df['ts_pct'].mean(),
                                'away_usg_rate': away_adv_df['usg_rate'].sum(),
                                'away_ast_to': away_adv_df['ast_to'].mean(),
                                'away_stocks': away_adv_df['stocks'].sum(),
                                
                                # Player info - Away team
                                'away_avg_exp': away_add_df['experience'].mean(),
                                'away_avg_height': away_add_df['height'].mean(),
                                'away_avg_weight': away_add_df['weight'].mean(),
                                'away_career_ppg': away_add_df['career_ppg'].mean(),
                                'away_career_games': away_add_df['career_games'].mean(),
                                
                                # Target variable
                                'home_win': home_win
                            }
                            
                            # Add position balance metrics
                            for team_df, prefix in [(home_add_df, 'home'), (away_add_df, 'away')]:
                                positions = team_df['position'].value_counts()
                                game_stats[f'{prefix}_guards'] = positions.get('G', 0) + positions.get('PG', 0) + positions.get('SG', 0)
                                game_stats[f'{prefix}_forwards'] = positions.get('F', 0) + positions.get('SF', 0) + positions.get('PF', 0)
                                game_stats[f'{prefix}_centers'] = positions.get('C', 0)
                            
                            game_data.append(game_stats)
                            print(f"Successfully processed game {game_id}")
                        else:
                            print(f"Not enough valid player data for game {game_id}")
                    else:
                        print(f"Not enough starters found for game {game_id}")
                
                except Exception as e:
                    print(f"Error processing game {game_id}: {str(e)}")
                    continue
                    
            return pd.DataFrame(game_data)
            
        except Exception as e:
            print(f"Error fetching game data: {str(e)}")
            return pd.DataFrame()
        
    def train_model(self, season='2023-24', n_games=100):
        """
        Train the prediction model using historical game data
        """
        print("Training model...")
        print(f"Fetching data for {n_games} games from {season} season...")
        
        # Get training data
        data = self.get_game_data(season, n_games)
        
        if data.empty:
            raise ValueError("No training data available. Please check the API connection and try again.")
            
        print(f"Successfully collected data for {len(data)} games")
        
        # Separate features and target
        features = data.drop('home_win', axis=1)
        target = data['home_win']
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            features_scaled, target, test_size=0.2, random_state=42
        )
        
        # Train model
        print("Training Random Forest model...")
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        print(f"Model training complete:")
        print(f"Training accuracy: {train_score:.3f}")
        print(f"Testing accuracy: {test_score:.3f}")
        
        return train_score, test_score
        
    def predict_game(self, home_lineup, away_lineup):
        """
        Predict the outcome of a game given two lineups
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train_model() first.")
            
        # Get stats for both lineups
        home_stats = []
        away_stats = []
        home_additional = []
        away_additional = []
        
        # Process home team
        for player in home_lineup:
            # Get basic stats
            stats = self.data_fetcher.get_player_stats(player)
            if stats is not None:
                home_stats.append(stats)
                # Get player ID for additional info
                player_dict = players.find_players_by_full_name(player)
                if player_dict:
                    player_info = self.get_player_info(player_dict[0]['id'])
                    if player_info:
                        home_additional.append(player_info)
                
        # Process away team
        for player in away_lineup:
            # Get basic stats
            stats = self.data_fetcher.get_player_stats(player)
            if stats is not None:
                away_stats.append(stats)
                # Get player ID for additional info
                player_dict = players.find_players_by_full_name(player)
                if player_dict:
                    player_info = self.get_player_info(player_dict[0]['id'])
                    if player_info:
                        away_additional.append(player_info)
                
        if (len(home_stats) != 5 or len(away_stats) != 5 or 
            len(home_additional) != 5 or len(away_additional) != 5):
            raise ValueError("Could not get complete stats for all players")
            
        # Calculate team metrics
        home_df = pd.DataFrame(home_stats)
        away_df = pd.DataFrame(away_stats)
        home_add_df = pd.DataFrame(home_additional)
        away_add_df = pd.DataFrame(away_additional)
        
        # Calculate advanced stats
        home_advanced = [self.calculate_advanced_stats(stats) for stats in home_stats]
        away_advanced = [self.calculate_advanced_stats(stats) for stats in away_stats]
        home_adv_df = pd.DataFrame(home_advanced)
        away_adv_df = pd.DataFrame(away_advanced)
        
        # Create feature dictionary
        game_features = pd.DataFrame([{
            # Basic stats - Home team
            'home_pts': home_df['PTS'].sum(),
            'home_ast': home_df['AST'].sum(),
            'home_reb': home_df['REB'].sum(),
            'home_stl': home_df['STL'].sum(),
            'home_blk': home_df['BLK'].sum(),
            'home_fg_pct': home_df['FG_PCT'].mean(),
            'home_fg3_pct': home_df['FG3_PCT'].mean(),
            'home_ft_pct': home_df['FT_PCT'].mean(),
            'home_tov': home_df['TOV'].sum(),
            
            # Advanced stats - Home team
            'home_ts_pct': home_adv_df['ts_pct'].mean(),
            'home_usg_rate': home_adv_df['usg_rate'].sum(),
            'home_ast_to': home_adv_df['ast_to'].mean(),
            'home_stocks': home_adv_df['stocks'].sum(),
            
            # Player info - Home team
            'home_avg_exp': home_add_df['experience'].mean(),
            'home_avg_height': home_add_df['height'].mean(),
            'home_avg_weight': home_add_df['weight'].mean(),
            'home_career_ppg': home_add_df['career_ppg'].mean(),
            'home_career_games': home_add_df['career_games'].mean(),
            
            # Basic stats - Away team
            'away_pts': away_df['PTS'].sum(),
            'away_ast': away_df['AST'].sum(),
            'away_reb': away_df['REB'].sum(),
            'away_stl': away_df['STL'].sum(),
            'away_blk': away_df['BLK'].sum(),
            'away_fg_pct': away_df['FG_PCT'].mean(),
            'away_fg3_pct': away_df['FG3_PCT'].mean(),
            'away_ft_pct': away_df['FT_PCT'].mean(),
            'away_tov': away_df['TOV'].sum(),
            
            # Advanced stats - Away team
            'away_ts_pct': away_adv_df['ts_pct'].mean(),
            'away_usg_rate': away_adv_df['usg_rate'].sum(),
            'away_ast_to': away_adv_df['ast_to'].mean(),
            'away_stocks': away_adv_df['stocks'].sum(),
            
            # Player info - Away team
            'away_avg_exp': away_add_df['experience'].mean(),
            'away_avg_height': away_add_df['height'].mean(),
            'away_avg_weight': away_add_df['weight'].mean(),
            'away_career_ppg': away_add_df['career_ppg'].mean(),
            'away_career_games': away_add_df['career_games'].mean(),
        }])
        
        # Add position balance metrics
        for team_df, prefix in [(home_add_df, 'home'), (away_add_df, 'away')]:
            positions = team_df['position'].value_counts()
            game_features[f'{prefix}_guards'] = positions.get('G', 0) + positions.get('PG', 0) + positions.get('SG', 0)
            game_features[f'{prefix}_forwards'] = positions.get('F', 0) + positions.get('SF', 0) + positions.get('PF', 0)
            game_features[f'{prefix}_centers'] = positions.get('C', 0)
        
        # Scale features
        features_scaled = self.scaler.transform(game_features)
        
        # Make prediction
        win_prob = self.model.predict_proba(features_scaled)[0]
        
        # Get feature importance
        feature_importance = pd.DataFrame({
            'feature': game_features.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return {
            'home_win_probability': win_prob[1],
            'away_win_probability': win_prob[0],
            'key_factors': feature_importance.head(5).to_dict('records')  # Top 5 most important features
        }

def main():
    # Test the predictor
    predictor = GamePredictor()
    
    # Train the model
    print("Training model...")
    predictor.train_model(n_games=50)  # Using fewer games for testing
    
    # Test prediction
    home_lineup = [
        "LeBron James",
        "Anthony Davis",
        "D'Angelo Russell",
        "Austin Reaves",
        "Rui Hachimura"
    ]
    
    away_lineup = [
        "Stephen Curry",
        "Klay Thompson",
        "Andrew Wiggins",
        "Draymond Green",
        "Kevon Looney"
    ]
    
    print("\nPredicting game outcome...")
    result = predictor.predict_game(home_lineup, away_lineup)
    print(f"\nPrediction Results:")
    print(f"Home team win probability: {result['home_win_probability']:.3f}")
    print(f"Away team win probability: {result['away_win_probability']:.3f}")
    print("\nKey Factors:")
    for factor in result['key_factors']:
        print(f"- {factor['feature']}: {factor['importance']:.3f}")

if __name__ == "__main__":
    main() 