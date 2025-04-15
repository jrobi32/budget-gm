import random
import time
from team_simulator import TeamSimulator

class SeasonSimulator:
    def __init__(self, team):
        self.team = team
        self.simulator = TeamSimulator()
        self.simulator.build_team([player['name'] for player in team])
        self.wins = 0
        self.losses = 0
        self.player_stats = {}
        self.initialize_player_stats()

    def initialize_player_stats(self):
        """Initialize season stats for each player"""
        for player in self.team:
            self.player_stats[player['name']] = {
                'points': 0,
                'rebounds': 0,
                'assists': 0,
                'steals': 0,
                'blocks': 0,
                'games_played': 0
            }

    def simulate_game(self):
        """Simulate a single game and update stats"""
        # Base win probability
        win_prob = self.simulator.calculate_win_probability()
        
        # Add some randomness to make games more interesting
        win_prob += random.uniform(-0.1, 0.1)
        win_prob = max(0.1, min(0.9, win_prob))  # Keep between 10% and 90%
        
        # Simulate game result
        game_won = random.random() < win_prob
        if game_won:
            self.wins += 1
        else:
            self.losses += 1

        # Update player stats
        for player in self.team:
            base_stats = player['stats']
            name = player['name']
            
            # Generate varied stats based on base stats
            points = random.normalvariate(base_stats['points'], 5)
            rebounds = random.normalvariate(base_stats['rebounds'], 2)
            assists = random.normalvariate(base_stats['assists'], 2)
            steals = random.normalvariate(base_stats['steals'], 0.5)
            blocks = random.normalvariate(base_stats['blocks'], 0.5)
            
            # Ensure stats are non-negative
            points = max(0, points)
            rebounds = max(0, rebounds)
            assists = max(0, assists)
            steals = max(0, steals)
            blocks = max(0, blocks)
            
            # Update season totals
            self.player_stats[name]['points'] += points
            self.player_stats[name]['rebounds'] += rebounds
            self.player_stats[name]['assists'] += assists
            self.player_stats[name]['steals'] += steals
            self.player_stats[name]['blocks'] += blocks
            self.player_stats[name]['games_played'] += 1

    def simulate_season(self):
        """Simulate the full 82-game season"""
        print("\nSimulating season...")
        for game in range(1, 83):
            self.simulate_game()
            print(f"\rGame {game}/82: {self.wins}-{self.losses}", end="")
            time.sleep(0.05)  # Small delay for visual effect
        print("\n")

    def get_season_stats(self):
        """Return formatted season stats for each player"""
        stats = []
        for name, totals in self.player_stats.items():
            games = totals['games_played']
            if games > 0:
                stats.append({
                    'name': name,
                    'points': totals['points'] / games,
                    'rebounds': totals['rebounds'] / games,
                    'assists': totals['assists'] / games,
                    'steals': totals['steals'] / games,
                    'blocks': totals['blocks'] / games,
                    'games_played': games
                })
        return stats

def display_season_stats(stats):
    """Display the season stats for each player"""
    print("\nSeason Stats:")
    print("=============")
    for player in stats:
        print(f"\n{player['name']}")
        print(f"   Points: {player['points']:.1f} | Rebounds: {player['rebounds']:.1f} | Assists: {player['assists']:.1f}")
        print(f"   Steals: {player['steals']:.1f} | Blocks: {player['blocks']:.1f}")