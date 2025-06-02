# auth_service/controller.py

from flask import Blueprint, request, jsonify
from models import db, User
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt
)
import redis
import json
from config import Config
from passlib.hash import bcrypt
from service import AuthService

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')

# Инициализируем Redis Pub/Sub-клиент
redis_client = redis.from_url(Config.REDIS_URL)

@auth_bp.route('/register', methods=['POST'])
@jwt_required(optional=True)
def register():
    """
    Если role='manager' в теле, то JWT из заголовка должен быть от manager.
    Если role='user', JWT не нужен (optional=True).
    Поле 'phone' теперь поддерживается.
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    email    = data.get('email', '').strip()
    password = data.get('password', '').strip()
    role     = data.get('role', 'user').strip()
    phone    = data.get('phone', '').strip()

    # Проверяем обязательные поля
    if not username or not email or not password or not phone:
        return jsonify({'msg': 'username, email, password и phone обязательны'}), 400

    # Если хотят зарегистрировать роль manager — проверяем JWT
    if role == 'manager':
        jwt_data = get_jwt()
        if not jwt_data or jwt_data.get('role') != 'manager':
            return jsonify({'msg': 'Только existing manager может создавать менеджеров'}), 403

    # Проверка уникальности логина/email
    if User.query.filter_by(username=username).first():
        return jsonify({'msg': 'username занят'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'msg': 'email занят'}), 409

    # Создаём нового пользователя (передаём phone)
    try:
        user = AuthService.register_user(username, password, email, role, phone)
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400

    # Публикуем событие «create» (с учётом phone)
    payload = {
        'action': 'create',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'phone': user.phone
        }
    }
    redis_client.publish('user_events', json.dumps(payload))

    # Возвращаем новый профиль (без пароля) и JWT
    access = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
    refresh = create_refresh_token(identity=user.id)
    return jsonify({
        'access_token': access,
        'refresh_token': refresh,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'phone': user.phone
        }
    }), 201


@auth_bp.route('/update/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """
    Обновляем email, role и phone.
    JWT не проверяет роль здесь — если нужно, добавьте проверку get_jwt()['role'].
    """
    data = request.get_json()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'Пользователь не найден'}), 404

    # Обновляем поля, если они пришли
    user.email = data.get('email', user.email).strip()
    user.role  = data.get('role', user.role).strip()
    if 'phone' in data:
        user.phone = data.get('phone', '').strip()

    db.session.commit()

    # Публикуем событие «update», включая phone
    payload = {
        'action': 'update',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'phone': user.phone
        }
    }
    redis_client.publish('user_events', json.dumps(payload))

    return jsonify({
        'msg': 'Пользователь обновлён',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'phone': user.phone
        }
    }), 200


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    При логине возвращаем в ответе phone.
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'msg': 'username и password обязательны'}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.verify(password, user.password):
        return jsonify({'msg': 'Неправильный username или password'}), 401

    access = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role}
    )
    refresh = create_refresh_token(identity=user.id)
    return jsonify({
        'access_token': access,
        'refresh_token': refresh,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'phone': user.phone
        }
    }), 200
