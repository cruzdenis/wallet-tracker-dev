from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from src.models.models import db, User, Wallet, BalanceHistory, AppSettings
from src.models.manual_balance import ManualBalance

debug_bp = Blueprint('debug', __name__)


@debug_bp.route('/db-status', methods=['GET'])
@login_required
def db_status():
    """Debug endpoint to check database contents"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        users = User.query.all()
        wallets = Wallet.query.all()
        balances = BalanceHistory.query.all()
        settings = AppSettings.query.first()
        
        # Check if ManualBalance table exists
        manual_balances = []
        manual_balance_error = None
        try:
            manual_balances = ManualBalance.query.all()
        except Exception as e:
            manual_balance_error = str(e)
        
        return jsonify({
            'database_status': 'connected',
            'users': {
                'count': len(users),
                'list': [{
                    'id': u.id,
                    'username': u.username,
                    'is_admin': u.is_admin
                } for u in users]
            },
            'wallets': {
                'count': len(wallets),
                'list': [{
                    'id': w.id,
                    'address': w.address,
                    'name': w.name,
                    'created_at': w.created_at.isoformat(),
                    'last_synced': w.last_synced.isoformat() if w.last_synced else None
                } for w in wallets]
            },
            'balance_history': {
                'count': len(balances),
                'sample': [{
                    'id': b.id,
                    'wallet_id': b.wallet_id,
                    'networth': b.networth,
                    'timestamp': b.timestamp.isoformat()
                } for b in balances[:5]]  # Just show first 5
            },
            'settings': {
                'api_key_configured': bool(settings and settings.octav_api_key),
                'sync_interval': settings.sync_interval_hours if settings else None
            } if settings else None,
            'manual_balance': {
                'table_exists': manual_balance_error is None,
                'count': len(manual_balances) if manual_balance_error is None else 0,
                'error': manual_balance_error,
                'sample': [{
                    'id': mb.id,
                    'wallet_id': mb.wallet_id,
                    'networth': mb.networth,
                    'timestamp': mb.timestamp.isoformat() if mb.timestamp else None
                } for mb in manual_balances[:5]] if manual_balance_error is None else []
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'database_status': 'error'
        }), 500

