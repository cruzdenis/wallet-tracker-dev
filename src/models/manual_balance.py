from src.models.models import db
from datetime import datetime


class ManualBalance(db.Model):
    """Manual balance entries for historical data before automatic sync"""
    __tablename__ = 'manual_balances'
    
    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    networth = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    wallet = db.relationship('Wallet', backref='manual_balances')
    
    def __repr__(self):
        return f'<ManualBalance wallet_id={self.wallet_id} networth={self.networth} timestamp={self.timestamp}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_id': self.wallet_id,
            'timestamp': self.timestamp.isoformat(),
            'networth': self.networth,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

