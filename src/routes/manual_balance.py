from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from src.models.models import db, Wallet, WalletPermission
from src.models.manual_balance import ManualBalance
from datetime import datetime

manual_balance_bp = Blueprint('manual_balance', __name__)


def has_wallet_access(wallet_id):
    """Check if current user has access to the wallet"""
    if current_user.is_admin:
        return True
    
    permission = WalletPermission.query.filter_by(
        user_id=current_user.id,
        wallet_id=wallet_id
    ).first()
    
    return permission is not None


@manual_balance_bp.route('/api/wallets/<int:wallet_id>/manual-balances', methods=['GET'])
@login_required
def get_manual_balances(wallet_id):
    """Get all manual balance entries for a wallet"""
    if not has_wallet_access(wallet_id):
        return jsonify({'error': 'Access denied'}), 403
    
    wallet = Wallet.query.get_or_404(wallet_id)
    
    manual_balances = ManualBalance.query.filter_by(wallet_id=wallet_id)\
        .order_by(ManualBalance.timestamp.desc())\
        .all()
    
    return jsonify({
        'manual_balances': [mb.to_dict() for mb in manual_balances]
    })


@manual_balance_bp.route('/api/wallets/<int:wallet_id>/manual-balances', methods=['POST'])
@login_required
def add_manual_balance(wallet_id):
    """Add a new manual balance entry"""
    if not has_wallet_access(wallet_id):
        return jsonify({'error': 'Access denied'}), 403
    
    wallet = Wallet.query.get_or_404(wallet_id)
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('timestamp') or not data.get('networth'):
        return jsonify({'error': 'Missing required fields: timestamp and networth'}), 400
    
    try:
        # Parse timestamp
        timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        networth = float(data['networth'])
        notes = data.get('notes', '')
        
        # Validate networth
        if networth < 0:
            return jsonify({'error': 'Networth must be positive'}), 400
        
        # Create manual balance entry
        manual_balance = ManualBalance(
            wallet_id=wallet_id,
            timestamp=timestamp,
            networth=networth,
            notes=notes
        )
        
        db.session.add(manual_balance)
        db.session.commit()
        
        return jsonify({
            'message': 'Manual balance added successfully',
            'manual_balance': manual_balance.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to add manual balance: {str(e)}'}), 500


@manual_balance_bp.route('/api/wallets/<int:wallet_id>/manual-balances/<int:balance_id>', methods=['PUT'])
@login_required
def update_manual_balance(wallet_id, balance_id):
    """Update an existing manual balance entry"""
    if not has_wallet_access(wallet_id):
        return jsonify({'error': 'Access denied'}), 403
    
    manual_balance = ManualBalance.query.filter_by(
        id=balance_id,
        wallet_id=wallet_id
    ).first_or_404()
    
    data = request.get_json()
    
    try:
        # Update fields if provided
        if 'timestamp' in data:
            manual_balance.timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        
        if 'networth' in data:
            networth = float(data['networth'])
            if networth < 0:
                return jsonify({'error': 'Networth must be positive'}), 400
            manual_balance.networth = networth
        
        if 'notes' in data:
            manual_balance.notes = data['notes']
        
        manual_balance.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Manual balance updated successfully',
            'manual_balance': manual_balance.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update manual balance: {str(e)}'}), 500


@manual_balance_bp.route('/api/wallets/<int:wallet_id>/manual-balances/<int:balance_id>', methods=['DELETE'])
@login_required
def delete_manual_balance(wallet_id, balance_id):
    """Delete a manual balance entry"""
    if not has_wallet_access(wallet_id):
        return jsonify({'error': 'Access denied'}), 403
    
    manual_balance = ManualBalance.query.filter_by(
        id=balance_id,
        wallet_id=wallet_id
    ).first_or_404()
    
    try:
        db.session.delete(manual_balance)
        db.session.commit()
        
        return jsonify({'message': 'Manual balance deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete manual balance: {str(e)}'}), 500

