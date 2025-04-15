import json

# Load the player pool
with open('player_pool.json', 'r') as f:
    player_pool = json.load(f)

# Adjust $0 players' stats
if "$0" in player_pool:
    for player in player_pool["$0"]:
        stats = player["stats"]
        # Reduce all stats by 70%
        stats["points"] *= 0.3
        stats["rebounds"] *= 0.3
        stats["assists"] *= 0.3
        stats["steals"] *= 0.3
        stats["blocks"] *= 0.3
        stats["fg_pct"] *= 0.3
        stats["ft_pct"] *= 0.3
        stats["three_pct"] *= 0.3
        stats["minutes"] *= 0.3

# Save the modified player pool
with open('player_pool.json', 'w') as f:
    json.dump(player_pool, f, indent=2)

print("$0 players' stats have been reduced by 70%") 