from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from src.models.models import Wallet, BalanceHistory, WalletPermission
from src.models.manual_balance import ManualBalance
from sqlalchemy import func
from datetime import datetime, timedelta

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')

@portfolio_bp.route('/history/', methods=['GET'])
@login_required
def get_portfolio_history():
    """Get portfolio total net worth history"""
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Get wallets accessible to user
        if current_user.is_admin:
            wallet_ids = [w.id for w in Wallet.query.all()]
        else:
            permissions = WalletPermission.query.filter_by(user_id=current_user.id).all()
            wallet_ids = [p.wallet_id for p in permissions]
        
        if not wallet_ids:
            return jsonify({'history': [], 'stats': {}})
        
        # Get cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all balance history for accessible wallets (automatic)
        history_records = BalanceHistory.query.filter(
            BalanceHistory.wallet_id.in_(wallet_ids),
            BalanceHistory.timestamp >= cutoff_date
        ).order_by(BalanceHistory.timestamp.asc()).all()
        
        # Get manual balance history for accessible wallets
        manual_records = ManualBalance.query.filter(
            ManualBalance.wallet_id.in_(wallet_ids),
            ManualBalance.timestamp >= cutoff_date
        ).order_by(ManualBalance.timestamp.asc()).all()
        
        # Group by timestamp and wallet_id to avoid duplicates
        # Structure: {timestamp: {wallet_id: networth}}
        timestamp_wallet_data = {}
        
        # Add automatic balance history
        for record in history_records:
            # Round timestamp to nearest hour for grouping
            ts_key = record.timestamp.replace(minute=0, second=0, microsecond=0)
            ts_str = ts_key.isoformat()
            
            if ts_str not in timestamp_wallet_data:
                timestamp_wallet_data[ts_str] = {}
            
            # Store by wallet_id to track which wallets have data at this timestamp
            timestamp_wallet_data[ts_str][record.wallet_id] = record.networth
        
        # Add manual balance history ONLY for wallets that don't have automatic data at that timestamp
        for record in manual_records:
            # Round timestamp to nearest hour for grouping
            ts_key = record.timestamp.replace(minute=0, second=0, microsecond=0)
            ts_str = ts_key.isoformat()
            
            if ts_str not in timestamp_wallet_data:
                timestamp_wallet_data[ts_str] = {}
            
            # Only add manual balance if this wallet doesn't already have automatic data at this timestamp
            if record.wallet_id not in timestamp_wallet_data[ts_str]:
                timestamp_wallet_data[ts_str][record.wallet_id] = record.balance
        
        # Now sum up networth per timestamp
        timestamp_totals = {}
        for ts_str, wallet_data in timestamp_wallet_data.items():
            total_networth = sum(wallet_data.values())
            timestamp_totals[ts_str] = {
                'timestamp': ts_str,
                'networth': total_networth,
                'wallet_count': len(wallet_data)
            }
        
        # Convert to list and sort
        history = sorted(timestamp_totals.values(), key=lambda x: x['timestamp'])
        
        # Calculate statistics
        stats = {}
        if history:
            current_value = history[-1]['networth']
            initial_value = history[0]['networth']
            change = current_value - initial_value
            change_percent = (change / initial_value * 100) if initial_value > 0 else 0
            
            stats = {
                'current': current_value,
                'initial': initial_value,
                'change': change,
                'change_percent': change_percent,
                'data_points': len(history)
            }
        
        return jsonify({
            'history': history,
            'stats': stats
        })
        
    except Exception as e:
        print(f"Error getting portfolio history: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

