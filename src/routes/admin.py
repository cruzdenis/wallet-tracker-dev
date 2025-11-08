from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from src.models.models import db, User, Wallet, WalletPermission, AppSettings
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ========== USER MANAGEMENT ==========

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """List all users"""
    users = User.query.all()
    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'is_admin': u.is_admin
        } for u in users]
    }), 200


@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """Create a new user"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password required'}), 400
    
    # Check if username already exists
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400
    
    # Create new user
    user = User(
        username=data['username'],
        password_hash=generate_password_hash(data['password']),
        is_admin=data.get('is_admin', False)
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        }
    }), 201


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if data.get('username'):
        # Check if new username is already taken
        existing = User.query.filter_by(username=data['username']).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Username already exists'}), 400
        user.username = data['username']
    
    if data.get('password'):
        user.password_hash = generate_password_hash(data['password'])
    
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        }
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete user"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200


# ========== WALLET MANAGEMENT ==========

@admin_bp.route('/wallets', methods=['POST'])
@admin_required
def create_wallet():
    """Create a new wallet - SIMPLIFIED VERSION"""
    data = request.get_json()
    
    if not data or not data.get('address'):
        return jsonify({'error': 'Wallet address required'}), 400
    
    # Check if wallet already exists
    existing_wallet = Wallet.query.filter_by(address=data['address']).first()
    if existing_wallet:
        return jsonify({'error': 'Wallet already exists'}), 400
    
    # Create new wallet
    wallet = Wallet(
        address=data['address'],
        name=data.get('name')
    )
    
    db.session.add(wallet)
    db.session.commit()
    
    return jsonify({
        'message': 'Wallet created successfully',
        'wallet': {
            'id': wallet.id,
            'address': wallet.address,
            'name': wallet.name
        }
    }), 201


@admin_bp.route('/wallets/<int:wallet_id>', methods=['PUT'])
@admin_required
def update_wallet(wallet_id):
    """Update wallet"""
    wallet = Wallet.query.get(wallet_id)
    if not wallet:
        return jsonify({'error': 'Wallet not found'}), 404
    
    data = request.get_json()
    
    if data.get('address'):
        # Check if new address is already taken
        existing = Wallet.query.filter_by(address=data['address']).first()
        if existing and existing.id != wallet_id:
            return jsonify({'error': 'Wallet address already exists'}), 400
        wallet.address = data['address']
    
    if 'name' in data:
        wallet.name = data['name']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Wallet updated successfully',
        'wallet': {
            'id': wallet.id,
            'address': wallet.address,
            'name': wallet.name
        }
    }), 200


@admin_bp.route('/wallets/<int:wallet_id>', methods=['DELETE'])
@admin_required
def delete_wallet(wallet_id):
    """Delete wallet"""
    wallet = Wallet.query.get(wallet_id)
    if not wallet:
        return jsonify({'error': 'Wallet not found'}), 404
    
    db.session.delete(wallet)
    db.session.commit()
    
    return jsonify({'message': 'Wallet deleted successfully'}), 200


# ========== PERMISSION MANAGEMENT ==========

@admin_bp.route('/permissions', methods=['GET'])
@admin_required
def list_permissions():
    """List all wallet permissions"""
    permissions = WalletPermission.query.all()
    return jsonify({
        'permissions': [{
            'id': p.id,
            'user_id': p.user_id,
            'wallet_id': p.wallet_id,
            'username': p.user.username,
            'wallet_address': p.wallet.address,
            'wallet_name': p.wallet.name
        } for p in permissions]
    }), 200


@admin_bp.route('/permissions', methods=['POST'])
@admin_required
def grant_permission():
    """Grant wallet access to user"""
    data = request.get_json()
    
    if not data or not data.get('user_id') or not data.get('wallet_id'):
        return jsonify({'error': 'User ID and Wallet ID required'}), 400
    
    # Check if permission already exists
    existing = WalletPermission.query.filter_by(
        user_id=data['user_id'],
        wallet_id=data['wallet_id']
    ).first()
    
    if existing:
        return jsonify({'error': 'Permission already exists'}), 400
    
    # Create permission
    permission = WalletPermission(
        user_id=data['user_id'],
        wallet_id=data['wallet_id']
    )
    
    db.session.add(permission)
    db.session.commit()
    
    return jsonify({
        'message': 'Permission granted successfully',
        'permission': {
            'id': permission.id,
            'user_id': permission.user_id,
            'wallet_id': permission.wallet_id
        }
    }), 201


@admin_bp.route('/permissions/<int:permission_id>', methods=['DELETE'])
@admin_required
def revoke_permission(permission_id):
    """Revoke wallet access from user"""
    permission = WalletPermission.query.get(permission_id)
    if not permission:
        return jsonify({'error': 'Permission not found'}), 404
    
    db.session.delete(permission)
    db.session.commit()
    
    return jsonify({'message': 'Permission revoked successfully'}), 200

