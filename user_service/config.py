# user_service/config.py

import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('USER_DATABASE_URI', 'sqlite:///user.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
