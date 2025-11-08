#!/usr/bin/env python3
"""
Dedicated scheduler worker for automatic wallet synchronization.
This runs as a separate process from the web server to avoid conflicts with Gunicorn workers.
"""
import os
import sys
import time
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv()

# Import after path is set
from src.models.models import db
from src.scheduler import init_scheduler
from flask import Flask

def create_app():
    """Create minimal Flask app for scheduler"""
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///src/database/app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')
    
    # Initialize database
    db.init_app(app)
    
    return app

def main():
    """Main scheduler worker loop"""
    print("\n" + "="*60)
    print("🚀 WALLET TRACKER - SCHEDULER WORKER")
    print("="*60)
    print("📅 Initializing automatic synchronization service...")
    print("="*60 + "\n")
    
    # Create app and push context
    app = create_app()
    
    with app.app_context():
        # Initialize scheduler
        scheduler = init_scheduler(app)
        
        if scheduler:
            print("✅ Scheduler initialized successfully!")
            print("📊 Scheduler is now running in background...")
            print("⏰ Automatic sync will run according to configured interval")
            print("\n" + "="*60)
            print("Press Ctrl+C to stop the scheduler")
            print("="*60 + "\n")
            
            try:
                # Keep the worker alive
                while True:
                    time.sleep(60)  # Sleep for 1 minute
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  Scheduler worker shutting down...")
                if scheduler:
                    scheduler.shutdown()
                print("✅ Scheduler stopped gracefully")
                
        else:
            print("❌ Failed to initialize scheduler!")
            sys.exit(1)

if __name__ == '__main__':
    main()

