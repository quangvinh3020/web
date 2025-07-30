from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class WalletTopup(db.Model):
    __tablename__ = 'wallet_topups'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    content = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='Đang duyệt')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'amount': self.amount,
            'content': self.content,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        } 