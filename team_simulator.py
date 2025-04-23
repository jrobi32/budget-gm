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
    def __init__(self):
        self.team = []
        self.budget = 15  # Updated budget
        self.remaining_budget = self.budget
        self.total_cost = 0
        self.team_quality = 0
        self.win_probability = 0.5
        
    def add_player(self, player):
        """Add a player to the team"""
        if not self._can_afford_player(player):
            return False, "Not enough budget"
            
        if self._is_team_full():
            return False, "Team is full"
            
        self.team.append(player)
        self.total_cost += self._get_player_cost(player)
        self.remaining_budget = self.budget - self.total_cost
        self._update_team_quality()
        
        return True, "Player added successfully"
        
    def _can_afford_player(self, player):
        """Check if team can afford a player"""
        cost = self._get_player_cost(player)
        return self.remaining_budget >= cost
        
    def _is_team_full(self):
        """Check if team has maximum allowed players"""
        return len(self.team) >= 5
        
    def _get_player_cost(self, player):
        """Get player's cost"""
        return int(player['cost'].replace('$', ''))
        
    def _update_team_quality(self):
        """Update team's overall quality"""
        if not self.team:
            self.team_quality = 0
            self.win_probability = 0.5
            return
            
        # Calculate average stats
        total_stats = {
            'pts': 0,
            'ast': 0,
            'reb': 0,
            'stl': 0,
            'blk': 0,
            'fg_pct': 0,
            'ts_pct': 0
        }
        
        for player in self.team:
            stats = player['stats']
            for stat in total_stats:
                total_stats[stat] += stats[stat]
                
        avg_stats = {stat: value / len(self.team) for stat, value in total_stats.items()}
        
        # Calculate team quality score (0-100)
        weights = {
            'pts': 1.0,
            'ast': 0.8,
            'reb': 0.7,
            'stl': 0.6,
            'blk': 0.6,
            'fg_pct': 0.5,
            'ts_pct': 0.8
        }
        
        quality_score = 0
        for stat, weight in weights.items():
            if stat in ['fg_pct', 'ts_pct']:
                quality_score += avg_stats[stat] * weight
            else:
                # Normalize counting stats
                max_values = {'pts': 30, 'ast': 8, 'reb': 12, 'stl': 2, 'blk': 2}
                normalized = min(avg_stats[stat] / max_values[stat], 1.0) * 100
                quality_score += normalized * weight
                
        self.team_quality = quality_score
        
        # Update win probability based on team quality
        # Assuming average team quality is 50
        self.win_probability = 1 / (1 + np.exp(-0.1 * (self.team_quality - 50)))
        
    def simulate_game(self):
        """Simulate a single game"""
        if not self._is_team_complete():
            return False, "Team is incomplete"
            
        # Add some randomness to win probability
        game_prob = self.win_probability + random.uniform(-0.1, 0.1)
        game_prob = max(0.1, min(0.9, game_prob))  # Cap between 10% and 90%
        
        won = random.random() < game_prob
        return won, "Victory!" if won else "Defeat."
        
    def simulate_season(self, num_games=82):
        """Simulate a full season"""
        if not self._is_team_complete():
            return False, "Team is incomplete"
            
        wins = 0
        losses = 0
        
        for _ in range(num_games):
            won, _ = self.simulate_game()
            if won:
                wins += 1
            else:
                losses += 1
                
        win_pct = wins / num_games
        return True, {
            'wins': wins,
            'losses': losses,
            'win_pct': win_pct,
            'team_quality': self.team_quality,
            'total_cost': self.total_cost
        }
        
    def _is_team_complete(self):
        """Check if team has exactly 5 players"""
        return len(self.team) == 5
        
    def get_team_stats(self):
        """Get team's current statistics"""
        return {
            'num_players': len(self.team),
            'total_cost': self.total_cost,
            'remaining_budget': self.remaining_budget,
            'team_quality': round(self.team_quality, 1),
            'win_probability': round(self.win_probability * 100, 1),
            'is_complete': self._is_team_complete()
        }
        
    def get_player_stats(self, player):
        """Get formatted player statistics"""
        stats = player['stats']
        return (
            f"{player['name']}: "
            f"{stats['pts']} PPG, "
            f"{stats['ast']} APG, "
            f"{stats['reb']} RPG, "
            f"{stats['stl']} SPG, "
            f"{stats['blk']} BPG, "
            f"FG: {stats['fg_pct']}%, "
            f"TS: {stats['ts_pct']}%"
        )
        
    def display_team(self):
        """Display current team roster and stats"""
        print("\nCurrent Team:")
        print("-" * 50)
        for player in self.team:
            print(f"${player['cost']} - {self.get_player_stats(player)}")
        print("-" * 50)
        print(f"Players: {len(self.team)}/5")
        print(f"Total Cost: ${self.total_cost}")
        print(f"Remaining Budget: ${self.remaining_budget}")
        print(f"Team Quality: {round(self.team_quality, 1)}")
        print(f"Win Probability: {round(self.win_probability * 100, 1)}%")
        
    def display_season_results(self, results):
        """Display season simulation results"""
        print("\nSeason Simulation Results:")
        print("-" * 50)
        print(f"Wins: {results['wins']}")
        print(f"Losses: {results['losses']}")
        print(f"Win %: {results['win_pct'] * 100:.1f}%")
        print(f"Team Quality: {results['team_quality']:.1f}")
        print(f"Total Cost: ${results['total_cost']}")
        print("-" * 50)

def main():
    # Test the simulator
    simulator = TeamSimulator()
    
    # Example teams with $15 budget
    example_team1 = {
        "name": "Team 1",
        "players": [
            "Nikola Jokic",      # $5 (MVP)
            "Devin Booker",      # $4 (All-Star)
            "Anthony Edwards",   # $3 (Rising Star)
            "Kyle Kuzma",        # $2 (Solid starter)
            "Alex Caruso"        # $1 (Elite defender)
        ]
    }
    
    example_team2 = {
        "name": "Team 2",
        "players": [
            "Giannis Antetokounmpo",  # $5 (MVP)
            "Jayson Tatum",      # $4 (All-Star)
            "Josh Hart",         # $2 (Solid role player)
            "Georges Niang",     # $2 (Role player)
            "Alex Caruso"        # $1 (Elite defender)
        ]
    }
    
    example_team3 = {
        "name": "Team 3",
        "players": [
            "Luka Doncic",       # $5 (MVP)
            "Devin Booker",      # $4 (All-Star)
            "Anthony Edwards",   # $3 (Rising Star)
            "Kyle Kuzma",        # $2 (Solid starter)
            "Josh Hart"          # $1 (Solid role player)
        ]
    }
    
    # Test each team
    for team in [example_team1, example_team2, example_team3]:
        print(f"\n{'='*50}")
        print(f"Testing {team['name']}...")
        print("Building team...")
        simulator.build_team(team['players'])
        
        print("\nSimulating season...")
        results = simulator.simulate_season()
        
        simulator.display_season_results(results)
        print(f"{'='*50}")

if __name__ == "__main__":
    main() 