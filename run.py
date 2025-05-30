#!/usr/bin/env python3
"""
Simple script to run the Deadman All Stars Hiscores application
"""

import sys
import os
from app import app
from config import Config

def main():
    """Main function to run the Flask application"""
    try:
        print("🏆 Starting Deadman All Stars Hiscores Tracker...")
        print(f"📊 Data will be scraped and updated every {Config.SCRAPE_INTERVAL // 60} minutes")
        
        if not Config.IS_RENDER:
            print(f"🌐 Access the application at: http://localhost:{Config.PORT}")
            print("⚠️  Press Ctrl+C to stop the application")
            print("-" * 50)
        
        # Run the Flask application
        app.run(
            debug=Config.DEBUG,
            host=Config.HOST,
            port=Config.PORT,
            use_reloader=False  # Disable reloader to prevent scheduler conflicts
        )
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 