import json
import pandas as pd
import numpy as np
import random
import math
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Player:
    def __init__(self, name, points, rebounds, assists, steals, blocks, fg_pct, ft_pct, three_pt_pct):
        self.name = name
        self.stats = {
            'points': points,
            'rebounds': rebounds,
            'assists': assists,
            'steals': steals,
            'blocks': blocks,
            'fg_pct': fg_pct,
            'ft_pct': ft_pct,
            'three_pt_pct': three_pt_pct
        }
        self.game_stats = {
            'points': 0,
            'rebounds': 0,
            'assists': 0,
            'steals': 0,
            'blocks': 0,
            'fg_made': 0,
            'fg_attempts': 0,
            'ft_made': 0,
            'ft_attempts': 0,
            'three_made': 0,
            'three_attempts': 0
        }
        self.season_stats = {
            'points': 0,
            'rebounds': 0,
            'assists': 0,
            'steals': 0,
            'blocks': 0,
            'games_played': 0
        }

    def reset_game_stats(self):
        for stat in self.game_stats:
            self.game_stats[stat] = 0

    def update_season_stats(self):
        self.season_stats['points'] += self.game_stats['points']
        self.season_stats['rebounds'] += self.game_stats['rebounds']
        self.season_stats['assists'] += self.game_stats['assists']
        self.season_stats['steals'] += self.game_stats['steals']
        self.season_stats['blocks'] += self.game_stats['blocks']
        self.season_stats['games_played'] += 1

