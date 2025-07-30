from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class TopupCard(db.Model):
    __tablename__ = 'topup_cards'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    card_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    serial = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Đang duyệt')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'card_type': self.card_type,
            'amount': self.amount,
            'serial': self.serial,
            'code': self.code,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        } 