from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import json
import os
from datetime import datetime
from scraper import DeadmanScraper
from data_processor import DataProcessor
from database import HistoryDatabase

app = Flask(__name__)

# Initialize scraper, data processor, and database
scraper = DeadmanScraper()
data_processor = DataProcessor()
db = HistoryDatabase()

# Global variable to store latest data
latest_data = {}
last_update = None

def update_data():
    """Background task to update hiscores data"""
    global latest_data, last_update
    try:
        print(f"Updating data at {datetime.now()}")
        raw_data = scraper.scrape_all_data()
        latest_data = data_processor.process_data(raw_data)
        last_update = datetime.now()
        
        # Save to database for historical tracking
        db.save_snapshot(latest_data)
        db.save_player_data(raw_data)
        db.save_team_data(latest_data.get('teams', {}))
        
        print(f"Data updated successfully. Teams: {len(latest_data.get('teams', {}))}")
    except Exception as e:
        print(f"Error updating data: {e}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_data, trigger="interval", minutes=15)
scheduler.start()

# Initial data load
update_data()

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
    return jsonify({
        'data': latest_data,
        'last_update': last_update.isoformat() if last_update else None
    })

@app.route('/api/teams')
def api_teams():
    """API endpoint to get team data"""
    teams = latest_data.get('teams', {})
    return jsonify(teams)

@app.route('/api/team/<team_name>')
def api_team(team_name):
    """API endpoint to get specific team data"""
    teams = latest_data.get('teams', {})
    team_data = teams.get(team_name.upper(), {})
    return jsonify(team_data)

@app.route('/api/leaderboards')
def api_leaderboards():
    """API endpoint to get skill leaderboards"""
    leaderboards = latest_data.get('leaderboards', {})
    return jsonify(leaderboards)

@app.route('/api/comparison')
def api_comparison():
    """API endpoint for team comparison data"""
    team1 = request.args.get('team1', '').upper()
    team2 = request.args.get('team2', '').upper()
    
    teams = latest_data.get('teams', {})
    comparison_data = data_processor.compare_teams(teams, team1, team2)
    
    return jsonify(comparison_data)

@app.route('/api/refresh')
def api_refresh():
    """Manual refresh endpoint"""
    update_data()
    return jsonify({'status': 'success', 'message': 'Data refreshed'})

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
    for player_name in player_names:
        player_data = {}
        for skill in data_processor.skills:
            # Get latest data for this player and skill
            leaderboard = latest_data.get('leaderboards', {}).get(skill, [])
            player_stats = next((p for p in leaderboard if p['name'] == player_name), None)
            if player_stats:
                player_data[skill] = player_stats
        comparison_data[player_name] = player_data
    
    return jsonify(comparison_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080) 