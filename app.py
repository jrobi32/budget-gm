from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import json
from team_simulator import TeamSimulator
from models import DailyChallenge
import os
from flask_cors import CORS
from datetime import datetime
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')  # Use environment variable if available

# Ensure data directory exists
os.makedirs('data/challenges', exist_ok=True)

# Initialize team simulator
simulator = TeamSimulator()

@app.route('/')
def index():
    # Get the current challenge
    challenge = DailyChallenge()
    
    # Check if user has already submitted for today
    player_name = session.get('player_name')
    has_submitted = False
    
    if player_name:
        submission = challenge.get_player_submission(player_name)
        has_submitted = submission is not None
    
    return render_template('index.html', 
                          challenge=challenge, 
                          player_name=player_name,
                          has_submitted=has_submitted)

@app.route('/login', methods=['POST'])
def login():
    player_name = request.form.get('player_name')
    if player_name:
        session['player_name'] = player_name
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('player_name', None)
    return redirect(url_for('index'))

@app.route('/api/player_pool')
def get_player_pool():
    try:
        # Get 5 random players from each category
        random_players = simulator.get_random_players(count=5)
        if not random_players:
            return jsonify({'error': 'Failed to get random players'}), 500
        return jsonify(random_players)
    except Exception as e:
        logger.error(f"Error getting player pool: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulate', methods=['POST'])
def simulate_team():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        players = data.get('players', [])
        player_name = data.get('player_name', '')

        if len(players) != 5:
            return jsonify({'error': 'Team must have exactly 5 players'}), 400

        if not player_name:
            return jsonify({'error': 'Player name is required'}), 400

        logger.info(f"Simulating team for {player_name} with players: {players}")
        
        result = simulator.simulate_team(players)
        
        if not result or 'win_probability' not in result:
            logger.error(f"Invalid simulation result: {result}")
            return jsonify({'error': 'Invalid simulation result'}), 500

        # Calculate projected record based on win probability
        win_probability = result['win_probability']
        projected_wins = round(82 * win_probability)
        projected_losses = 82 - projected_wins

        response = {
            'wins': projected_wins,
            'losses': projected_losses,
            'win_probability': win_probability
        }
        
        logger.info(f"Simulation result: {response}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error simulating team: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/submit_team', methods=['POST'])
def submit_team():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        players = data.get('players', [])
        player_name = data.get('player_name', '')
        record = data.get('record', {})

        if len(players) != 5:
            return jsonify({'error': 'Team must have exactly 5 players'}), 400

        if not player_name:
            return jsonify({'error': 'Player name is required'}), 400

        if not record or 'wins' not in record or 'losses' not in record:
            return jsonify({'error': 'Invalid record data'}), 400

        # Create data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')

        # Load existing submissions
        submissions_file = 'data/submissions.json'
        submissions = []
        if os.path.exists(submissions_file):
            try:
                with open(submissions_file, 'r') as f:
                    submissions = json.load(f)
            except Exception as e:
                logger.error(f"Error loading submissions: {str(e)}")

        # Add new submission
        submission = {
            'player_name': player_name,
            'players': players,
            'record': record,
            'timestamp': datetime.now().isoformat()
        }
        submissions.append(submission)

        # Save updated submissions
        try:
            with open(submissions_file, 'w') as f:
                json.dump(submissions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving submission: {str(e)}")
            return jsonify({'error': 'Failed to save submission'}), 500

        return jsonify({'message': 'Team submitted successfully'})

    except Exception as e:
        logger.error(f"Error submitting team: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/leaderboard')
def leaderboard():
    # Check if a date parameter is provided
    date = request.args.get('date')
    
    if date:
        # Load the challenge for the specified date
        challenge = DailyChallenge(date)
    else:
        # Get the current challenge
        challenge = DailyChallenge()
    
    leaderboard_data = challenge.get_leaderboard()
    
    player_name = session.get('player_name')
    player_rank = None
    player_percentile = None
    
    if player_name:
        for i, submission in enumerate(leaderboard_data):
            if submission['player_name'] == player_name:
                player_rank = i + 1
                player_percentile = submission.get('percentile', 0)
                break
    
    return render_template('leaderboard.html', 
                          leaderboard=leaderboard_data,
                          player_name=player_name,
                          player_rank=player_rank,
                          player_percentile=player_percentile,
                          challenge_date=challenge.date)

@app.route('/api/check_submission')
def check_submission():
    player_name = request.args.get('player_name')
    date = request.args.get('date')  # Optional date parameter
    
    if not player_name:
        return jsonify({'error': 'Missing player name'}), 400
    
    # Get the challenge for the specified date or today
    challenge = DailyChallenge(date) if date else DailyChallenge()
    
    submission = challenge.get_player_submission(player_name)
    return jsonify({
        'has_submission': submission is not None,
        'submission': submission
    })

@app.route('/api/submitted_team')
def get_submitted_team():
    player_name = request.args.get('player_name')
    date = request.args.get('date')  # Optional date parameter
    
    if not player_name:
        return jsonify({'error': 'Missing player name'}), 400
    
    # Get the challenge for the specified date or today
    challenge = DailyChallenge(date) if date else DailyChallenge()
    
    submission = challenge.get_player_submission(player_name)
    if not submission:
        return jsonify({'error': 'No submission found'}), 404
    
    return jsonify(submission)

@app.route('/api/available_dates')
def get_available_dates():
    challenge = DailyChallenge()
    dates = challenge.get_available_dates()
    return jsonify(dates)

@app.route('/api/challenge/<date>')
def get_challenge_by_date(date):
    challenge = DailyChallenge(date)
    if not challenge.player_pool:
        return jsonify({'error': 'Challenge not found'}), 404
    
    return jsonify({
        'date': challenge.date,
        'player_pool': challenge.player_pool
    })

def load_player_pool():
    try:
        with open('player_pool.json', 'r') as f:
            full_pool = json.load(f)
            
        # Select 5 random players from each category
        limited_pool = {}
        for category in ['$3', '$2', '$1', '$0']:
            players = full_pool.get(category, [])
            if len(players) > 5:
                limited_pool[category] = random.sample(players, 5)
            else:
                limited_pool[category] = players
                
        return limited_pool
    except Exception as e:
        print(f"Error loading player pool: {e}")
        return {"$3": [], "$2": [], "$1": [], "$0": []}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 