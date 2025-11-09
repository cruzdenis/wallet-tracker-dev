import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_login import LoginManager
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

from src.models.models import db, User
from src.routes.auth import auth_bp
from src.routes.wallets import wallets_bp
from src.routes.admin import admin_bp
from src.routes.settings import settings_bp
from src.routes.backup import backup_bp
from src.routes.portfolio import portfolio_bp
from src.routes.quota import quota_bp
from src.routes.manual_balance import manual_balance_bp
from src.scheduler import init_scheduler

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Apply ProxyFix to handle HTTPS properly behind reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# Database configuration
# Support both PostgreSQL (Railway) and SQLite (local development)
database_url = os.getenv('DATABASE_URL')

if database_url:
    # Railway provides DATABASE_URL for PostgreSQL
    # Fix postgres:// to postgresql:// for SQLAlchemy
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(f"=== Using PostgreSQL database ===")
else:
    # Fallback to SQLite for local development
    # Use /data volume in Railway or project directory locally
    data_dir = os.getenv('DATA_DIR', '/data')
    if not os.path.exists(data_dir):
        # If /data doesn't exist, use project directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_root, 'data')
    
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    print(f"=== Using SQLite database: {db_path} ===")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}

# Enable logging
import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = False  # Allow cookies over HTTP for local dev
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME'] = 'wallet_tracker_session'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
app.config['REMEMBER_COOKIE_DURATION'] = 86400  # 24 hours

# CORS configuration
CORS(app, supports_credentials=True, origins=['*'])

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    # Return JSON for API requests, HTML for others
    from flask import request, jsonify
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Unauthorized'}), 401
    return send_from_directory(app.static_folder, 'index.html')

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(wallets_bp, url_prefix='/api/wallets')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(settings_bp, url_prefix='/api/settings')
app.register_blueprint(backup_bp, url_prefix='/api/backup')
app.register_blueprint(portfolio_bp)
app.register_blueprint(quota_bp)
app.register_blueprint(manual_balance_bp)

# Debug blueprint removed for production

# Create database tables and initialize scheduler
with app.app_context():
    db.create_all()
    
    # Create default admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: username='admin', password='admin123'")
    
    # Scheduler is now running as a separate worker process
    # See scheduler_worker.py and Procfile
    # init_scheduler(app)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

