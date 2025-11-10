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
    """Get portfolio total net worth history with forward-fill for missing wallet data"""
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
        
        # Build a map of actual data points per wallet
        # Structure: {wallet_id: {timestamp: networth}}
        wallet_data = {wid: {} for wid in wallet_ids}
        
        # Add automatic balance history
        for record in history_records:
            if not record.timestamp:
                continue
            ts_key = record.timestamp.replace(minute=0, second=0, microsecond=0)
            wallet_data[record.wallet_id][ts_key] = record.networth
        
        # Add manual balance history (only if no automatic data exists at that time)
        for record in manual_records:
            if not record.timestamp:
                continue
            ts_key = record.timestamp.replace(minute=0, second=0, microsecond=0)
            
            # Only add if no automatic data at this timestamp
            if ts_key not in wallet_data[record.wallet_id]:
                wallet_data[record.wallet_id][ts_key] = record.networth
        
        # Get all unique timestamps where AT LEAST ONE wallet has actual data
        all_timestamps = set()
        for wid_data in wallet_data.values():
            all_timestamps.update(wid_data.keys())
        
        if not all_timestamps:
            return jsonify({'history': [], 'stats': {}})
        
        all_timestamps = sorted(all_timestamps)
        
        # Build forward-filled data for each wallet
        # For each timestamp where at least one wallet has data,
        # use last known value for wallets without data at that time
        history = []
        last_known_values = {wid: None for wid in wallet_ids}
        
        for ts in all_timestamps:
            # Update last known values for wallets that have data at this timestamp
            for wid in wallet_ids:
                if ts in wallet_data[wid]:
                    last_known_values[wid] = wallet_data[wid][ts]
            
            # Calculate total using last known values (forward-fill)
            total = 0
            wallet_count = 0
            
            for wid in wallet_ids:
                if last_known_values[wid] is not None:
                    total += last_known_values[wid]
                    wallet_count += 1
            
            # Only add point if at least one wallet has data
            if wallet_count > 0:
                history.append({
                    'timestamp': ts.isoformat(),
                    'networth': total,
                    'wallet_count': wallet_count
                })
        
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
        error_traceback = traceback.format_exc()
        print(error_traceback)
        return jsonify({
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': error_traceback
        }), 500

