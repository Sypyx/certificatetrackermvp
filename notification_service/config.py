# notification_service/config.py

import os

class Config:
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

    AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://auth_service:5001')
    CERT_SERVICE_URL = os.getenv('CERT_SERVICE_URL', 'http://certificate_service:5003')
    USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user_service:5002')
    SMS_RU_API_KEY = os.environ.get('SMS_RU_API_KEY', None)

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USE_TLS = True
    SMTP_USER = os.getenv('SMTP_USER', 'your_email@gmail.com')
    SMTP_PASS = os.getenv('SMTP_PASS', 'your_app_password_or_password')
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'your_email@gmail.com')
