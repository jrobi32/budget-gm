from nba_api.stats.endpoints import leaguedashplayerstats
import pandas as pd
import numpy as np
from datetime import datetime
import json

def get_player_stats(season):
    """Fetch player stats for a given season"""
    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        per_mode_detailed='PerGame',
        season=season,
        season_type_all_star='Regular Season',
        measure_type_detailed_defense='Base'
    )
    return pd.DataFrame(stats.get_data_frames()[0])

def calculate_player_rating(player_stats):
    """Calculate a comprehensive player rating based on multiple statistics"""
    # Weights for different statistics
    weights = {
        'PTS': 1.0,
        'REB': 0.7,
        'AST': 0.7,
        'STL': 0.5,
        'BLK': 0.5,
        'FG_PCT': 0.4,
        'FG3_PCT': 0.3,
        'FT_PCT': 0.3,
        'TOV': -0.3,
        'GP': 0.1
    }
    
    try:
        # Calculate weighted score
        score = (
            player_stats['PTS'] * weights['PTS'] +
            player_stats['REB'] * weights['REB'] +
            player_stats['AST'] * weights['AST'] +
            player_stats['STL'] * weights['STL'] +
            player_stats['BLK'] * weights['BLK'] +
            player_stats['FG_PCT'] * weights['FG_PCT'] * 100 +
            player_stats['FG3_PCT'] * weights['FG3_PCT'] * 100 +
            player_stats['FT_PCT'] * weights['FT_PCT'] * 100 -
            player_stats['TOV'] * weights['TOV'] +
            player_stats['GP'] * weights['GP']
        )
    except:
        score = 0
    
    return score

def categorize_players(df, num_players=500):
    """Categorize players into tiers based on their ratings"""
    # Calculate player ratings
    df['RATING'] = df.apply(calculate_player_rating, axis=1)
    
    # Sort by rating and get top players
    top_players = df.nlargest(num_players, 'RATING')
    
    # Create tiers
    tier_sizes = {
        '$5': int(num_players * 0.08),   # Top 8%
        '$4': int(num_players * 0.17),   # Next 17%
        '$3': int(num_players * 0.25),   # Next 25%
        '$2': int(num_players * 0.25),   # Next 25%
        '$1': int(num_players * 0.25)    # Bottom 25%
    }
    
    # Assign tiers
    top_players['TIER'] = None
    current_idx = 0
    
    for tier, size in tier_sizes.items():
        top_players.iloc[current_idx:current_idx + size, -1] = tier
        current_idx += size
    
    # Fill any remaining players (due to rounding) with $1 tier
    top_players['TIER'] = top_players['TIER'].fillna('$1')
    
    return top_players

def get_multi_season_stats(seasons):
    """Get stats across multiple seasons and average them"""
    all_stats = []
    
    for season in seasons:
        print(f"Fetching stats for season {season}...")
        stats = get_player_stats(season)
        
        # Convert numeric columns to float
        numeric_columns = ['GP', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'FG_PCT', 'FG3_PCT', 'FT_PCT', 'TOV']
        for col in numeric_columns:
            stats[col] = pd.to_numeric(stats[col], errors='coerce')
        
        all_stats.append(stats)
    
    # Combine and average stats across seasons
    combined_stats = pd.concat(all_stats)
    avg_stats = combined_stats.groupby('PLAYER_NAME', as_index=False).agg({
        'PLAYER_ID': 'first',
        'GP': 'mean',
        'MIN': 'mean',
        'PTS': 'mean',
        'REB': 'mean',
        'AST': 'mean',
        'STL': 'mean',
        'BLK': 'mean',
        'FG_PCT': 'mean',
        'FG3_PCT': 'mean',
        'FT_PCT': 'mean',
        'TOV': 'mean'
    })
    
    return avg_stats

def convert_to_json_format(df):
    """Convert the DataFrame to the required JSON format"""
    result = {
        '$5': [],
        '$4': [],
        '$3': [],
        '$2': [],
        '$1': []
    }
    
    for _, row in df.iterrows():
        try:
            player_data = {
                'id': int(row['PLAYER_ID']),
                'name': row['PLAYER_NAME'],
                'stats': {
                    'games_played': float(row['GP']),
                    'points': float(row['PTS']),
                    'rebounds': float(row['REB']),
                    'assists': float(row['AST']),
                    'steals': float(row['STL']),
                    'blocks': float(row['BLK']),
                    'fg_pct': float(row['FG_PCT']),
                    'ft_pct': float(row['FT_PCT']),
                    'three_pct': float(row['FG3_PCT']),
                    'minutes': float(row['MIN'])
                }
            }
            result[row['TIER']].append(player_data)
        except:
            print(f"Warning: Could not convert stats for player {row['PLAYER_NAME']}")
            continue
    
    return result

def main():
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
    print("Fetching player statistics for the last 3 seasons...")
    avg_stats = get_multi_season_stats(seasons)
    print("Categorizing players...")
    categorized_players = categorize_players(avg_stats)
    
    # Convert to JSON format
    print("Converting to JSON format...")
    json_data = convert_to_json_format(categorized_players)
    
    # Save to JSON file
    with open('player_pool.json', 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print("\nResults saved to 'player_pool.json'")
    
    # Print summary
    for tier in ['$5', '$4', '$3', '$2', '$1']:
        tier_players = categorized_players[categorized_players['TIER'] == tier]
        print(f"\n{tier} Tier Players ({len(tier_players)}):")
        print(tier_players[['PLAYER_NAME', 'RATING', 'PTS', 'REB', 'AST']].head().to_string())

if __name__ == "__main__":
    main() 