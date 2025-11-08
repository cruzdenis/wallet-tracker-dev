#!/usr/bin/env python3
"""
Wallet Tracker - Local Execution Script
Run this script to start the application locally
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Wallet Tracker - Starting Local Server")
    print("=" * 60)
    print()
    print("📍 Access the application at: http://localhost:5000")
    print("👤 Default credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print()
    print("⚠️  Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    # Run the Flask app
    app.run(
        host='127.0.0.1',  # Only accessible from this computer
        port=5000,
        debug=True,        # Enable debug mode for development
        use_reloader=True  # Auto-reload on code changes
    )

