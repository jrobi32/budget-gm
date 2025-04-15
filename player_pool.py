from data_fetcher import NBADataFetcher
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import json
import random

class PlayerPool:
    def __init__(self):
        self.data_fetcher = NBADataFetcher()
        self.players = {}  # Dictionary to store player costs
        self.player_stats = {}  # Dictionary to store player stats
        self._load_player_pool()
        
    def _load_player_pool(self):
        """
        Load the pre-built player pool from JSON file
        """
        try:
            with open('player_pool.json', 'r') as f:
                categorized_players = json.load(f)
                
            # Convert JSON data to internal format
            for cost, player_list in categorized_players.items():
                for player_data in player_list:
                    player_name = player_data['name']
                    self.players[player_name] = {'cost': int(cost)}
                    self.player_stats[player_name] = pd.Series(player_data['stats'])
                    
            print(f"Loaded {len(self.players)} players from pre-built pool")
            
        except FileNotFoundError:
            print("Player pool not found. Building it first...")
            self._build_player_pool()
            
    def _build_player_pool(self):
        """
        Build the complete NBA player pool and save it to a JSON file
        """
        print("Building complete NBA player pool...")
        
        # Get all active players
        active_players = self.data_fetcher.get_active_players()
        print(f"Found {len(active_players)} active players")
        
        # Initialize categorized players
        categorized_players = {
            '3': [],  # MVP candidates
            '2': [],  # All-Stars
            '1': [],  # Quality starters
            '0': []   # Role players
        }
        
        # Process each player
        for i, player in enumerate(active_players, 1):
            print(f"Processing player {i}/{len(active_players)}: {player}")
            
            try:
                stats = self.data_fetcher.get_player_stats(player)
                if stats is not None:
                    cost = self._calculate_player_cost(stats)
                    categorized_players[str(cost)].append({
                        'name': player,
                        'stats': stats.to_dict()
                    })
                    print(f"Added {player} to ${cost} category")
            except Exception as e:
                print(f"Error processing {player}: {str(e)}")
                continue
        
        # Save to JSON file
        with open('player_pool.json', 'w') as f:
            json.dump(categorized_players, f, indent=2)
        
        print("\nPlayer pool saved to player_pool.json")
        print("Category counts:")
        for cost, players in categorized_players.items():
            print(f"${cost}: {len(players)} players")
            
        # Load the saved data
        self._load_player_pool()
        
    def get_random_players(self, cost, count=5):
        """
        Get random players from a specific cost category
        """
        players_in_category = [p for p, data in self.players.items() if data['cost'] == cost]
        if len(players_in_category) < count:
            print(f"Warning: Only {len(players_in_category)} players available in ${cost} category")
            return players_in_category
        return random.sample(players_in_category, count)
        
    def get_player_cost(self, player_name):
        """
        Get the cost of a specific player
        """
        return self.players.get(player_name, {}).get('cost', 0)
        
    def get_player_stats(self, player_name):
        """
        Get the stats of a specific player
        """
        return self.player_stats.get(player_name)
        
    def _calculate_player_cost(self, stats):
        """
        Calculate player cost based on performance metrics averaged over 3 seasons
        Returns cost from 0-3 dollars
        """
        if stats is None:
            return 0
            
        # Basic stats weights - adjusted to better reflect impact
        weights = {
            'PTS': 0.45,      # Points (increased weight)
            'AST': 0.20,      # Assists (playmaking)
            'REB': 0.15,      # Rebounds
            'STL': 0.10,      # Steals
            'BLK': 0.10,      # Blocks
            'FG_PCT': 0.05,   # Field Goal Percentage
            'TS_PCT': 0.05    # True Shooting Percentage
        }
        
        # Calculate weighted score
        score = 0
        for stat, weight in weights.items():
            if stat in stats:
                if stat in ['FG_PCT', 'TS_PCT']:
                    # Convert percentages to 0-1 scale
                    score += (stats[stat] / 100) * weight * 10
                else:
                    # Scale counting stats appropriately
                    score += stats[stat] * weight
        
        # Add bonuses for exceptional performance
        if stats['PTS'] >= 25:  # Elite scoring
            score += 15
        elif stats['PTS'] >= 20:  # Very good scoring
            score += 10
        elif stats['PTS'] >= 15:  # Good scoring
            score += 5
            
        if stats['AST'] >= 7:   # Elite playmaking
            score += 8
        elif stats['AST'] >= 5:  # Very good playmaking
            score += 4
            
        if stats['REB'] >= 10:  # Elite rebounding
            score += 8
        elif stats['REB'] >= 7:  # Very good rebounding
            score += 4
            
        if stats['STL'] + stats['BLK'] >= 2.5:  # Elite defense
            score += 8
        elif stats['STL'] + stats['BLK'] >= 1.5:  # Very good defense
            score += 4
            
        if stats['TS_PCT'] >= 0.60:  # Elite efficiency
            score += 4
            
        # Apply games played adjustment
        # Ideal is 246 games (82 games * 3 seasons)
        # Scale down score based on games played percentage
        games_played = stats.get('GP', 0)
        games_played_percentage = min(games_played / 246, 1.0)  # Cap at 100%
        
        # Apply a minimum threshold - players with less than 50% of games get penalized more
        if games_played_percentage < 0.5:
            # More severe penalty for very low games played
            score *= (games_played_percentage * 0.7)  # 70% of their games played percentage
        else:
            # Less severe penalty for moderate to high games played
            score *= (0.5 + (games_played_percentage - 0.5) * 0.8)  # Scale from 50% to 90%
        
        # Normalize score to 0-3 range with adjusted thresholds:
        # $3: Elite players (score > 25) - Only MVP candidates
        # $2: Very good players (score > 18) - All-Stars and high-end starters
        # $1: Solid players (score > 12) - Quality starters and good role players
        # $0: Role players and below (score <= 12) - Bench players and deep bench
        
        if score > 25:
            return 3
        elif score > 18:
            return 2
        elif score > 12:
            return 1
        else:
            return 0
        
    def build_player_pool(self, min_games=20, min_minutes=15):
        """
        Build a pool of players based on their performance over the last 3 seasons.
        Players must meet minimum games and minutes played criteria.
        
        Args:
            min_games (int): Minimum number of games played across all seasons
            min_minutes (float): Minimum average minutes per game
        """
        # Get all active players
        active_players = self.data_fetcher.get_active_players()
        
        # Fetch stats for each player
        for player_name in active_players:
            stats = self.data_fetcher.get_player_stats(player_name)
            
            if stats is not None:
                # Check if player meets minimum criteria
                if stats['GP'] >= min_games and stats['MIN'] >= min_minutes:
                    # Calculate player value
                    value = self._calculate_player_value(stats)
                    
                    # Convert value to cost
                    cost = self._value_to_cost(value)
                    
                    # Add player to pool
                    self.players[player_name] = {'cost': cost}
                    self.player_stats[player_name] = stats
                
    def _calculate_player_value(self, stats: pd.Series) -> float:
        """
        Calculate a player's value based on their statistics
        """
        # Base stats weights
        weights = {
            'PTS': 2.0,     # Points (major factor)
            'AST': 1.5,     # Assists (playmaking)
            'REB': 1.2,     # Rebounds
            'STOCKS': 1.5,  # Combined steals and blocks
            'TS_PCT': 25.0, # True shooting percentage (heavily weighted)
            'AST_TO': 5.0,  # Assist to turnover ratio
            'USG_PCT': 1.0, # Usage rate
            'MIN': 0.2,     # Minutes played
        }
        
        value = 0
        for stat, weight in weights.items():
            if stat in stats:
                value += stats[stat] * weight
        
        # Bonus points for exceptional performance
        
        # Scoring bonuses
        if stats['PTS'] >= 30:  # MVP-level scoring
            value += 25
        elif stats['PTS'] >= 27:  # All-Star level scoring
            value += 20
        elif stats['PTS'] >= 23:  # High-end starter scoring
            value += 15
        
        # Playmaking bonus
        if stats['AST'] >= 8:  # Elite playmaking
            value += 15
        elif stats['AST'] >= 6:  # Very good playmaking
            value += 10
        
        # Rebounding bonus
        if stats['REB'] >= 10:  # Elite rebounding
            value += 15
        elif stats['REB'] >= 8:  # Very good rebounding
            value += 10
        
        # Two-way player bonus
        if stats['STOCKS'] >= 2.5:  # Elite defender
            value += 15
        elif stats['STOCKS'] >= 1.8:  # Good defender
            value += 10
        
        # Efficiency bonus
        if stats['TS_PCT'] >= 0.62:  # Elite efficiency
            value += 15
        elif stats['TS_PCT'] >= 0.58:  # Good efficiency
            value += 10
        
        # Usage rate bonus
        if stats['USG_PCT'] >= 30:  # Primary option
            value += 10
        
        # Minutes played bonus (reliability)
        if stats['MIN'] >= 35:
            value += 10
        elif stats['MIN'] >= 30:
            value += 5
        
        return value
        
    def _value_to_cost(self, value: float) -> float:
        """
        Convert a player's value to a cost between $1 and $5 (whole numbers only)
        """
        # Adjusted value ranges for better star recognition
        min_value = 30   # Minimum value
        max_value = 150  # Maximum value
        
        normalized = (value - min_value) / (max_value - min_value)
        cost = 1 + (normalized * 4)  # Scale to 1-5 range
        
        # Adjusted ranges to properly value stars:
        # $1: 1.0 - 2.0 (role players)
        # $2: 2.0 - 2.8 (solid role players)
        # $3: 2.8 - 3.5 (good starters)
        # $4: 3.5 - 4.0 (all-stars)
        # $5: 4.0+ (superstars)
        if cost < 2.0:
            return 1
        elif cost < 2.8:
            return 2
        elif cost < 3.5:
            return 3
        elif cost < 4.0:
            return 4
        else:
            return 5
        
    def get_available_players(self) -> List[Tuple[str, float]]:
        """
        Get list of available players with their costs
        """
        return [(player, self.get_player_cost(player)) for player in self.players.keys()]
        
    def validate_team(self, selected_players: List[str], budget: float = 15.0) -> bool:
        """
        Validate if a team is within budget and has exactly 5 players
        """
        if len(selected_players) != 5:
            return False
            
        total_cost = sum(self.get_player_cost(player) for player in selected_players)
        return total_cost <= budget

