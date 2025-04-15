#!/usr/bin/env python
"""
Script to generate a new daily challenge for the NBA Team Builder.
Run this script once per day to create a new challenge.
"""

import os
import json
import random
from datetime import datetime
from models import DailyChallenge

def main():
    """Generate a new daily challenge"""
    print("Generating new daily challenge...")
    
    # Create a new challenge for today
    challenge = DailyChallenge()
    
    # The challenge will be automatically generated when initialized
    # because there's no challenge file for today yet
    
    print(f"Challenge for {challenge.date} created successfully!")
    print(f"Player pool: {sum(len(players) for players in challenge.player_pool.values())} players")
    
    # Print the players in each category
    for cost, players in challenge.player_pool.items():
        print(f"\n{cost} Players:")
        for player in players:
            print(f"  - {player['name']}")

if __name__ == "__main__":
    main() 