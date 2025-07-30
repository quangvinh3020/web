import os
from datetime import timedelta

class Config:
    SECRET_KEY = 'your_jwt_secret'
    SQLALCHEMY_DATABASE_URI = 'mongodb+srv://admin:971012@admin.7oi2tx6.mongodb.net/?retryWrites=true&w=majority&appName=admin'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    JWT_SECRET_KEY = 'your_jwt_secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Momo payment configuration
    PARTNER_CODE = 'MOMO...'
    ACCESS_KEY = '...'
    SECRET_KEY = '...'
    MOMO_ENDPOINT = 'https://test-payment.momo.vn/v2/gateway/api/create'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'} 