def main():
    # Test the player pool with specific players
    pool = PlayerPool()
    
    # Test with a larger sample of players across all tiers
    test_players = [
        # MVP Candidates
        "Nikola Jokic",
        "Shai Gilgeous-Alexander",
        "Luka Doncic",
        "Joel Embiid",
        "Giannis Antetokounmpo",
        
        # All-Stars
        "Jayson Tatum",
        "Devin Booker",
        "Anthony Davis",
        "Donovan Mitchell",
        "De'Aaron Fox",
        
        # Quality Starters
        "Mikal Bridges",
        "CJ McCollum",
        "Draymond Green",
        "Kristaps Porzingis",
        "Fred VanVleet",
        
        # Solid Role Players
        "Kyle Kuzma",
        "Bojan Bogdanovic",
        "Gary Trent Jr.",
        "Josh Hart",
        "Marcus Smart",
        
        # Role Players
        "Pat Connaughton",
        "Georges Niang",
        "Jae Crowder",
        "Alex Caruso",
        "Joe Harris"
    ]
    
    print("Building player pool with test players...")
    for player in test_players:
        stats = pool.data_fetcher.get_player_stats(player)
        if stats is not None:
            value = pool._calculate_player_value(stats)
            cost = pool._value_to_cost(value)
            pool.players[player] = {'cost': cost}
            pool.player_stats[player] = stats
    
    # Print players by tier with more detailed stats
    print("\nPlayers by Cost Tier:")
    print("-" * 80)
    
    players_by_tier = {}
    for player, cost in pool.get_available_players():
        if cost not in players_by_tier:
            players_by_tier[cost] = []
        players_by_tier[cost].append((player, pool.get_player_stats(player)))
    
    for cost in sorted(players_by_tier.keys(), reverse=True):
        print(f"\n${cost} Players:")
        print("-" * 40)
        for player, stats in players_by_tier[cost]:
            print(f"\n{player}")
            print(f"PPG: {stats['PTS']:.1f}, APG: {stats['AST']:.1f}, RPG: {stats['REB']:.1f}")
            print(f"Stocks: {stats['STOCKS']:.1f}, TS%: {stats['TS_PCT']:.1%}")
            print(f"USG%: {stats['USG_PCT']:.1%}, Minutes: {stats['MIN']:.1f}")
    
    # Show example team combinations
    print("\n" + "-" * 80)
    print("\nExample Team Combinations ($15 budget):")
    print("-" * 80)
    
    # Example 1: Superstar-centric team
    team1 = ["Nikola Jokic", "Kyle Kuzma", "Josh Hart", "Georges Niang", "Alex Caruso"]
    total_cost1 = sum(pool.get_player_cost(player) for player in team1)
    print(f"\nTeam 1 - Superstar Build (Total: ${total_cost1}):")
    for player in team1:
        cost = pool.get_player_cost(player)
        print(f"- {player}: ${cost}")
    
    # Example 2: Balanced team
    team2 = ["De'Aaron Fox", "Fred VanVleet", "Bojan Bogdanovic", "Marcus Smart", "Joe Harris"]
    total_cost2 = sum(pool.get_player_cost(player) for player in team2)
    print(f"\nTeam 2 - Balanced Build (Total: ${total_cost2}):")
    for player in team2:
        cost = pool.get_player_cost(player)
        print(f"- {player}: ${cost}")

if __name__ == "__main__":
    main() 