# Deadman All Stars - Deployment Guide

## Prerequisites
- GitHub account
- Render account (free tier available)
- Your code pushed to a GitHub repository

## 1. App Deployment on Render

### Step 1: Prepare Your Repository
1. Make sure all your code is committed and pushed to GitHub
2. Ensure your `requirements.txt` is up to date
3. Create a `render.yaml` file (optional but recommended)

### Step 2: Create Web Service on Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:

**Basic Settings:**
- **Name**: `deadman-hiscores` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your default branch)

**Build & Deploy Settings:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python run.py`

**Environment Variables:**
```
FLASK_ENV=production
PORT=8080
```

### Step 3: Advanced Configuration
In the "Advanced" section:
- **Auto-Deploy**: Enable (deploys automatically on git push)
- **Health Check Path**: `/` (optional)

### Step 4: Deploy
1. Click "Create Web Service"
2. Render will automatically build and deploy your app
3. You'll get a URL like: `https://deadman-hiscores.onrender.com`

## 2. Database Deployment on Render

### Option A: PostgreSQL Database (Recommended for Production)

#### Step 1: Create PostgreSQL Database
1. In Render Dashboard, click "New +" → "PostgreSQL"
2. Configure:
   - **Name**: `deadman-hiscores-db`
   - **Database**: `deadman_hiscores`
   - **User**: `deadman_user` (auto-generated)
   - **Region**: Same as your web service
   - **Plan**: Free tier available

#### Step 2: Get Database Connection Details
After creation, you'll get:
- **Internal Database URL**: For connecting from your Render services
- **External Database URL**: For external connections
- **Connection parameters**: Host, Port, Database, Username, Password

#### Step 3: Update Your App for PostgreSQL
You'll need to modify your app to use PostgreSQL instead of SQLite:

1. **Update requirements.txt**:
```
Flask==2.3.3
requests==2.31.0
beautifulsoup4==4.12.2
schedule==1.2.0
psycopg2-binary==2.9.7
```

2. **Create database_postgres.py**:
```python
import psycopg2
import json
import os
from datetime import datetime
from typing import Dict, List, Any

class HistoryDatabase:
    def __init__(self):
        self.db_url = os.environ.get('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.init_database()
    
    def get_connection(self):
        return psycopg2.connect(self.db_url)
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snapshots (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data TEXT NOT NULL
            )
        ''')
        
        # Create player_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_history (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                skill TEXT NOT NULL,
                level INTEGER NOT NULL,
                xp BIGINT NOT NULL,
                rank INTEGER NOT NULL
            )
        ''')
        
        # Create team_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_history (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                team TEXT NOT NULL,
                skill TEXT NOT NULL,
                avg_level REAL NOT NULL,
                avg_xp BIGINT NOT NULL,
                total_xp BIGINT NOT NULL,
                players_count INTEGER NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ... rest of your methods adapted for PostgreSQL
```

#### Step 4: Update Environment Variables
In your Render Web Service, add:
```
DATABASE_URL=<your-postgres-internal-url>
```

### Option B: SQLite with Persistent Storage (Simpler)

#### Step 1: Use Render Persistent Disks
1. In your Web Service settings, go to "Disks"
2. Add a new disk:
   - **Name**: `database-storage`
   - **Mount Path**: `/opt/render/project/data`
   - **Size**: 1GB (free tier)

#### Step 2: Update Database Path
Modify your `database.py` to use the persistent disk:
```python
import os

class HistoryDatabase:
    def __init__(self):
        # Use persistent disk in production, local file in development
        if os.environ.get('RENDER'):
            self.db_path = '/opt/render/project/data/deadman_history.db'
        else:
            self.db_path = 'deadman_history.db'
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
```

#### Step 3: Add Environment Variable
```
RENDER=true
```

## 3. Final Deployment Steps

### Update Your App Configuration
Create `config.py`:
```python
import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # App settings
    SCRAPE_INTERVAL = int(os.environ.get('SCRAPE_INTERVAL', 900))  # 15 minutes
    PORT = int(os.environ.get('PORT', 8080))
    HOST = os.environ.get('HOST', '0.0.0.0')
    
    # Production settings
    DEBUG = os.environ.get('FLASK_ENV') != 'production'
```

### Update run.py for Production
```python
from app import app
from config import Config

if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
```

### Environment Variables Summary
Set these in your Render Web Service:
```
FLASK_ENV=production
PORT=8080
SECRET_KEY=your-secret-key-here
DATABASE_URL=your-database-url-here  # If using PostgreSQL
RENDER=true  # If using SQLite with persistent disk
SCRAPE_INTERVAL=900
```

## 4. Post-Deployment

### Monitoring
- Check Render logs for any errors
- Monitor database connections
- Set up health checks

### Custom Domain (Optional)
1. In Render Dashboard → Your Service → Settings
2. Add your custom domain
3. Configure DNS records as instructed

### SSL Certificate
Render automatically provides SSL certificates for all deployments.

## Troubleshooting

### Common Issues:
1. **Build fails**: Check `requirements.txt` and Python version
2. **Database connection errors**: Verify DATABASE_URL
3. **Port issues**: Ensure you're using the PORT environment variable
4. **Static files**: Make sure static files are included in your repository

### Logs:
Access logs in Render Dashboard → Your Service → Logs

## Cost Considerations

### Free Tier Limits:
- **Web Service**: 750 hours/month (enough for 24/7)
- **PostgreSQL**: 1GB storage, 1 million rows
- **Bandwidth**: 100GB/month

### Paid Plans:
- Start at $7/month for web services
- PostgreSQL starts at $7/month for more storage

Your app should run perfectly on the free tier for development and moderate usage! 