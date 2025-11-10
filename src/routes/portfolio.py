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
        
        # Build a timeline of all wallet balances
        # Structure: {wallet_id: [(timestamp, networth), ...]}
        wallet_timelines = {wid: [] for wid in wallet_ids}
        
        # Add automatic balance history
        for record in history_records:
            if not record.timestamp:
                continue
            ts_key = record.timestamp.replace(minute=0, second=0, microsecond=0)
            wallet_timelines[record.wallet_id].append((ts_key, record.networth))
        
        # Add manual balance history (only if no automatic data exists at that time)
        for record in manual_records:
            if not record.timestamp:
                continue
            ts_key = record.timestamp.replace(minute=0, second=0, microsecond=0)
            
            # Check if automatic data exists at this timestamp
            has_auto_data = any(
                ts == ts_key for ts, _ in wallet_timelines[record.wallet_id]
            )
            
            if not has_auto_data:
                wallet_timelines[record.wallet_id].append((ts_key, record.networth))
        
        # Sort each wallet's timeline
        for wid in wallet_ids:
            wallet_timelines[wid].sort(key=lambda x: x[0])
        
        # Get all unique timestamps across all wallets
        all_timestamps = set()
        for timeline in wallet_timelines.values():
            for ts, _ in timeline:
                all_timestamps.add(ts)
        
        if not all_timestamps:
            return jsonify({'history': [], 'stats': {}})
        
        all_timestamps = sorted(all_timestamps)
        
        # Build forward-filled data for each wallet
        # For each timestamp, use the last known value if wallet has no data at that time
        wallet_forward_filled = {}
        
        for wid in wallet_ids:
            timeline = wallet_timelines[wid]
            if not timeline:
                continue
            
            filled_data = {}
            last_value = None
            timeline_idx = 0
            
            for ts in all_timestamps:
                # Check if wallet has data at this timestamp
                if timeline_idx < len(timeline) and timeline[timeline_idx][0] == ts:
                    last_value = timeline[timeline_idx][1]
                    timeline_idx += 1
                
                # Use last known value (forward-fill)
                if last_value is not None:
                    filled_data[ts] = last_value
            
            wallet_forward_filled[wid] = filled_data
        
        # Now sum up all wallets at each timestamp
        history = []
        for ts in all_timestamps:
            total = 0
            wallet_count = 0
            
            for wid in wallet_ids:
                if wid in wallet_forward_filled and ts in wallet_forward_filled[wid]:
                    total += wallet_forward_filled[wid][ts]
                    wallet_count += 1
            
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

