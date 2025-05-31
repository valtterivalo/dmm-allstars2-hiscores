# Database Management Guide

## Overview

The Deadman All Stars hiscores application uses SQLite databases to store historical tournament data. The database behavior is designed to protect production data continuity while allowing local development.

## Database Locations

- **Production (Render)**: `/opt/render/project/data/deadman_history.db`
- **Development (Local)**: `deadman_history.db` (in project root)

## Data Protection Features

### 1. Environment-Aware Behavior
- **Production**: Saves all data normally, tagged as "production" source
- **Development**: Only saves data if no recent production data exists (prevents overwriting)

### 2. Deduplication
- Snapshots are hashed to prevent duplicate saves
- Player/team data uses UNIQUE constraints to prevent duplicates
- Recent identical data (within 1 hour) is automatically skipped

### 3. Data Continuity Protection
When running locally:
- If production data exists from the last 2 hours, local saves are skipped
- This prevents your local testing from interfering with production data collection
- You'll see messages like "Development mode: Skipping save due to recent production data"

## Database Schema

### Tables
1. **snapshots**: Complete data snapshots every 15 minutes
   - `timestamp`, `data`, `data_hash`, `source`
2. **player_history**: Individual player progress over time
   - `timestamp`, `player_name`, `team`, `skill`, `level`, `xp`, `rank`
3. **team_history**: Team aggregate statistics over time
   - `timestamp`, `team`, `skill`, `avg_level`, `avg_xp`, `total_xp`, `players_count`

## Monitoring Database Health

### 1. Check Database Status Locally
```bash
python check_database.py
```

### 2. View Database Stats via API
Visit: `https://your-app-url.com/api/database/stats`

### 3. Expected Data Volume
- **Snapshots**: ~96 per day (every 15 minutes)
- **Player records**: ~2,400 per day (24 skills × 100 players × 1 update/15min)
- **Team records**: ~144 per day (24 skills × 6 teams × 1 update/15min)

## Deployment Workflow

### Safe Development Process
1. **Local Testing**: Your local database won't interfere with production
2. **Push to Main**: Production continues collecting data uninterrupted
3. **Deploy**: New code deploys without affecting existing data

### What Happens During Deployment
- Production database persists across deployments
- New code starts using existing database immediately
- No data loss or interruption in collection

## Data Analytics Capabilities

With continuous data collection, you can analyze:
- Team performance trends over time
- Individual player progress
- Skill-specific competition dynamics
- Tournament momentum shifts
- Peak activity periods

## Troubleshooting

### If You See "No Data" After Deployment
1. Check database stats: `/api/database/stats`
2. Look for recent snapshots in logs
3. Verify scraping is working (check for "Data updated successfully" messages)

### If Local Development Shows Stale Data
This is normal! Local development loads the last production snapshot but doesn't update it to protect production data continuity.

### Database Recovery
If something goes wrong, the database contains:
- Complete snapshots for point-in-time recovery
- Granular player/team history for detailed analysis
- Source tracking to identify data origin

## Best Practices

1. **Don't manually edit the production database**
2. **Use the check script before major changes**
3. **Monitor the database stats endpoint regularly**
4. **Let the system handle deduplication automatically**

## Future Enhancements

Potential improvements:
- Automated database backups
- Data export functionality for analysis
- Real-time analytics dashboard
- Historical comparison tools 