from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import tempfile

from src.models.models import db, Wallet, BalanceHistory, ProtocolBalance, TokenBalance, User, WalletPermission, AppSettings

backup_bp = Blueprint('backup', __name__)


def admin_required(f):
    """Decorator to require admin privileges"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function


@backup_bp.route('/export', methods=['GET'])
@login_required
@admin_required
def export_backup():
    """Export database to JSON file"""
    try:
        print("\n📦 Creating database backup...")
        
        backup_data = {
            'version': '1.0',
            'timestamp': datetime.utcnow().isoformat(),
            'wallets': [],
            'users': [],
            'permissions': [],
            'settings': []
        }
        
        # Export wallets
        wallets = Wallet.query.all()
        for wallet in wallets:
            wallet_data = {
                'id': wallet.id,
                'name': wallet.name,
                'address': wallet.address,
                'created_at': wallet.created_at.isoformat() if wallet.created_at else None,
                'balance_history': []
            }
            
            # Export balance history
            history = BalanceHistory.query.filter_by(wallet_id=wallet.id).all()
            for h in history:
                history_data = {
                    'timestamp': h.timestamp.isoformat(),
                    'networth': h.networth,
                    'data_json': h.data_json,
                    'protocols': [],
                    'tokens': []
                }
                
                # Export protocol balances
                protocols = ProtocolBalance.query.filter_by(balance_history_id=h.id).all()
                for p in protocols:
                    history_data['protocols'].append({
                        'protocol_key': p.protocol_key,
                        'protocol_name': p.protocol_name,
                        'value': p.value
                    })
                
                # Export token balances
                tokens = TokenBalance.query.filter_by(balance_history_id=h.id).all()
                for t in tokens:
                    history_data['tokens'].append({
                        'token_symbol': t.token_symbol,
                        'token_name': t.token_name,
                        'balance': t.balance,
                        'value': t.value,
                        'price': t.price,
                        'chain': t.chain,
                        'protocol': t.protocol
                    })
                
                wallet_data['balance_history'].append(history_data)
            
            backup_data['wallets'].append(wallet_data)
        
        # Export users (without passwords for security)
        users = User.query.all()
        for user in users:
            backup_data['users'].append({
                'id': user.id,
                'username': user.username,
                'is_admin': user.is_admin
            })
        
        # Export permissions
        permissions = WalletPermission.query.all()
        for perm in permissions:
            backup_data['permissions'].append({
                'user_id': perm.user_id,
                'wallet_id': perm.wallet_id
            })
        
        # Export settings
        settings = AppSettings.query.all()
        for setting in settings:
            # Don't export sensitive data like API keys
            if setting.key not in ['octav_api_key']:
                backup_data['settings'].append({
                    'key': setting.key,
                    'value': setting.value
                })
        
        # Create temporary file
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f'wallet_tracker_backup_{timestamp}.json'
        
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"   ✓ Backup created: {filename}")
        print(f"   ✓ Wallets: {len(backup_data['wallets'])}")
        print(f"   ✓ Users: {len(backup_data['users'])}")
        
        return send_file(
            filepath,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"\n❌ Error creating backup: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@backup_bp.route('/import', methods=['POST'])
@login_required
@admin_required
def import_backup():
    """Import database from JSON file"""
    try:
        print("\n📥 Importing database backup...")
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.json'):
            return jsonify({'error': 'File must be JSON'}), 400
        
        # Read and parse JSON
        backup_data = json.load(file)
        
        if 'version' not in backup_data or 'wallets' not in backup_data:
            return jsonify({'error': 'Invalid backup file format'}), 400
        
        print(f"   ✓ Backup version: {backup_data['version']}")
        print(f"   ✓ Backup timestamp: {backup_data['timestamp']}")
        
        # Import wallets and their data
        imported_wallets = 0
        imported_history = 0
        
        for wallet_data in backup_data['wallets']:
            # Check if wallet already exists
            existing_wallet = Wallet.query.filter_by(address=wallet_data['address']).first()
            
            if existing_wallet:
                print(f"   ⚠ Wallet {wallet_data['name']} already exists, skipping...")
                continue
            
            # Create new wallet
            wallet = Wallet(
                name=wallet_data['name'],
                address=wallet_data['address']
            )
            db.session.add(wallet)
            db.session.flush()  # Get wallet ID
            
            imported_wallets += 1
            
            # Import balance history
            for history_data in wallet_data['balance_history']:
                balance_history = BalanceHistory(
                    wallet_id=wallet.id,
                    timestamp=datetime.fromisoformat(history_data['timestamp']),
                    networth=history_data['networth'],
                    data_json=history_data.get('data_json', '{}')
                )
                db.session.add(balance_history)
                db.session.flush()  # Get history ID
                
                imported_history += 1
                
                # Import protocol balances
                for protocol_data in history_data['protocols']:
                    protocol_balance = ProtocolBalance(
                        balance_history_id=balance_history.id,
                        protocol_key=protocol_data['protocol_key'],
                        protocol_name=protocol_data['protocol_name'],
                        value=protocol_data['value']
                    )
                    db.session.add(protocol_balance)
                
                # Import token balances
                for token_data in history_data['tokens']:
                    token_balance = TokenBalance(
                        balance_history_id=balance_history.id,
                        token_symbol=token_data['token_symbol'],
                        token_name=token_data['token_name'],
                        balance=token_data['balance'],
                        value=token_data['value'],
                        price=token_data['price'],
                        chain=token_data['chain'],
                        protocol=token_data['protocol']
                    )
                    db.session.add(token_balance)
        
        # Import permissions
        if 'permissions' in backup_data:
            for perm_data in backup_data['permissions']:
                # Only import if both user and wallet exist
                user = User.query.get(perm_data['user_id'])
                wallet = Wallet.query.get(perm_data['wallet_id'])
                
                if user and wallet:
                    existing_perm = WalletPermission.query.filter_by(
                        user_id=perm_data['user_id'],
                        wallet_id=perm_data['wallet_id']
                    ).first()
                    
                    if not existing_perm:
                        permission = WalletPermission(
                            user_id=perm_data['user_id'],
                            wallet_id=perm_data['wallet_id']
                        )
                        db.session.add(permission)
        
        # Import settings (non-sensitive only)
        if 'settings' in backup_data:
            for setting_data in backup_data['settings']:
                existing_setting = AppSettings.query.filter_by(key=setting_data['key']).first()
                if not existing_setting:
                    setting = AppSettings(
                        key=setting_data['key'],
                        value=setting_data['value']
                    )
                    db.session.add(setting)
        
        db.session.commit()
        
        print(f"   ✓ Imported {imported_wallets} wallets")
        print(f"   ✓ Imported {imported_history} balance records")
        print("   ✅ Import completed successfully")
        
        return jsonify({
            'message': 'Backup imported successfully',
            'wallets_imported': imported_wallets,
            'history_records': imported_history
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error importing backup: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

