# 🚀 Quick Deployment Checklist

## Pre-Deployment ✅

- [x] Database is working locally
- [x] All text visibility issues fixed
- [x] Production configuration files created
- [ ] Code committed and pushed to GitHub
- [ ] Requirements.txt is up to date

## Render Deployment Steps

### 1. Simple SQLite Deployment (Recommended for start)
1. **Create Web Service on Render**
   - Connect GitHub repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run.py`

2. **Add Environment Variables:**
   ```
   FLASK_ENV=production
   RENDER=true
   SCRAPE_INTERVAL=900
   ```

3. **Add Persistent Disk:**
   - Name: `database-storage`
   - Mount Path: `/opt/render/project/data`
   - Size: 1GB

### 2. PostgreSQL Deployment (For scaling)
1. **Create PostgreSQL Database first**
2. **Add DATABASE_URL environment variable**
3. **Update requirements.txt** to include `psycopg2-binary`

## Post-Deployment
- [ ] Check logs for errors
- [ ] Verify data scraping is working
- [ ] Test all pages load correctly
- [ ] Monitor for 24 hours

## URLs
- **Render Dashboard**: https://dashboard.render.com/
- **Your App**: Will be `https://deadman-hiscores.onrender.com` (or your chosen name)

## Support
If you run into issues:
1. Check Render logs first
2. Verify environment variables
3. Ensure persistent disk is mounted correctly 