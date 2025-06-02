# certificate_service/config.py

import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('CERT_DATABASE_URI', 'sqlite:///cert.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'some_default_secret')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')