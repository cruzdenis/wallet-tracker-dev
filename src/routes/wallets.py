from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func

from src.models.models import db, Wallet, WalletPermission, BalanceHistory, ProtocolBalance, TokenBalance
from src.services.octav_service import OctavService

wallets_bp = Blueprint('wallets', __name__)


def user_has_wallet_access(wallet_id):
    """Check if current user has access to wallet"""
    if current_user.is_admin:
        return True
    
    permission = WalletPermission.query.filter_by(
        user_id=current_user.id,
        wallet_id=wallet_id
    ).first()
    
    return permission is not None


@wallets_bp.route('/', methods=['GET'])
@login_required
def get_wallets():
    """Get all wallets accessible by current user"""
    if current_user.is_admin:
        wallets = Wallet.query.all()
    else:
        # Get wallets user has permission to view
        permissions = WalletPermission.query.filter_by(user_id=current_user.id).all()
        wallet_ids = [p.wallet_id for p in permissions]
        wallets = Wallet.query.filter(Wallet.id.in_(wallet_ids)).all() if wallet_ids else []
    
    return jsonify({
        'wallets': [{
            'id': w.id,
            'address': w.address,
            'name': w.name,
            'created_at': w.created_at.isoformat(),
            'last_synced': w.last_synced.isoformat() if w.last_synced else None
        } for w in wallets]
    }), 200


