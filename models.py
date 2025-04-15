from datetime import datetime
import json
import os

class DailyChallenge:
    def __init__(self, date=None):
        self.date = date or datetime.now().strftime('%Y-%m-%d')
        self.player_pool = {}
        self.submissions = {}
        self.load_challenge()
    
    def load_challenge(self):
        """Load the challenge for the current date or create a new one if it doesn't exist"""
        challenge_file = f'data/challenges/{self.date}.json'
        
        if os.path.exists(challenge_file):
            with open(challenge_file, 'r') as f:
                data = json.load(f)
                self.player_pool = data.get('player_pool', {})
                # Ensure submissions is a dictionary
                submissions = data.get('submissions', {})
                if isinstance(submissions, list):
                    # Convert list to dictionary if necessary
                    self.submissions = {sub['player_name']: sub for sub in submissions}
                else:
                    self.submissions = submissions
        else:
            # Create a new challenge with random players
            self.generate_new_challenge()
    
    def generate_new_challenge(self):
        """Generate a new challenge with random players from the player pool"""
        from team_builder import get_random_players
        
        # Load the full player pool
        with open('player_pool.json', 'r') as f:
            full_pool = json.load(f)
        
        # Select 5 random players from each cost category
        self.player_pool = {
            '$3': get_random_players(full_pool, '$3', 5),
            '$2': get_random_players(full_pool, '$2', 5),
            '$1': get_random_players(full_pool, '$1', 5),
            '$0': get_random_players(full_pool, '$0', 5)
        }
        
        # Save the new challenge
        self.save_challenge()
    
    def save_challenge(self):
        """Save the current challenge to a file"""
        # Ensure the directory exists
        os.makedirs('data/challenges', exist_ok=True)
        
        challenge_file = f'data/challenges/{self.date}.json'
        with open(challenge_file, 'w') as f:
            json.dump({
                'date': self.date,
                'player_pool': self.player_pool,
                'submissions': self.submissions
            }, f, indent=2)
    
    def add_submission(self, player_name, team, record):
        """Add a player submission to the challenge"""
        submission = {
            'player_name': player_name,
            'team': team,
            'record': record,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.submissions[player_name] = submission
        self.save_challenge()
        
        return submission
    
    def get_leaderboard(self):
        """Get the leaderboard for the current challenge"""
        # Sort submissions by wins (descending)
        sorted_submissions = sorted(
            self.submissions.values(), 
            key=lambda x: (x['record']['wins'], -x['record']['losses']), 
            reverse=True
        )
        
        return sorted_submissions
    
    def get_player_submission(self, player_name):
        """Get a player's submission for the current challenge"""
        if isinstance(self.submissions, dict):
            return self.submissions.get(player_name)
        else:
            # If submissions is a list, find the submission with matching player_name
            for submission in self.submissions:
                if submission.get('player_name') == player_name:
                    return submission
            return None
    
    def submit_team(self, player_name, players, record):
        # Get player stats from the player pool
        player_pool = self.load_player_pool()
        players_with_stats = []
        
        for player in players:
            player_found = False
            for cost, player_list in player_pool.items():
                for pool_player in player_list:
                    if pool_player['name'].lower() in player['name'].lower() or player['name'].lower() in pool_player['name'].lower():
                        player_with_stats = player.copy()
                        player_with_stats['stats'] = pool_player['stats']
                        players_with_stats.append(player_with_stats)
                        player_found = True
                        break
                if player_found:
                    break
        
        self.submissions[player_name] = {
            'players': players_with_stats,
            'record': record
        }
        self.save_challenge()
    
    def load_player_pool(self):
        try:
            with open('player_pool.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"$3": [], "$2": [], "$1": [], "$0": []} 