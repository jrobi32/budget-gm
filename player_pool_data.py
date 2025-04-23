import json
import logging
from categorize_players import categorize_players, get_multi_season_stats, convert_to_json_format
from datetime import datetime

def build_player_pool():
    """Build the player pool with stats and costs"""
    try:
        # Get current season
        current_year = datetime.now().year
        current_month = datetime.now().month
        current_season = f"{current_year-1}-{str(current_year)[2:]}" if current_month < 10 else f"{current_year}-{str(current_year+1)[2:]}"
        
        # Get stats for last 3 seasons
        seasons = [
            current_season,
            f"{int(current_season[:4])-1}-{str(int(current_season[:4]))[-2:]}",
            f"{int(current_season[:4])-2}-{str(int(current_season[:4])-1)[-2:]}"
        ]
        
        # Get and process stats
        logging.info("Fetching player statistics for the last 3 seasons...")
        avg_stats = get_multi_season_stats(seasons)
        logging.info("Categorizing players...")
        categorized_players = categorize_players(avg_stats)
        
        # Convert to JSON format
        logging.info("Converting to JSON format...")
        json_data = convert_to_json_format(categorized_players)
        
        # Save to JSON file
        with open('player_pool.json', 'w') as f:
            json.dump(json_data, f, indent=2)
        
        logging.info("Player pool built and saved successfully")
        return json_data
        
    except Exception as e:
        logging.error(f"Error building player pool: {str(e)}")
        raise

def convert_weighted_value_to_cost_tier(weighted_value):
    # Convert weighted value to cost tier
    if weighted_value >= 50:      # $5: Superstars
        return 5
    elif weighted_value >= 40:    # $4: All-Stars
        return 4
    elif weighted_value >= 30:    # $3: Quality starters
        return 3
    elif weighted_value >= 20:    # $2: Solid role players
        return 2
    else:                         # $1: Role players
        return 1

if __name__ == "__main__":
    build_player_pool() 