class TeamSimulator:
    def __init__(self, budget=10):
        self.budget = budget
        self.player_pool = self._load_player_pool()
        self.team = []
        self.team_stats = None
        self.league_averages = {
            'points': 110.0,
            'rebounds': 44.0,
            'assists': 24.0,
            'steals': 7.5,
            'blocks': 5.0,
            'fg_pct': 0.46,
            'ft_pct': 0.78,
            'three_pct': 0.36
        }

    def _load_player_pool(self):
        try:
            with open('player_pool.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading player pool: {str(e)}")
            return {}

    def _calculate_team_quality(self, team_stats):
        """Calculate team quality based on key stats"""
        try:
            # Weighted average of key stats
            weights = {
                'PTS': 0.3,
                'REB': 0.2,
                'AST': 0.2,
                'STL': 0.1,
                'BLK': 0.1,
                'FG%': 0.05,
                '3P%': 0.05
            }
            
            quality = 0
            for stat, weight in weights.items():
                if stat in team_stats:
                    # Normalize stats to 0-1 range
                    if stat in ['FG%', '3P%']:
                        normalized = team_stats[stat] / 100
                    else:
                        # Use league averages as reference points
                        normalized = team_stats[stat] / self.league_averages[stat]
                    quality += normalized * weight
            
            return quality
        except Exception as e:
            logger.error(f"Error calculating team quality: {str(e)}")
            return 0.5

    def _adjust_win_probability(self, base_prob, team_quality):
        """Adjust win probability based on team quality"""
        try:
            # Boost win probability for good teams
            if team_quality > 1.0:  # Above average team
                boost = min(0.2, (team_quality - 1.0) * 0.4)  # Max 20% boost
                adjusted_prob = min(0.9, base_prob + boost)  # Cap at 90%
            else:
                adjusted_prob = max(0.1, base_prob)  # Floor at 10%
            
            return adjusted_prob
        except Exception as e:
            logger.error(f"Error adjusting win probability: {str(e)}")
            return base_prob

    def simulate_team(self, players):
        """Simulate a team's season"""
        try:
            logger.info(f"Simulating team with players: {players}")
            
            # Get team stats
            team_stats = self.calculate_team_stats(players)
            if not team_stats:
                logger.error("Failed to calculate team stats")
                return None
            
            # Calculate team quality
            team_quality = self._calculate_team_quality(team_stats)
            logger.info(f"Team quality: {team_quality}")
            
            # Calculate base win probability
            base_win_prob = self._calculate_win_probability(team_stats)
            
            # Adjust win probability based on team quality
            win_prob = self._adjust_win_probability(base_win_prob, team_quality)
            logger.info(f"Adjusted win probability: {win_prob}")
            
            # Simulate season
            wins = 0
            losses = 0
            for _ in range(82):
                if random.random() < win_prob:
                    wins += 1
                else:
                    losses += 1
            
            return {
                'wins': wins,
                'losses': losses,
                'win_probability': win_prob,
                'team_stats': team_stats
            }
            
        except Exception as e:
            logger.error(f"Error in simulate_team: {str(e)}")
            return None

    def build_team(self, player_names):
        """Build a team from a list of player names"""
        try:
            logger.info(f"Building team with players: {player_names}")
            team = []
            
            for name in player_names:
                player_found = False
                for category in self.player_pool.values():
                    for player in category:
                        if player['name'] == name:
                            team.append(player)
                            player_found = True
                            logger.info(f"Found player {name} in player pool")
                            break
                    if player_found:
                        break
                
                if not player_found:
                    logger.error(f"Player {name} not found in player pool")
                    return None

            if len(team) != 5:
                logger.error(f"Team has {len(team)} players instead of 5")
                return None

            logger.info("Team built successfully")
            return team

        except Exception as e:
            logger.error(f"Error in build_team: {str(e)}")
            return None

    def get_random_players(self, count=5):
        """Get random players from each category"""
        try:
            logger.info(f"Getting {count} random players from each category")
            random_players = {}
            
            for category, players in self.player_pool.items():
                if len(players) >= count:
                    selected = random.sample(players, count)
                    random_players[category] = selected
                    logger.info(f"Selected {count} random players from {category}")
                else:
                    logger.warning(f"Not enough players in {category} to select {count}")
                    random_players[category] = players

            return random_players

        except Exception as e:
            logger.error(f"Error in get_random_players: {str(e)}")
            return None

    def _calculate_team_stats(self, team):
        """Calculate team statistics from player stats"""
        try:
            logger.info("Calculating team stats")
            team_stats = {
                'points': 0,
                'rebounds': 0,
                'assists': 0,
                'steals': 0,
                'blocks': 0,
                'fg_pct': 0,
                'ft_pct': 0,
                'three_pct': 0,
                'minutes': 0
            }

            for player in team:
                stats = player['stats']
                for stat in team_stats:
                    if stat in stats:
                        # Convert numpy.float64 to float
                        team_stats[stat] += float(stats[stat])

            # Average the percentages
            for stat in ['fg_pct', 'ft_pct', 'three_pct']:
                team_stats[stat] /= 5

            logger.info(f"Team stats calculated: {team_stats}")
            return team_stats

        except Exception as e:
            logger.error(f"Error in _calculate_team_stats: {str(e)}")
            return None

    def calculate_win_probability(self, team_stats):
        """Calculate win probability based on team stats"""
        try:
            logger.info("Calculating win probability")
            league_averages = self.league_averages
            
            # Calculate team rating
            team_rating = (
                (team_stats['points'] / league_averages['points']) * 0.3 +
                (team_stats['rebounds'] / league_averages['rebounds']) * 0.15 +
                (team_stats['assists'] / league_averages['assists']) * 0.15 +
                (team_stats['steals'] / league_averages['steals']) * 0.1 +
                (team_stats['blocks'] / league_averages['blocks']) * 0.1 +
                (team_stats['fg_pct'] / league_averages['fg_pct']) * 0.1 +
                (team_stats['ft_pct'] / league_averages['ft_pct']) * 0.05 +
                (team_stats['three_pct'] / league_averages['three_pct']) * 0.05
            )

            # Convert numpy.float64 to float
            team_rating = float(team_rating)

            # Calculate win probability using logistic function
            win_probability = 1 / (1 + math.exp(-(team_rating - 1) * 5))
            
            logger.info(f"Win probability calculated: {win_probability}")
            return win_probability

        except Exception as e:
            logger.error(f"Error in calculate_win_probability: {str(e)}")
            return None

    def simulate_season(self, num_games=82):
        game_results = []
        for _ in range(num_games):
            game_result = self.simulate_game()
            game_results.append(game_result)
        
        return {
            'game_results': game_results,
            'player_stats': self.team
        }

    def simulate_game(self):
        # Reset player game stats
        for player in self.team:
            player['reset_game_stats']()

        # Simulate player performances
        for player in self.team:
            # Field goals
            fg_attempts = random.randint(8, 20)
            fg_made = sum(1 for _ in range(fg_attempts) 
                         if random.random() < player['fg_pct'])
            player['fg_attempts'] = fg_attempts
            player['fg_made'] = fg_made

            # Three pointers
            three_attempts = random.randint(3, 10)
            three_made = sum(1 for _ in range(three_attempts)
                           if random.random() < player['three_pt_pct'])
            player['three_attempts'] = three_attempts
            player['three_made'] = three_made

            # Free throws
            ft_attempts = random.randint(2, 8)
            ft_made = sum(1 for _ in range(ft_attempts)
                         if random.random() < player['ft_pct'])
            player['ft_attempts'] = ft_attempts
            player['ft_made'] = ft_made

            # Calculate points
            player['points'] = (
                (fg_made - three_made) * 2 +  # 2-pointers
                three_made * 3 +  # 3-pointers
                ft_made  # Free throws
            )

            # Other stats
            player['rebounds'] = random.randint(
                max(0, int(player['rebounds'] - 2)),
                int(player['rebounds'] + 2)
            )
            player['assists'] = random.randint(
                max(0, int(player['assists'] - 2)),
                int(player['assists'] + 2)
            )
            player['steals'] = random.randint(
                max(0, int(player['steals'] - 1)),
                int(player['steals'] + 1)
            )
            player['blocks'] = random.randint(
                max(0, int(player['blocks'] - 1)),
                int(player['blocks'] + 1)
            )

            # Update season stats
            player['update_season_stats']()

        # Calculate team total points
        team_points = sum(p['points'] for p in self.team)
        
        # Simulate opponent points (based on team's defensive rating)
        defensive_rating = 110 - (self.team_stats['steals'] + self.team_stats['blocks'])
        opponent_points = random.gauss(defensive_rating, 5)
        
        # Determine game result
        result = 'W' if team_points > opponent_points else 'L'
        
        return {
            'result': result,
            'team_points': team_points,
            'opponent_points': opponent_points,
            'player_stats': self.team
        }

def main():
    # Test the simulator
    simulator = TeamSimulator(budget=11)
    
    # Example teams with $11 budget
    teams = [
        {
            "name": "Superstar + Balanced Support",
            "players": [
                "Nikola Jokic",      # $3 (MVP candidate)
                "Devin Booker",      # $2 (All-Star)
                "Anthony Edwards",   # $2 (All-Star)
                "Kyle Kuzma",        # $1 (Solid starter)
                "Alex Caruso"        # $1 (Elite defender)
            ]  # Total: $9
        },
        {
            "name": "Two Stars + Quality Role Players",
            "players": [
                "Nikola Jokic",      # $3 (MVP candidate)
                "Jayson Tatum",      # $2 (All-Star)
                "Josh Hart",         # $1 (Solid role player)
                "Georges Niang",     # $1 (Role player)
                "Alex Caruso"        # $1 (Elite defender)
            ]  # Total: $8
        },
        {
            "name": "Balanced All-Stars",
            "players": [
                "Devin Booker",      # $2 (All-Star)
                "Anthony Edwards",   # $2 (All-Star)
                "Jayson Tatum",      # $2 (All-Star)
                "Kyle Kuzma",        # $1 (Solid starter)
                "Josh Hart"          # $1 (Solid role player)
            ]  # Total: $8
        }
    ]
    
    # Test each team
    for team in teams:
        print(f"\n{'='*50}")
        print(f"Testing {team['name']}...")
        print("Building team...")
        simulator.build_team(team['players'])
        
        print("\nSimulating season...")
        results = simulator.simulate_season()
        
        print("\nSeason Simulation Results:")
        print(f"Team Composition (Total: ${sum(player['cost'] for player in team['players'])}):")
        for player in team['players']:
            print(f"- {player['name']}: ${player['cost']}")
        print(f"\nWins: {results['wins']}")
        print(f"Losses: {results['losses']}")
        print(f"Win Percentage: {results['win_pct']:.3f}")
        print(f"Power Rating: {results['power_rating']:.1f}")
        print(f"{'Made playoffs' if results['makes_playoffs'] else 'Did not make playoffs'}")
        print(f"{'='*50}")

if __name__ == "__main__":
    main() 