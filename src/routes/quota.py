from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime
from src.models.models import db, Wallet, CashFlow, QuotaHistory, BalanceHistory
from src.models.manual_balance import ManualBalance
from sqlalchemy import desc

quota_bp = Blueprint('quota', __name__, url_prefix='/api/quota')

@quota_bp.route('/wallets/<int:wallet_id>/cash-flows/', methods=['GET'])
@login_required
def get_cash_flows(wallet_id):
    """Get all cash flows for a wallet"""
    try:
        wallet = Wallet.query.get_or_404(wallet_id)
        
        # Get cash flows ordered by timestamp (newest first)
        cash_flows = CashFlow.query.filter_by(wallet_id=wallet_id).order_by(desc(CashFlow.timestamp)).all()
        
        return jsonify({
            'cash_flows': [{
                'id': cf.id,
                'timestamp': cf.timestamp.isoformat(),
                'type': cf.type,
                'amount': cf.amount,
                'description': cf.description,
                'quota_value_at_time': cf.quota_value_at_time,
                'quotas_issued': cf.quotas_issued
            } for cf in cash_flows]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quota_bp.route('/wallets/<int:wallet_id>/cash-flows/', methods=['POST'])
@login_required
def add_cash_flow(wallet_id):
    """Add a new cash flow (in or out)"""
    try:
        wallet = Wallet.query.get_or_404(wallet_id)
        data = request.get_json()
        
        # Validate input
        if not data.get('type') or data['type'] not in ['in', 'out']:
            return jsonify({'error': 'Invalid type. Must be "in" or "out"'}), 400
            
        if not data.get('amount') or float(data['amount']) <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400
        
        amount = float(data['amount'])
        flow_type = data['type']
        description = data.get('description', '')
        timestamp = datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.utcnow()
        
        # Get net worth at the time of the cash flow
        # First try to find balance at or before the cash flow date
        balance_at_date = BalanceHistory.query.filter(
            BalanceHistory.wallet_id == wallet_id,
            BalanceHistory.timestamp <= timestamp
        ).order_by(desc(BalanceHistory.timestamp)).first()
        
        # If no automatic balance found, try manual balance
        if not balance_at_date:
            from src.models.manual_balance import ManualBalance
            balance_at_date = ManualBalance.query.filter(
                ManualBalance.wallet_id == wallet_id,
                ManualBalance.timestamp <= timestamp
            ).order_by(desc(ManualBalance.timestamp)).first()
        
        if not balance_at_date:
            return jsonify({'error': f'No balance history found at or before {timestamp.strftime("%Y-%m-%d")}. Please add a balance entry for that date first.'}), 400
        
        current_networth = balance_at_date.networth
        
        # Calculate current quota value
        if wallet.current_quota_quantity > 0:
            current_quota_value = current_networth / wallet.current_quota_quantity
        else:
            # First cash flow - initialize with initial quota value
            current_quota_value = wallet.initial_quota_value
        
        # Calculate quotas issued/redeemed
        if flow_type == 'in':
            # Cash in: issue new quotas at current value
            quotas_issued = amount / current_quota_value
            new_quota_quantity = wallet.current_quota_quantity + quotas_issued
        else:
            # Cash out: redeem quotas at current value
            quotas_issued = amount / current_quota_value
            new_quota_quantity = wallet.current_quota_quantity - quotas_issued
            
            if new_quota_quantity < 0:
                return jsonify({'error': 'Insufficient quotas to redeem'}), 400
        
        # Create cash flow record
        cash_flow = CashFlow(
            wallet_id=wallet_id,
            timestamp=timestamp,
            type=flow_type,
            amount=amount,
            description=description,
            quota_value_at_time=current_quota_value,
            quotas_issued=quotas_issued
        )
        
        # Update wallet quota quantity
        wallet.current_quota_quantity = new_quota_quantity
        
        # Create quota history record
        quota_history = QuotaHistory(
            wallet_id=wallet_id,
            timestamp=timestamp,
            quota_value=current_quota_value,
            quota_quantity=new_quota_quantity,
            networth=current_networth
        )
        
        db.session.add(cash_flow)
        db.session.add(quota_history)
        db.session.commit()
        
        return jsonify({
            'message': 'Cash flow added successfully',
            'cash_flow': {
                'id': cash_flow.id,
                'type': cash_flow.type,
                'amount': cash_flow.amount,
                'quota_value_at_time': cash_flow.quota_value_at_time,
                'quotas_issued': cash_flow.quotas_issued
            },
            'new_quota_quantity': new_quota_quantity,
            'current_quota_value': current_quota_value
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@quota_bp.route('/wallets/<int:wallet_id>/cash-flows/<int:flow_id>/', methods=['DELETE'])
@login_required
def delete_cash_flow(wallet_id, flow_id):
    """Delete a cash flow"""
    try:
        cash_flow = CashFlow.query.filter_by(id=flow_id, wallet_id=wallet_id).first_or_404()
        wallet = Wallet.query.get_or_404(wallet_id)
        
        # Reverse the quota quantity change
        if cash_flow.type == 'in':
            wallet.current_quota_quantity -= cash_flow.quotas_issued
        else:
            wallet.current_quota_quantity += cash_flow.quotas_issued
        
        # Delete associated quota history record
        QuotaHistory.query.filter_by(
            wallet_id=wallet_id,
            timestamp=cash_flow.timestamp
        ).delete()
        
        db.session.delete(cash_flow)
        db.session.commit()
        
        return jsonify({'message': 'Cash flow deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@quota_bp.route('/wallets/<int:wallet_id>/quota-history/', methods=['GET'])
@login_required
def get_quota_history(wallet_id):
    """Get quota value history for performance analysis"""
    try:
        wallet = Wallet.query.get_or_404(wallet_id)
        
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Get quota history
        quota_history = QuotaHistory.query.filter_by(wallet_id=wallet_id)\
            .order_by(QuotaHistory.timestamp)\
            .limit(limit)\
            .all()
        
        # Get automatic balance history
        auto_balance_history = BalanceHistory.query.filter_by(wallet_id=wallet_id)\
            .order_by(BalanceHistory.timestamp)\
            .limit(limit)\
            .all()
        
        # Get manual balance history
        manual_balance_history = ManualBalance.query.filter_by(wallet_id=wallet_id)\
            .order_by(ManualBalance.timestamp)\
            .all()
        
        # Merge both histories
        all_balances = []
        
        # Add automatic balances
        for balance in auto_balance_history:
            all_balances.append({
                'timestamp': balance.timestamp,
                'networth': balance.networth,
                'source': 'automatic'
            })
        
        # Add manual balances
        for balance in manual_balance_history:
            all_balances.append({
                'timestamp': balance.timestamp,
                'networth': balance.networth,
                'source': 'manual'
            })
        
        # Sort by timestamp
        all_balances.sort(key=lambda x: x['timestamp'])
        
        # Get all cash flows to track quota quantity changes over time
        cash_flows = CashFlow.query.filter_by(wallet_id=wallet_id).order_by(CashFlow.timestamp).all()
        
        # Calculate quota value for each balance point
        history_data = []
        for balance in all_balances:
            # Calculate quota quantity at this point in time
            # Start with initial quantity (0 or from first cash flow)
            quota_quantity_at_time = 0
            
            # Add up all cash flows that happened before or at this balance timestamp
            for cf in cash_flows:
                if cf.timestamp <= balance['timestamp']:
                    if cf.type == 'in':
                        quota_quantity_at_time += cf.quotas_issued
                    else:
                        quota_quantity_at_time -= cf.quotas_issued
            
            # Calculate quota value at this point
            if quota_quantity_at_time > 0:
                quota_value = balance['networth'] / quota_quantity_at_time
            else:
                quota_value = wallet.initial_quota_value
            
            history_data.append({
                'timestamp': balance['timestamp'].isoformat(),
                'quota_value': quota_value,
                'networth': balance['networth'],
                'quota_quantity': quota_quantity_at_time,
                'source': balance['source']
            })
        
        # Calculate performance metrics
        if history_data:
            initial_quota_value = history_data[0]['quota_value']
            current_quota_value = history_data[-1]['quota_value']
            performance_pct = ((current_quota_value - initial_quota_value) / initial_quota_value) * 100
        else:
            initial_quota_value = wallet.initial_quota_value
            current_quota_value = wallet.initial_quota_value
            performance_pct = 0
        
        # Calculate total invested (cash in - cash out)
        # cash_flows already loaded above
        total_cash_in = sum(cf.amount for cf in cash_flows if cf.type == 'in')
        total_cash_out = sum(cf.amount for cf in cash_flows if cf.type == 'out')
        total_invested = total_cash_in - total_cash_out
        
        # Get current net worth
        latest_balance = BalanceHistory.query.filter_by(wallet_id=wallet_id)\
            .order_by(desc(BalanceHistory.timestamp)).first()
        current_networth = latest_balance.networth if latest_balance else 0
        
        # Calculate absolute gain/loss
        absolute_gain = current_networth - total_invested
        
        return jsonify({
            'history': history_data,
            'metrics': {
                'current_quota_value': current_quota_value,
                'initial_quota_value': initial_quota_value,
                'performance_pct': performance_pct,
                'quota_quantity': wallet.current_quota_quantity,
                'total_invested': total_invested,
                'current_networth': current_networth,
                'absolute_gain': absolute_gain,
                'roi_pct': (absolute_gain / total_invested * 100) if total_invested > 0 else 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@quota_bp.route('/wallets/<int:wallet_id>/initialize-quotas/', methods=['POST'])
@login_required
def initialize_quotas(wallet_id):
    """Initialize quota system for a wallet with first cash in"""
    try:
        wallet = Wallet.query.get_or_404(wallet_id)
        data = request.get_json()
        
        if wallet.current_quota_quantity > 0:
            return jsonify({'error': 'Quotas already initialized'}), 400
        
        initial_amount = float(data.get('amount', 0))
        if initial_amount <= 0:
            return jsonify({'error': 'Initial amount must be greater than 0'}), 400
        
        # Set initial quota value (default $1.00)
        initial_quota_value = float(data.get('initial_quota_value', 1.0))
        wallet.initial_quota_value = initial_quota_value
        
        # Calculate initial quota quantity
        initial_quota_quantity = initial_amount / initial_quota_value
        wallet.current_quota_quantity = initial_quota_quantity
        
        # Create initial cash flow
        cash_flow = CashFlow(
            wallet_id=wallet_id,
            timestamp=datetime.utcnow(),
            type='in',
            amount=initial_amount,
            description='Initial investment',
            quota_value_at_time=initial_quota_value,
            quotas_issued=initial_quota_quantity
        )
        
        # Create initial quota history
        quota_history = QuotaHistory(
            wallet_id=wallet_id,
            timestamp=datetime.utcnow(),
            quota_value=initial_quota_value,
            quota_quantity=initial_quota_quantity,
            networth=initial_amount
        )
        
        db.session.add(cash_flow)
        db.session.add(quota_history)
        db.session.commit()
        
        return jsonify({
            'message': 'Quotas initialized successfully',
            'initial_quota_value': initial_quota_value,
            'initial_quota_quantity': initial_quota_quantity
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

