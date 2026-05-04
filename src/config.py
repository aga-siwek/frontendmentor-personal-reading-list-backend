import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    # Render provides URL with 'postgres://' prefix, SQLAlchemy requires 'postgresql://'
    SQLALCHEMY_DATABASE_URI = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev_jwt_secret_key')
    JWT_TOKEN_LOCATION = ['headers']
