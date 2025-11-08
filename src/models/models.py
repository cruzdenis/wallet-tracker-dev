from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    wallet_permissions = db.relationship('WalletPermission', back_populates='user', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'


class Wallet(db.Model):
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_synced = db.Column(db.DateTime, nullable=True)
    
    # Quota system fields
    initial_quota_value = db.Column(db.Float, default=1.0, nullable=False)  # Initial quota value (default $1.00)
    current_quota_quantity = db.Column(db.Float, default=0.0, nullable=False)  # Current number of quotas
    
    # Relationships
    balance_history = db.relationship('BalanceHistory', back_populates='wallet', cascade='all, delete-orphan')
    permissions = db.relationship('WalletPermission', back_populates='wallet', cascade='all, delete-orphan')
    cash_flows = db.relationship('CashFlow', back_populates='wallet', cascade='all, delete-orphan')
    quota_history = db.relationship('QuotaHistory', back_populates='wallet', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Wallet {self.address}>'


class WalletPermission(db.Model):
    __tablename__ = 'wallet_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='wallet_permissions')
    wallet = db.relationship('Wallet', back_populates='permissions')
    
    # Unique constraint: one user can only have one permission per wallet
    __table_args__ = (db.UniqueConstraint('user_id', 'wallet_id', name='unique_user_wallet'),)
    
    def __repr__(self):
        return f'<WalletPermission user_id={self.user_id} wallet_id={self.wallet_id}>'


class BalanceHistory(db.Model):
    __tablename__ = 'balance_history'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    networth = db.Column(db.Float, nullable=False)
    data_json = db.Column(db.Text, nullable=False)  # Store full API response as JSON
    
    # Relationships
    wallet = db.relationship('Wallet', back_populates='balance_history')
    protocol_balances = db.relationship('ProtocolBalance', back_populates='balance_history', cascade='all, delete-orphan')
    token_balances = db.relationship('TokenBalance', back_populates='balance_history', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BalanceHistory wallet_id={self.wallet_id} networth={self.networth}>'


class ProtocolBalance(db.Model):
    __tablename__ = 'protocol_balances'
    
    id = db.Column(db.Integer, primary_key=True)
    balance_history_id = db.Column(db.Integer, db.ForeignKey('balance_history.id'), nullable=False)
    protocol_name = db.Column(db.String(100), nullable=False)
    protocol_key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, nullable=False)
    chain = db.Column(db.String(50), nullable=True)
    
    # Relationships
    balance_history = db.relationship('BalanceHistory', back_populates='protocol_balances')
    
    def __repr__(self):
        return f'<ProtocolBalance {self.protocol_name} value={self.value}>'


class TokenBalance(db.Model):
    __tablename__ = 'token_balances'
    
    id = db.Column(db.Integer, primary_key=True)
    balance_history_id = db.Column(db.Integer, db.ForeignKey('balance_history.id'), nullable=False)
    token_symbol = db.Column(db.String(50), nullable=False)
    token_name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.String(100), nullable=False)  # Store as string to preserve precision
    value = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    chain = db.Column(db.String(50), nullable=True)
    protocol = db.Column(db.String(100), nullable=True)
    
    # Relationships
    balance_history = db.relationship('BalanceHistory', back_populates='token_balances')
    
    def __repr__(self):
        return f'<TokenBalance {self.token_symbol} balance={self.balance}>'


class CashFlow(db.Model):
    """Track cash in/out movements for quota calculation"""
    __tablename__ = 'cash_flows'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'in' or 'out'
    amount = db.Column(db.Float, nullable=False)  # USD value
    description = db.Column(db.Text, nullable=True)
    quota_value_at_time = db.Column(db.Float, nullable=False)  # Quota value when transaction occurred
    quotas_issued = db.Column(db.Float, nullable=False)  # Number of quotas issued/redeemed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    wallet = db.relationship('Wallet', back_populates='cash_flows')
    
    def __repr__(self):
        return f'<CashFlow wallet_id={self.wallet_id} type={self.type} amount={self.amount}>'


class QuotaHistory(db.Model):
    """Track quota value over time for performance analysis"""
    __tablename__ = 'quota_history'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    quota_value = db.Column(db.Float, nullable=False)  # Value of one quota at this time
    quota_quantity = db.Column(db.Float, nullable=False)  # Total number of quotas
    networth = db.Column(db.Float, nullable=False)  # Net worth at this time
    
    # Relationships
    wallet = db.relationship('Wallet', back_populates='quota_history')
    
    def __repr__(self):
        return f'<QuotaHistory wallet_id={self.wallet_id} quota_value={self.quota_value}>'


class AppSettings(db.Model):
    __tablename__ = 'app_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AppSettings {self.key}>'

