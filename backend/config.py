import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'touristguard360-dev-secret-key-change-in-production')
    JWT_SECRET = os.environ.get('JWT_SECRET', 'touristguard360-jwt-secret-key')
    JWT_EXPIRY_HOURS = 24
    DATABASE_PATH = os.path.join(BASE_DIR, 'touristguard.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file upload
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'}
    CORS_ORIGINS = '*'
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'touristguard360-encryption-key-32b!')  # Must be 32 bytes for AES-256
