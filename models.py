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
                
                # Debug logging
                print(f"Loaded challenge for {self.date}")
                print(f"Player pool structure: {self.player_pool}")
                print(f"Number of players in each category:")
                for cost, players in self.player_pool.items():
                    print(f"{cost}: {len(players)} players")
                    if players:
                        print(f"First player in {cost}: {players[0]['name']}")
        else:
            # Create a new challenge with random players
            print(f"Challenge file not found for {self.date}, generating new challenge...")
            self.generate_new_challenge()
            # Save the new challenge
            self.save_challenge()
    
    def generate_new_challenge(self):
        """Generate a new challenge with random players from the player pool"""
        from team_builder import get_random_players
        
        # Load the full player pool
        try:
            with open('player_pool.json', 'r') as f:
                full_pool = json.load(f)
                print(f"Loaded full player pool with {sum(len(players) for players in full_pool.values())} players")
        except FileNotFoundError:
            print("Error: player_pool.json not found")
            self.player_pool = {"$3": [], "$2": [], "$1": [], "$0": []}
            return
        
        # Select 5 random players from each cost category
        self.player_pool = {
            '$3': get_random_players(full_pool, '$3', 5),
            '$2': get_random_players(full_pool, '$2', 5),
            '$1': get_random_players(full_pool, '$1', 5),
            '$0': get_random_players(full_pool, '$0', 5)
        }
        
        # Debug logging
        print(f"Generated new challenge for {self.date}")
        print(f"Player pool structure: {self.player_pool}")
        print(f"Number of players in each category:")
        for cost, players in self.player_pool.items():
            print(f"{cost}: {len(players)} players")
            if players:
                print(f"First player in {cost}: {players[0]['name']}")
        
        # Save the new challenge
        self.save_challenge()
    
    def save_challenge(self):
        """Save the current challenge to a file"""
        # Ensure the data directory exists
        os.makedirs('data/challenges', exist_ok=True)
        
        # Create the challenge data
        challenge_data = {
            'date': self.date,
            'player_pool': self.player_pool,
            'submissions': self.submissions
        }
        
        # Save to file
        challenge_file = f'data/challenges/{self.date}.json'
        try:
            with open(challenge_file, 'w') as f:
                json.dump(challenge_data, f, indent=2)
            print(f"Saved challenge to {challenge_file}")
        except Exception as e:
            print(f"Error saving challenge: {e}")
    
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
        
        # Calculate percentile rank
        percentile = self.calculate_percentile(player_name, record)
        
        self.submissions[player_name] = {
            'players': players_with_stats,
            'record': record,
            'percentile': percentile,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.save_challenge()
        
        return {
            'players': players_with_stats,
            'record': record,
            'percentile': percentile
        }
    
    def calculate_percentile(self, player_name, record):
        """Calculate the percentile rank of a player's submission"""
        # Get all submissions with records
        submissions_with_records = [
            sub for sub in self.submissions.values() 
            if 'record' in sub and isinstance(sub['record'], dict) and 'wins' in sub['record']
        ]
        
        # Add the current submission if it's not already in the list
        current_submission = {
            'player_name': player_name,
            'record': record
        }
        
        if current_submission not in submissions_with_records:
            submissions_with_records.append(current_submission)
        
        # Sort by wins (descending)
        sorted_submissions = sorted(
            submissions_with_records,
            key=lambda x: (x['record']['wins'], -x['record']['losses']),
            reverse=True
        )
        
        # Find the rank of the current submission
        total_submissions = len(sorted_submissions)
        if total_submissions <= 1:
            return 100  # If there's only one submission, it's the best
        
        # Find the index of the current submission
        for i, sub in enumerate(sorted_submissions):
            if sub['player_name'] == player_name:
                # Calculate percentile (higher is better)
                percentile = 100 - ((i / (total_submissions - 1)) * 100)
                return round(percentile, 1)
        
        return 0  # Default if not found
    
    def get_percentile_message(self, percentile):
        """Get a friendly message based on the percentile rank"""
        if percentile >= 90:
            return f"You were in the top {percentile}% of players for today's game!"
        elif percentile >= 75:
            return f"You were in the top {percentile}% of players for today's game!"
        elif percentile >= 50:
            return f"You were in the top {percentile}% of players for today's game!"
        elif percentile >= 25:
            return f"You were in the top {percentile}% of players for today's game!"
        else:
            return f"You were in the top {percentile}% of players for today's game!"
    
    def load_player_pool(self):
        try:
            with open('player_pool.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"$3": [], "$2": [], "$1": [], "$0": []}
    
    def get_available_dates(self):
        """Get a list of all available challenge dates"""
        challenge_dir = 'data/challenges'
        if not os.path.exists(challenge_dir):
            return []
        
        dates = []
        for filename in os.listdir(challenge_dir):
            if filename.endswith('.json'):
                date = filename.replace('.json', '')
                dates.append(date)
        
        return sorted(dates, reverse=True)
    
    def get_challenge_by_date(self, date):
        """Get a challenge by date"""
        challenge_file = f'data/challenges/{date}.json'
        if not os.path.exists(challenge_file):
            return None
        
        with open(challenge_file, 'r') as f:
            data = json.load(f)
            return data 