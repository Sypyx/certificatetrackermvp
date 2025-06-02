# user_service/app.py

import threading
import time
import json
import redis

from flask import Flask
from flask_cors import CORS
from config import Config
from models import db, UserProfile
from controller import user_bp  # наш Blueprint из controller.py
from flask_jwt_extended import JWTManager


def create_app():
    app = Flask(__name__)
    CORS(app)  # здесь можно ограничить фронтэндом, но оставим *
    app.config.from_object(Config)
    db.init_app(app)
    jwt = JWTManager(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(user_bp)

    with app.app_context():
        start_redis_listener(app)

    return app


def start_redis_listener(app):
    """
    Запускает фоновый поток, который подписывается на Redis-канал 'user_events'
    и обрабатывает события create/update.
    """

    def _listener():
        r = redis.from_url(Config.REDIS_URL)
        pubsub = r.pubsub()
        pubsub.subscribe('user_events')

        for message in pubsub.listen():
            if message['type'] != 'message':
                continue
            try:
                payload = json.loads(message['data'])
                handle_user_event(app, payload)
            except Exception as e:
                print(f"[user_service] Ошибка при чтении события: {e}")

    thread = threading.Thread(target=_listener, daemon=True)
    thread.start()


def handle_user_event(app, payload):
    """
    Обрабатываем JSON-событие из auth_service:
      payload = { 'action': 'create'|'update', 'user': {id, username, email, role, phone} }
    """
    action = payload.get('action')
    user_data = payload.get('user', {})
    if not user_data or 'id' not in user_data:
        return

    user_id = user_data['id']
    username = user_data['username']
    email = user_data['email']
    role = user_data['role']
    phone = user_data.get('phone')  # вот оно

    with app.app_context():
        existing = UserProfile.query.get(user_id)
        if action == 'create':
            if existing:
                # обновляем поля, включая phone
                existing.username = username
                existing.email = email
                existing.role = role
                existing.phone = phone
            else:
                new_profile = UserProfile(
                    id=user_id,
                    username=username,
                    email=email,
                    role=role,
                    phone=phone  # записываем phone
                )
                db.session.add(new_profile)
            db.session.commit()

        elif action == 'update':
            if existing:
                existing.username = username
                existing.email = email
                existing.role = role
                existing.phone = phone  # обновляем phone
                db.session.commit()
            else:
                # Если update пришло раньше create (маловероятно), создаём
                new_profile = UserProfile(
                    id=user_id,
                    username=username,
                    email=email,
                    role=role,
                    phone=phone
                )
                db.session.add(new_profile)
                db.session.commit()
        # (при необходимости можно обрабатывать action=='delete')


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5002, debug=True)
