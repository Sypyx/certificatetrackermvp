# auth_service/config.py

import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('AUTH_DATABASE_URI', 'sqlite:///auth.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'some_default_secret')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

    # Дефолтный «вшитый» менеджер
    DEFAULT_MANAGER_USERNAME = os.getenv('DEFAULT_MANAGER_USERNAME', 'admin')
    DEFAULT_MANAGER_PASSWORD = os.getenv('DEFAULT_MANAGER_PASSWORD', 'AdminPass123')
    DEFAULT_MANAGER_EMAIL    = os.getenv('DEFAULT_MANAGER_EMAIL', 'admin@example.com')
    DEFAULT_MANAGER_ROLE     = 'manager'
