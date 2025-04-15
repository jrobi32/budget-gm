import json
import logging
import sys
import time
from data_fetcher import NBADataFetcher

def setup_logging():
    # Remove any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('player_pool.log', mode='w', encoding='utf-8')
        ]
    )

def calculate_player_cost(stats):
    """Calculate player cost based on weighted stats"""
    # Weights for different stats
    weights = {
        'points': 0.5,          # Even higher weight for scoring
        'rebounds': 0.08,       # Reduced weight
        'assists': 0.15,        # Increased weight for playmaking
        'steals': 0.04,         # Reduced weight
        'blocks': 0.04,         # Reduced weight
        'fg_pct': 0.06,         # Increased weight for efficiency
        'ft_pct': 0.04,         # Reduced weight
        'three_pct': 0.04,      # Reduced weight
        'defensive_rating': 0.01,
        'offensive_rating': 0.01,
        'net_rating': 0.01,
        'usage_rate': 0.01,
        'true_shooting': 0.03,  # Increased weight for overall efficiency
        'defensive_rebound_pct': 0.01,
        'offensive_rebound_pct': 0.01,
        'assist_pct': 0.01,
        'steal_pct': 0.01,
        'block_pct': 0.01
    }
    
    # Calculate weighted value
    weighted_value = 0
    for stat, weight in weights.items():
        if stat in stats:
            # Special handling for percentages
            if stat in ['fg_pct', 'ft_pct', 'three_pct', 'true_shooting']:
                weighted_value += (stats[stat] * 100) * weight  # Convert to percentage
            else:
                weighted_value += stats[stat] * weight
    
    # Convert to cost scale (0-3) with new thresholds
    if weighted_value >= 19:      # $3: Elite players
        return 3
    elif weighted_value >= 13:    # $2: Very good players
        return 2
    elif weighted_value >= 7:     # $1: Solid players
        return 1
    else:                         # $0: Role players
        return 0

def build_player_pool():
    """Build the player pool with stats and costs"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize the data fetcher
        fetcher = NBADataFetcher()
        
        # Start with empty player pool
        player_pool = {
            "$3": [],
            "$2": [],
            "$1": [],
            "$0": []
        }
        logger.info("Created new empty player pool")
        
        # Get top 150 scorers
        logger.info("Fetching top 150 scorers...")
        players = fetcher.get_top_scorers(limit=150)
        logger.info(f"Found {len(players)} players to process")
        
        if not players:
            logger.info("No players to process")
            return player_pool
        
        # Process players in chunks
        chunk_size = 10
        total_chunks = (len(players) + chunk_size - 1) // chunk_size
        processed_count = 0
        
        for i in range(0, len(players), chunk_size):
            chunk = players[i:i + chunk_size]
            chunk_num = (i // chunk_size) + 1
            logger.info(f"Processing chunk {chunk_num} of {total_chunks} ({processed_count}/{len(players)} players processed)")
            
            for player in chunk:
                try:
                    logger.info(f"Fetching stats for {player['name']} (ID: {player['id']})")
                    stats = fetcher.get_player_stats(player['id'])
                    
                    if stats:
                        cost = calculate_player_cost(stats)
                        player_data = {
                            "id": player['id'],
                            "name": player['name'],
                            "stats": stats
                        }
                        
                        # Add to appropriate cost category
                        if cost == 3:
                            player_pool["$3"].append(player_data)
                            logger.info(f"{player['name']} added to $3 (Total $3 players: {len(player_pool['$3'])})")
                        elif cost == 2:
                            player_pool["$2"].append(player_data)
                            logger.info(f"{player['name']} added to $2 (Total $2 players: {len(player_pool['$2'])})")
                        elif cost == 1:
                            player_pool["$1"].append(player_data)
                            logger.info(f"{player['name']} added to $1 (Total $1 players: {len(player_pool['$1'])})")
                        else:
                            player_pool["$0"].append(player_data)
                            logger.info(f"{player['name']} added to $0 (Total $0 players: {len(player_pool['$0'])})")
                        
                        processed_count += 1
                    
                    # Add delay between players
                    time.sleep(5)
                    
                except Exception as e:
                    logger.error(f"Error processing {player['name']}: {str(e)}")
                    continue
            
            # Add shorter delay between chunks
            time.sleep(60)  # 1 minute between chunks
            
            # Save progress after each chunk
            with open('player_pool.json', 'w') as f:
                json.dump(player_pool, f, indent=2)
            logger.info(f"Progress saved after chunk {chunk_num} ({processed_count}/{len(players)} players processed)")
        
        # Log final counts
        total_players = sum(len(category) for category in player_pool.values())
        logger.info(f"Final player pool contains {total_players} players:")
        for cost, players in player_pool.items():
            logger.info(f"{cost}: {len(players)} players")
        
        return player_pool
        
    except Exception as e:
        logger.error(f"Error building player pool: {str(e)}")
        return None

if __name__ == "__main__":
    build_player_pool() 