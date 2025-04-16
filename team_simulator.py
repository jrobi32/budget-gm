import json
import pandas as pd
import numpy as np
import random
import math

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
        self.team = []
        self.team_stats = None
        
        # Load player pool
        try:
            with open('player_pool.json', 'r') as f:
                self.player_pool = json.load(f)
        except FileNotFoundError:
            print("Error: player_pool.json not found")
            self.player_pool = {"$3": [], "$2": [], "$1": [], "$0": []}
        
    def simulate_team(self, players):
        """
        Simulate a team's season and return the win probability
        """
        try:
            print(f"Starting team simulation for players: {players}")
            
            # Build the team first
            self.build_team(players)
            
            if not self.team:
                print("Error: No players were added to the team")
                return 0.0
                
            if len(self.team) < 5:
                print(f"Error: Team has fewer than 5 players. Current team size: {len(self.team)}")
                return 0.0
            
            # Calculate win probability
            win_probability = self.calculate_win_probability()
            print(f"Calculated win probability: {win_probability}")
            
            return win_probability
            
        except Exception as e:
            print(f"Error in simulate_team: {str(e)}")
            raise
        
    def build_team(self, players):
        """
        Build a team from a list of player names
        """
        total_cost = 0
        self.team = []
        
        print(f"Building team with players: {players}")
        print(f"Player pool structure: {self.player_pool}")
        
        for player_name in players:
            # Find player's cost
            player_found = False
            for cost, player_list in self.player_pool.items():
                print(f"Checking {cost} players...")
                for player in player_list:
                    # Case-insensitive matching and handle partial matches
                    if player['name'].lower() in player_name.lower() or player_name.lower() in player['name'].lower():
                        print(f"Found match: {player['name']} for {player_name}")
                        player_cost = int(cost[1])  # Convert "$3" to 3, etc.
                        if total_cost + player_cost <= self.budget:
                            self.team.append(player)
                            total_cost += player_cost
                            player_found = True
                            print(f"Added {player['name']} to team. Total cost: ${total_cost}")
                            break
                if player_found:
                    break
            
            if not player_found:
                print(f"Warning: Player {player_name} not found in player pool or exceeds budget. Skipping.")
                
        if len(self.team) < 5:
            print(f"Warning: Team has fewer than 5 players. Current team size: {len(self.team)}")
            
        # Calculate team stats
        self._calculate_team_stats()
        
    def _calculate_team_stats(self):
        """
        Calculate team statistics by averaging player stats
        """
        if not self.team:
            return
            
        # Initialize stats dictionary
        team_stats = {
            'points': 0,
            'rebounds': 0,
            'assists': 0,
            'steals': 0,
            'blocks': 0,
            'fg_pct': 0,
            'ft_pct': 0,
            'three_pct': 0,
            'minutes': 0,
            'games_played': 0
        }
        
        # Sum up stats for all players
        for player in self.team:
            stats = player['stats']
            for stat in team_stats:
                team_stats[stat] += stats[stat]
        
        # Calculate averages
        for stat in team_stats:
            team_stats[stat] /= len(self.team)
            
        self.team_stats = team_stats
        
    def calculate_win_probability(self):
        """
        Calculate the team's win probability based on their stats
        """
        if not self.team_stats:
            return 0.0
            
        # Get league averages
        league_avgs = self._get_league_averages()
        
        # Calculate team rating with adjusted weights
        team_rating = (
            self.team_stats['points'] * 0.35 +  # Increased weight for scoring
            self.team_stats['rebounds'] * 0.15 +
            self.team_stats['assists'] * 0.15 +
            self.team_stats['steals'] * 0.1 +
            self.team_stats['blocks'] * 0.1 +
            self.team_stats['fg_pct'] * 0.1 +
            self.team_stats['ft_pct'] * 0.05 +
            self.team_stats['three_pct'] * 0.05
        )
        
        # Calculate league average rating
        league_rating = (
            league_avgs['points'] * 0.35 +  # Match the team rating weights
            league_avgs['rebounds'] * 0.15 +
            league_avgs['assists'] * 0.15 +
            league_avgs['steals'] * 0.1 +
            league_avgs['blocks'] * 0.1 +
            league_avgs['fg_pct'] * 0.1 +
            league_avgs['ft_pct'] * 0.05 +
            league_avgs['three_pct'] * 0.05
        )
        
        # Calculate win probability using modified logistic function
        rating_diff = team_rating - league_rating
        
        # Add a slight boost to make 50-win teams more common
        base_win_prob = 1 / (1 + np.exp(-rating_diff * 0.15))  # Increased sensitivity
        
        # Add a small boost for teams with good stats
        if base_win_prob > 0.4:  # Only boost teams that are already decent
            boost = (base_win_prob - 0.4) * 0.2  # 20% boost for teams above 0.4
            win_prob = min(0.85, base_win_prob + boost)  # Cap at 85% to maintain some randomness
        else:
            win_prob = base_win_prob
            
        return win_prob
        
    def _get_league_averages(self):
        """
        Get league average statistics
        """
        # These are approximate NBA league averages
        return {
            'points': 15.0,
            'rebounds': 5.0,
            'assists': 3.5,
            'steals': 1.0,
            'blocks': 0.5,
            'fg_pct': 0.45,
            'ft_pct': 0.75,
            'three_pct': 0.35,
            'minutes': 25.0,
            'games_played': 60.0
        }
        
    def simulate_season(self):
        """
        Simulate a season with the current team
        """
        if not self.team_stats:
            return None
            
        # Get win probability
        win_prob = self.calculate_win_probability()
        
        # Simulate 82 games
        wins = 0
        for _ in range(82):
            if np.random.random() < win_prob:
                wins += 1
                
        losses = 82 - wins
        win_pct = wins / 82
        
        # Calculate power rating
        power_rating = win_prob * 100
        
        # Determine if team makes playoffs
        makes_playoffs = win_pct >= 0.5
        
        return {
            'wins': wins,
            'losses': losses,
            'win_pct': win_pct,
            'power_rating': power_rating,
            'makes_playoffs': makes_playoffs
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

    def simulate_season(self, num_games=82):
        game_results = []
        for _ in range(num_games):
            game_result = self.simulate_game()
            game_results.append(game_result)
        
        return {
            'game_results': game_results,
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