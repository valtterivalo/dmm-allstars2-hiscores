from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import json
import os
from datetime import datetime
import threading
from scraper import DeadmanScraper
from data_processor import DataProcessor
from database import HistoryDatabase

app = Flask(__name__)

# Initialize scraper, data processor, and database
scraper = DeadmanScraper()
data_processor = DataProcessor()
db = HistoryDatabase()

# Global variable to store latest data with thread safety
latest_data = {}
last_update = None
data_lock = threading.Lock()

def load_initial_data():
    """Load initial data from database if available"""
    global latest_data, last_update
    try:
        # Show database statistics
        db_stats = db.get_database_stats()
        print("=== Database Statistics ===")
        print(f"Total snapshots: {db_stats.get('total_snapshots', 0)}")
        print(f"Snapshots by source: {db_stats.get('snapshots_by_source', {})}")
        print(f"Date range: {db_stats.get('snapshot_date_range', {}).get('earliest', 'N/A')} to {db_stats.get('snapshot_date_range', {}).get('latest', 'N/A')}")
        print(f"Total player records: {db_stats.get('total_player_records', 0)}")
        print(f"Unique players tracked: {db_stats.get('unique_players', 0)}")
        print(f"Snapshots in last 24h: {db_stats.get('snapshots_last_24h', 0)}")
        print("===========================")
        
        # Try to load the most recent snapshot from database
        snapshot_data = db.get_latest_snapshot()
        if snapshot_data:
            with data_lock:
                latest_data = snapshot_data
                last_update = datetime.now()  # We don't store exact timestamp in snapshot
            print("Loaded initial data from database")
        else:
            print("No existing data in database, will wait for first scrape")
    except Exception as e:
        print(f"Error loading initial data: {e}")

def update_data():
    """Background task to update hiscores data"""
    global latest_data, last_update
    try:
        print(f"Starting data update at {datetime.now()}")
        raw_data = scraper.scrape_all_data()
        
        # Process the data
        processed_data = data_processor.process_data(raw_data)
        
        # Only update global data if processing was successful and we have valid data
        if processed_data and processed_data.get('teams'):
            with data_lock:
                latest_data = processed_data
                last_update = datetime.now()
            
            # Save to database for historical tracking
            try:
                db.save_snapshot(processed_data)
                db.save_player_data(raw_data)
                db.save_team_data(processed_data.get('teams', {}))
            except Exception as db_error:
                print(f"Error saving to database: {db_error}")
            
            print(f"Data updated successfully. Teams: {len(processed_data.get('teams', {}))}")
        else:
            print("Processed data was empty or invalid, keeping existing data")
            
    except Exception as e:
        print(f"Error updating data: {e}")
        print("Keeping existing data until next update cycle")

# Load initial data from database
load_initial_data()

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_data, trigger="interval", minutes=15)
scheduler.start()

# Start initial data update in background (don't block startup)
def initial_update():
    """Run initial update without blocking startup"""
    try:
        update_data()
    except Exception as e:
        print(f"Initial update failed: {e}")

# Run initial update in a separate thread
import threading
initial_thread = threading.Thread(target=initial_update)
initial_thread.daemon = True
initial_thread.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/teams')
def teams():
    """Teams overview page"""
    return render_template('teams.html')

@app.route('/compare')
def compare():
    """Team comparison page"""
    return render_template('compare.html')

@app.route('/players')
def players():
    """Player comparison page"""
    return render_template('players.html')

@app.route('/api/data')
def api_data():
    """API endpoint to get all processed data"""
    with data_lock:
        return jsonify({
            'data': latest_data,
            'last_update': last_update.isoformat() if last_update else None
        })

@app.route('/api/teams')
def api_teams():
    """API endpoint to get team data"""
    with data_lock:
        teams = latest_data.get('teams', {})
    return jsonify(teams)

@app.route('/api/team/<team_name>')
def api_team(team_name):
    """API endpoint to get specific team data"""
    with data_lock:
        teams = latest_data.get('teams', {})
        team_data = teams.get(team_name.upper(), {})
    return jsonify(team_data)

@app.route('/api/leaderboards')
def api_leaderboards():
    """API endpoint to get skill leaderboards"""
    with data_lock:
        leaderboards = latest_data.get('leaderboards', {})
    return jsonify(leaderboards)

@app.route('/api/comparison')
def api_comparison():
    """API endpoint for team comparison data"""
    try:
        team1 = request.args.get('team1', '').upper()
        team2 = request.args.get('team2', '').upper()
        
        if not team1 or not team2:
            return jsonify({'error': 'Both team1 and team2 parameters are required'}), 400
        
        with data_lock:
            teams = latest_data.get('teams', {})
        
        if not teams:
            return jsonify({'error': 'No team data available'}), 503
            
        comparison_data = data_processor.compare_teams(teams, team1, team2)
        
        return jsonify(comparison_data)
    except Exception as e:
        print(f"Error in team comparison: {e}")
        return jsonify({'error': f'Error loading comparison data: {str(e)}'}), 500

@app.route('/api/history/player/<player_name>')
def api_player_history(player_name):
    """Get historical data for a specific player"""
    skill = request.args.get('skill', 'overall')
    history = db.get_player_history(player_name, skill)
    return jsonify(history)

@app.route('/api/history/team/<team_name>')
def api_team_history(team_name):
    """Get historical data for a specific team"""
    skill = request.args.get('skill', 'overall')
    history = db.get_team_history(team_name.upper(), skill)
    return jsonify(history)

@app.route('/api/players')
def api_players():
    """Get list of all players"""
    players = db.get_all_players()
    return jsonify(players)

@app.route('/api/compare/players')
def api_compare_players():
    """Compare two or more players"""
    player_names = request.args.getlist('players')
    if len(player_names) < 2:
        return jsonify({'error': 'At least 2 players required for comparison'})
    
    comparison_data = {}
    with data_lock:
        current_leaderboards = latest_data.get('leaderboards', {})
    
    for player_name in player_names:
        player_data = {}
        for skill in data_processor.skills:
            # Get latest data for this player and skill
            leaderboard = current_leaderboards.get(skill, [])
            player_stats = next((p for p in leaderboard if p['name'] == player_name), None)
            if player_stats:
                player_data[skill] = player_stats
        comparison_data[player_name] = player_data
    
    return jsonify(comparison_data)

@app.route('/api/database/stats')
def api_database_stats():
    """Get database statistics for monitoring"""
    try:
        stats = db.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080) 