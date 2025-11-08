from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps

from src.models.models import db, AppSettings

settings_bp = Blueprint('settings', __name__)


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@settings_bp.route('/', methods=['GET'])
@login_required
def get_settings():
    """Get all app settings (admin only for sensitive settings)"""
    settings = AppSettings.query.all()
    
    # Non-admin users can only see non-sensitive settings
    if not current_user.is_admin:
        settings = [s for s in settings if s.key == 'sync_interval_hours']
    
    return jsonify({
        'settings': [{
            'key': s.key,
            'value': s.value if s.key != 'octav_api_key' else '***' if s.value else None,
            'updated_at': s.updated_at.isoformat()
        } for s in settings]
    }), 200


@settings_bp.route('/<string:key>', methods=['GET'])
@login_required
def get_setting(key):
    """Get specific setting"""
    # Only admin can access API key
    if key == 'octav_api_key' and not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    setting = AppSettings.query.filter_by(key=key).first()
    
    if not setting:
        return jsonify({'error': 'Setting not found'}), 404
    
    return jsonify({
        'key': setting.key,
        'value': setting.value if key != 'octav_api_key' else '***' if setting.value else None,
        'updated_at': setting.updated_at.isoformat()
    }), 200


@settings_bp.route('/', methods=['POST'])
@admin_required
def update_settings():
    """Update multiple settings"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No settings provided'}), 400
    
    updated = []
    
    for key, value in data.items():
        setting = AppSettings.query.filter_by(key=key).first()
        
        if setting:
            setting.value = str(value) if value is not None else None
        else:
            setting = AppSettings(key=key, value=str(value) if value is not None else None)
            db.session.add(setting)
        
        updated.append(key)
    
    db.session.commit()
    
    # If sync interval was updated, update the scheduler
    if 'sync_interval_hours' in updated:
        from src.scheduler import update_scheduler_job
        with current_app.app_context():
            update_scheduler_job()
    
    return jsonify({
        'message': 'Settings updated successfully',
        'updated': updated
    }), 200


@settings_bp.route('/<string:key>', methods=['PUT'])
@admin_required
def update_setting(key):
    """Update single setting"""
    data = request.get_json()
    
    if not data or 'value' not in data:
        return jsonify({'error': 'Value required'}), 400
    
    setting = AppSettings.query.filter_by(key=key).first()
    
    if setting:
        setting.value = str(data['value']) if data['value'] is not None else None
    else:
        setting = AppSettings(key=key, value=str(data['value']) if data['value'] is not None else None)
        db.session.add(setting)
    
    db.session.commit()
    
    # If sync interval was updated, update the scheduler
    if key == 'sync_interval_hours':
        from src.scheduler import update_scheduler_job
        with current_app.app_context():
            update_scheduler_job()
    
    return jsonify({
        'message': 'Setting updated successfully',
        'key': key,
        'value': setting.value if key != 'octav_api_key' else '***' if setting.value else None
    }), 200


@settings_bp.route('/<string:key>', methods=['DELETE'])
@admin_required
def delete_setting(key):
    """Delete setting"""
    setting = AppSettings.query.filter_by(key=key).first()
    
    if not setting:
        return jsonify({'error': 'Setting not found'}), 404
    
    db.session.delete(setting)
    db.session.commit()
    
    return jsonify({'message': 'Setting deleted successfully'}), 200

