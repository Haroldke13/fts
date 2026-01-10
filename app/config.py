# Flask config
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
    # Use DATABASE_URL if available (for Render/PostgreSQL), otherwise fallback to SQLite
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///../instance/fts.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
