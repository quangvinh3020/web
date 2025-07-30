from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    order = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'status': self.status
        } 