# Deadman All Stars Hiscores Tracker

A comprehensive web application for tracking and analyzing the RuneScape Deadman All Stars competition. This application scrapes data from the official hiscores, processes team statistics, and provides beautiful visualizations for comparing team performance.

## Features

### 🏆 Dashboard
- **Live Team Standings**: Real-time rankings based on total XP
- **Skill Leaders**: Top performers in each skill across all teams
- **Interactive Charts**: Team distribution pie chart and performance comparisons
- **Overview Statistics**: Total players, teams, and competition metrics

### 👥 Teams Overview
- **Detailed Team Cards**: Individual team statistics and member information
- **Team Filtering**: Filter by specific teams or view all
- **Modal Details**: In-depth team analysis with skill breakdowns
- **Player Performance**: Individual player statistics within teams

### ⚖️ Team Comparison
- **Side-by-Side Analysis**: Compare any two teams across all skills
- **Radar Charts**: Visual skill comparison with team colors
- **Win/Loss Breakdown**: Skills won by each team
- **Heatmap Visualization**: All teams performance across skills
- **Detailed Tables**: Numerical comparisons with differences

### 📊 Data & Visualization
- **Real-time Updates**: Data refreshes every 15 minutes automatically
- **Interactive Charts**: Built with Plotly.js for responsive visualizations
- **Team Color Coding**: Consistent color scheme across all visualizations
- **Mobile Responsive**: Works perfectly on all device sizes

## Team Structure

The competition features 6 teams with 5 players each:

- **BB (B0aty Brawlers)**: B0aty, Evscape, Pip, Dubie, Port Khaz
- **DN (Dino Nuggets)**: Coxie, Verf, Dino, Westham, Skiddler
- **TT (Torvesta Titans)**: Mammal, Torvesta, eliop14, Lake, Alfie
- **SMO (SkillSpecs Smorcs)**: SkillSpecs, SickNerd, C Enginr, Purpp, SparcMac
- **OW (Odablock Warriors)**: Mika, Rhys, Muts, Mmorpg, Odablock
- **SNA (Solomission Snakes)**: Solomission, Purespam, Ditter, Raikesy, Victim

## Technology Stack

- **Backend**: Python Flask
- **Data Processing**: Pandas, NumPy
- **Web Scraping**: BeautifulSoup, Requests
- **Frontend**: Bootstrap 5, JavaScript
- **Visualizations**: Plotly.js
- **Scheduling**: APScheduler for automated updates
- **Deployment**: Gunicorn ready for production

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd deadman_hiscores
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   Open your browser and navigate to `http://localhost:8080`

### Production Deployment

The application is ready for deployment on platforms like Render, Heroku, or any VPS.

#### Render Deployment
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Use the following settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3

#### Environment Variables
No environment variables are required for basic functionality.

## API Endpoints

The application provides several API endpoints for accessing data:

- `GET /api/data` - Complete dataset with teams, leaderboards, and statistics
- `GET /api/teams` - All team data
- `GET /api/team/<team_name>` - Specific team data
- `GET /api/leaderboards` - Skill leaderboards
- `GET /api/comparison?team1=<team1>&team2=<team2>` - Team comparison data
- `GET /api/refresh` - Manual data refresh trigger

## Data Sources

The application scrapes data from the official RuneScape hiscores:
- **Base URL**: `https://secure.runescape.com/m=hiscore_oldschool_tournament/`
- **Skills Tracked**: 24 skills including Overall, Combat, and Skilling
- **Update Frequency**: Every 15 minutes
- **Data Points**: Player names, levels, XP, rankings

## Features in Detail

### Automatic Data Updates
- Background scheduler runs every 15 minutes
- Scrapes all skill pages (pages 1-2 to capture all competitors)
- Processes raw data into team statistics
- Calculates averages, totals, and rankings
- Updates all visualizations automatically

### Team Analytics
- **Average Statistics**: Mean levels and XP across team members
- **Total Statistics**: Combined team XP and player counts
- **Best Players**: Top performer in each skill per team
- **Rankings**: Team positions in each skill category

### Responsive Design
- Mobile-first approach with Bootstrap 5
- RuneScape-themed color scheme (gold, brown, dark)
- Smooth animations and hover effects
- Accessible navigation and controls

## Customization

### Adding New Teams
Update the `team_prefixes` dictionary in both `scraper.py` and `data_processor.py`:

```python
self.team_prefixes = {
    'BB': 'B0aty Brawlers',
    'DN': 'Dino Nuggets',
    # Add new teams here
}
```

### Modifying Update Frequency
Change the interval in `app.py`:

```python
scheduler.add_job(func=update_data, trigger="interval", minutes=15)  # Change minutes value
```

### Custom Styling
Modify the CSS variables in `templates/base.html`:

```css
:root {
    --rs-gold: #FFD700;
    --rs-dark: #2C1810;
    /* Add custom colors */
}
```

## Troubleshooting

### Common Issues

1. **Data not loading**: Check if the hiscores website is accessible
2. **Slow performance**: Reduce update frequency or optimize scraping
3. **Missing teams**: Verify team prefixes match player names
4. **Charts not displaying**: Ensure Plotly.js is loaded correctly

### Debugging

Enable debug mode in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=8080)
```

Check console logs for scraping errors and data processing issues.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and entertainment purposes. Please respect the RuneScape terms of service when scraping data.

## Acknowledgments

- Jagex for RuneScape and the Deadman competition
- All the content creators participating in Deadman All Stars
- Bootstrap and Plotly.js for excellent frontend libraries 