@wallets_bp.route('/<int:wallet_id>/', methods=['GET'])
@wallets_bp.route('/<int:wallet_id>', methods=['GET'])
@login_required
def get_wallet(wallet_id):
    """Get single wallet details"""
    try:
        print(f"\n💼 Getting wallet {wallet_id} details...")
        
        if not user_has_wallet_access(wallet_id):
            print(f"   ❌ Access denied for user {current_user.id}")
            return jsonify({'error': 'Access denied'}), 403
        
        wallet = Wallet.query.get(wallet_id)
        if not wallet:
            print(f"   ❌ Wallet {wallet_id} not found")
            return jsonify({'error': 'Wallet not found'}), 404
        
        # Get latest balance
        latest_balance = BalanceHistory.query.filter_by(wallet_id=wallet_id)\
            .order_by(BalanceHistory.timestamp.desc()).first()
        
        if latest_balance:
            print(f"   ✓ Wallet: {wallet.name} ({wallet.address})")
            print(f"   ✓ Latest balance: ${latest_balance.networth:,.2f}")
        else:
            print(f"   ⚠ Wallet: {wallet.name} - No balance history")
        
        result = {
            'wallet': {
                'id': wallet.id,
                'address': wallet.address,
                'name': wallet.name,
                'created_at': wallet.created_at.isoformat(),
                'last_synced': wallet.last_synced.isoformat() if wallet.last_synced else None,
                'latest_balance': {
                    'networth': latest_balance.networth,
                    'timestamp': latest_balance.timestamp.isoformat()
                } if latest_balance else None
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"\n❌ Error in get_wallet: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@wallets_bp.route('/<int:wallet_id>/balance-history/', methods=['GET'])
@wallets_bp.route('/<int:wallet_id>/balance-history', methods=['GET'])
@login_required
def get_balance_history(wallet_id):
    """Get balance history for a wallet"""
    try:
        print(f"\n📈 Getting balance history for wallet {wallet_id}...")
        
        if not user_has_wallet_access(wallet_id):
            print(f"   ❌ Access denied")
            return jsonify({'error': 'Access denied'}), 403
        
        # Get query parameters
        days = request.args.get('days', default=30, type=int)
        limit = request.args.get('limit', default=100, type=int)
        
        # Calculate date threshold
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        # Query balance history
        history = BalanceHistory.query.filter(
            BalanceHistory.wallet_id == wallet_id,
            BalanceHistory.timestamp >= date_threshold
        ).order_by(BalanceHistory.timestamp.desc()).limit(limit).all()
        
        print(f"   ✓ Found {len(history)} records (last {days} days)")
        
        result = {
            'history': [{
                'id': h.id,
                'timestamp': h.timestamp.isoformat(),
                'networth': h.networth
            } for h in history]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"\n❌ Error in get_balance_history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'history': []}), 500


@wallets_bp.route('/<int:wallet_id>/protocols/', methods=['GET'])
@wallets_bp.route('/<int:wallet_id>/protocols', methods=['GET'])
@login_required
def get_protocol_breakdown(wallet_id):
    """Get protocol breakdown for latest balance"""
    try:
        print(f"\n🔷 Getting protocol breakdown for wallet {wallet_id}...")
        
        if not user_has_wallet_access(wallet_id):
            print(f"   ❌ Access denied")
            return jsonify({'error': 'Access denied'}), 403
        
        # Get latest balance history
        latest_balance = BalanceHistory.query.filter_by(wallet_id=wallet_id)\
            .order_by(BalanceHistory.timestamp.desc()).first()
        
        if not latest_balance:
            print(f"   ⚠ No balance history found")
            return jsonify({'protocols': [], 'timestamp': None}), 200
        
        # Get protocol balances
        protocols = ProtocolBalance.query.filter_by(balance_history_id=latest_balance.id).all()
        
        print(f"   ✓ Found {len(protocols)} protocols")
        for p in protocols:
            print(f"      - {p.protocol_name}: ${p.value:,.2f}")
        
        result = {
            'timestamp': latest_balance.timestamp.isoformat(),
            'protocols': [{
                'name': p.protocol_name,
                'key': p.protocol_key,
                'value': p.value,
                'chain': p.chain
            } for p in protocols]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"\n❌ Error in get_protocol_breakdown: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'protocols': [], 'timestamp': None}), 500


@wallets_bp.route('/<int:wallet_id>/tokens/', methods=['GET'])
@wallets_bp.route('/<int:wallet_id>/tokens', methods=['GET'])
@login_required
def get_token_breakdown(wallet_id):
    """Get token breakdown for latest balance"""
    try:
        print(f"\n🪙 Getting token breakdown for wallet {wallet_id}...")
        
        if not user_has_wallet_access(wallet_id):
            print(f"   ❌ Access denied")
            return jsonify({'error': 'Access denied'}), 403
        
        # Get latest balance history
        latest_balance = BalanceHistory.query.filter_by(wallet_id=wallet_id)\
            .order_by(BalanceHistory.timestamp.desc()).first()
        
        if not latest_balance:
            print(f"   ⚠ No balance history found")
            return jsonify({'tokens': [], 'timestamp': None}), 200
        
        # Get token balances
        tokens = TokenBalance.query.filter_by(balance_history_id=latest_balance.id).all()
        
        print(f"   ✓ Found {len(tokens)} tokens")
        # Show top 5 tokens
        for t in sorted(tokens, key=lambda x: x.value, reverse=True)[:5]:
            print(f"      - {t.token_symbol}: ${t.value:,.2f}")
        
        result = {
            'timestamp': latest_balance.timestamp.isoformat(),
            'tokens': [{
                'symbol': t.token_symbol,
                'name': t.token_name,
                'balance': t.balance,
                'value': t.value,
                'price': t.price,
                'chain': t.chain,
                'protocol': t.protocol
            } for t in tokens]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"\n❌ Error in get_token_breakdown: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'tokens': [], 'timestamp': None}), 500


@wallets_bp.route('/<int:wallet_id>/protocol-history/', methods=['GET'])
@wallets_bp.route('/<int:wallet_id>/protocol-history', methods=['GET'])
@login_required
def get_protocol_history(wallet_id):
    """Get balance history grouped by protocol"""
    try:
        print(f"\n📊 Getting protocol history for wallet {wallet_id}...")
        
        if not user_has_wallet_access(wallet_id):
            print(f"   ❌ Access denied")
            return jsonify({'error': 'Access denied'}), 403
        
        # Get parameters
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Calculate cutoff date
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get balance history
        balance_records = BalanceHistory.query.filter(
            BalanceHistory.wallet_id == wallet_id,
            BalanceHistory.timestamp >= cutoff_date
        ).order_by(BalanceHistory.timestamp.asc()).limit(limit).all()
        
        if not balance_records:
            print(f"   ⚠ No balance history found")
            return jsonify({'history': [], 'protocols': []}), 200
        
        print(f"   ✓ Found {len(balance_records)} balance records")
        
        # Build history with protocol breakdown
        history = []
        all_protocols = set()
        
        for record in balance_records:
            # Get protocol balances for this record
            protocol_balances = ProtocolBalance.query.filter_by(
                balance_history_id=record.id
            ).all()
            
            # Build protocols dict
            protocols_dict = {}
            for pb in protocol_balances:
                protocol_key = pb.protocol_key or 'unknown'
                all_protocols.add(protocol_key)
                protocols_dict[protocol_key] = {
                    'name': pb.protocol_name or protocol_key,
                    'value': pb.value
                }
            
            history.append({
                'timestamp': record.timestamp.isoformat(),
                'networth': record.networth,
                'protocols': protocols_dict
            })
        
        print(f"   ✓ Found {len(all_protocols)} unique protocols")
        
        result = {
            'history': history,
            'protocols': list(all_protocols)
        }
        
        # Disable caching
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response, 200
        
    except Exception as e:
        print(f"\n❌ Error in get_protocol_history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'history': [], 'protocols': []}), 500


@wallets_bp.route('/<int:wallet_id>/sync/', methods=['POST'])
@wallets_bp.route('/<int:wallet_id>/sync', methods=['POST'])
@login_required
def sync_wallet(wallet_id):
    """Manually trigger wallet sync"""
    if not user_has_wallet_access(wallet_id):
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        print(f"\n🔄 Sync request received for wallet ID: {wallet_id}")
        success = OctavService.sync_wallet(wallet_id)
        if success:
            print(f"✅ Wallet {wallet_id} synced successfully")
            return jsonify({'message': 'Wallet synced successfully'}), 200
        else:
            print(f"❌ Failed to sync wallet {wallet_id}")
            return jsonify({'error': 'Failed to sync wallet'}), 500
    except Exception as e:
        print(f"❌ Exception during sync: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@wallets_bp.route('/summary/', methods=['GET'])
@wallets_bp.route('/summary', methods=['GET'])
@login_required
def get_portfolio_summary():
    """Get summary of all accessible wallets"""
    try:
        print("\n📊 Getting portfolio summary...")
        
        if current_user.is_admin:
            wallets = Wallet.query.all()
            print(f"   Admin user - loading all {len(wallets)} wallets")
        else:
            permissions = WalletPermission.query.filter_by(user_id=current_user.id).all()
            wallet_ids = [p.wallet_id for p in permissions]
            wallets = Wallet.query.filter(Wallet.id.in_(wallet_ids)).all() if wallet_ids else []
            print(f"   Regular user - loading {len(wallets)} permitted wallets")
        
        total_networth = 0
        wallet_summaries = []
        
        for wallet in wallets:
            # Get the MOST RECENT balance history for this wallet
            latest_balance = BalanceHistory.query.filter_by(wallet_id=wallet.id)\
                .order_by(BalanceHistory.timestamp.desc()).first()
            
            if latest_balance:
                print(f"   Wallet {wallet.id} ({wallet.name}): ${latest_balance.networth:,.2f}")
                total_networth += latest_balance.networth
                wallet_summaries.append({
                    'id': wallet.id,
                    'address': wallet.address,
                    'name': wallet.name,
                    'networth': latest_balance.networth,
                    'timestamp': latest_balance.timestamp.isoformat()
                })
            else:
                print(f"   Wallet {wallet.id} ({wallet.name}): No balance history")
        
        result = {
            'total_networth': total_networth,
            'wallets': wallet_summaries
        }
        
        print(f"\n✅ Summary: {len(wallet_summaries)} wallets, Total: ${total_networth:,.2f}\n")
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"\n❌ Error in get_portfolio_summary: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'total_networth': 0, 'wallets': []}), 500

