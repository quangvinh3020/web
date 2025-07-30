from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.String(36), db.ForeignKey('categories.id'), nullable=False)
    image = db.Column(db.String(255))
    sale = db.Column(db.Float)
    link_demo = db.Column(db.String(500))
    link_tai = db.Column(db.String(500))
    name_key = db.Column(db.String(100))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'category_id': self.category_id,
            'image': self.image,
            'sale': self.sale,
            'link_demo': self.link_demo,
            'link_tai': self.link_tai,
            'name_key': self.name_key,
            'content': self.content,
            'created_at': self.created_at.isoformat()
        } 