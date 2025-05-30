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
    
    # Render-specific settings
    IS_RENDER = os.environ.get('RENDER') == 'true' 