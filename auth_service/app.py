# auth_service/app.py

from flask import Flask
from flask_cors import CORS
from config import Config
from models import db, User  # модель User (см. ниже)
from controller import auth_bp
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(Config)
    db.init_app(app)
    jwt = JWTManager(app)

    # 1) Создать таблицы и дефолтного менеджера
    with app.app_context():
        db.create_all()
        ensure_default_manager()

    # 2) Зарегистрировать blueprint с маршрутами /auth/*
    app.register_blueprint(auth_bp)
    return app

def ensure_default_manager():
    """
    Проверяет, есть ли в базе хотя бы один пользователь с role='manager'.
    Если нет — создаёт «вшитого» по значениям из Config.
    """
    from passlib.hash import bcrypt

    manager = User.query.filter_by(role=Config.DEFAULT_MANAGER_ROLE).first()
    if manager:
        return  # Уже есть менеджер, ничего не делаем

    # Если менеджера нет, создаём «по умолчанию»
    default = User(
        username=Config.DEFAULT_MANAGER_USERNAME,
        email=Config.DEFAULT_MANAGER_EMAIL,
        role=Config.DEFAULT_MANAGER_ROLE
    )
    default.password = bcrypt.hash(Config.DEFAULT_MANAGER_PASSWORD)
    db.session.add(default)
    db.session.commit()
    print(f"[auth_service] Создан дефолтный менеджер: {default.username}")

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)
