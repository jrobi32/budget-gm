from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import json
from team_simulator import TeamSimulator
from models import DailyChallenge
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Ensure data directory exists
os.makedirs('data/challenges', exist_ok=True)

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
    challenge = DailyChallenge()
    # Ensure the player pool is properly formatted
    player_pool = challenge.player_pool
    
    # Log the player pool for debugging
    print("Player pool structure:", player_pool.keys())
    for category in player_pool:
        print(f"{category} players: {len(player_pool[category])}")
        if len(player_pool[category]) > 0:
            print(f"First player in {category}: {player_pool[category][0]['name']}")
    
    return jsonify(player_pool)

@app.route('/api/simulate', methods=['POST'])
def simulate_team():
    data = request.get_json()
    players = data.get('players', [])
    player_name = data.get('playerName', '')
    
    if len(players) != 5:
        return jsonify({'error': 'Team must have exactly 5 players'}), 400
    
    if not player_name:
        return jsonify({'error': 'Player name is required'}), 400
    
    try:
        simulator = TeamSimulator()
        win_probability = simulator.simulate_team(players)
        
        # Calculate projected record
        wins = round(win_probability * 82)
        losses = 82 - wins
        record = f"{wins}-{losses}"
        
        return jsonify({
            'record': record,
            'win_probability': win_probability
        })
    except Exception as e:
        print(f"Error simulating team: {e}")
        return jsonify({'error': 'Error simulating team. Please try again.'}), 500

@app.route('/api/submit_team', methods=['POST'])
def submit_team():
    data = request.get_json()
    player_name = data.get('player_name')
    players = data.get('players')
    
    if not player_name or not players:
        return jsonify({'error': 'Missing player name or players'}), 400
    
    if len(players) != 5:
        return jsonify({'error': 'Team must have exactly 5 players'}), 400
    
    try:
        # Simulate the team
        simulator = TeamSimulator()
        record = simulator.simulate_team(players)
        
        # Submit the team
        challenge = DailyChallenge()
        challenge.submit_team(player_name, players, record)
        
        return jsonify({
            'success': True,
            'record': record
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/leaderboard')
def leaderboard():
    challenge = DailyChallenge()
    leaderboard_data = challenge.get_leaderboard()
    
    player_name = session.get('player_name')
    player_rank = None
    
    if player_name:
        for i, submission in enumerate(leaderboard_data):
            if submission['player_name'] == player_name:
                player_rank = i + 1
                break
    
    return render_template('leaderboard.html', 
                          leaderboard=leaderboard_data,
                          player_name=player_name,
                          player_rank=player_rank,
                          challenge_date=challenge.date)

@app.route('/api/check_submission')
def check_submission():
    player_name = request.args.get('player_name')
    if not player_name:
        return jsonify({'error': 'Missing player name'}), 400
    
    challenge = DailyChallenge()
    submission = challenge.get_player_submission(player_name)
    return jsonify({
        'has_submission': submission is not None
    })

@app.route('/api/submitted_team')
def get_submitted_team():
    player_name = request.args.get('player_name')
    if not player_name:
        return jsonify({'error': 'Missing player name'}), 400
    
    challenge = DailyChallenge()
    submission = challenge.get_player_submission(player_name)
    if not submission:
        return jsonify({'error': 'No submission found'}), 404
    
    return jsonify(submission)

if __name__ == '__main__':
    app.run(debug=True) 