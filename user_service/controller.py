# user_service/controller.py

from flask import Blueprint, request, jsonify
from models import db, UserProfile
from service import UserService

user_bp = Blueprint('user_bp', __name__, url_prefix='/users')


@user_bp.route('/', methods=['GET'])
def list_users():
    """
    Возвращает всех пользователей (UserProfile), включая поле phone.
    """
    users = UserProfile.query.all()
    result = []
    for u in users:
        result.append({
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'phone': u.phone,           # добавляем phone в ответ
            # следующие два поля (next_certificate, days_left)
            # можно заполнять здесь, если сервис certificates знает о ближайшем:
            # 'next_certificate': u.next_certificate,
            # 'days_left': u.days_left
        })
    return jsonify({'users': result}), 200


@user_bp.route('/<int:user_id>', methods=['GET'])
# @jwt_required()  # этот путь открыт, либо защищайте при необходимости
def get_user(user_id):
    """
    Возвращает одного пользователя по id, включая phone.
    """
    user = UserService.get_user(user_id)
    if not user:
        return jsonify({'msg': 'Пользователь не найден'}), 404
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'phone': user.phone             # возвращаем phone
    }), 200


@user_bp.route('/', methods=['POST'])
def create_user():
    """
    Создание пользователя вручную (не через событие).
    Рекомендуется не использовать этот маршрут,
    так как user_profile должен поступать из auth_service.
    Но оставим реализацию с phone для полноты.
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    email    = data.get('email', '').strip()
    role     = data.get('role', 'user').strip()
    phone    = data.get('phone', None)
    if phone:
        phone = phone.strip()

    if not username or not email:
        return jsonify({'msg': 'username и email обязательны'}), 400

    if UserProfile.query.filter_by(username=username).first():
        return jsonify({'msg': 'username занят'}), 409
    if UserProfile.query.filter_by(email=email).first():
        return jsonify({'msg': 'email занят'}), 409

    new_profile = UserProfile(
        username=username,
        email=email,
        role=role,
        phone=phone           # сохраняем phone
    )
    db.session.add(new_profile)
    db.session.commit()

    return jsonify({
        'id': new_profile.id,
        'username': new_profile.username,
        'email': new_profile.email,
        'role': new_profile.role,
        'phone': new_profile.phone      # возвращаем phone
    }), 201


@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Обновление пользователя (в том числе phone).
    JWT-/permission-проверку добавьте, если нужно.
    """
    data = request.get_json()
    u = UserProfile.query.get(user_id)
    if not u:
        return jsonify({'msg': 'Пользователь не найден'}), 404

    u.username = data.get('username', u.username)
    u.email    = data.get('email', u.email)
    u.role     = data.get('role', u.role)
    if 'phone' in data:
        # Если передали phone (даже пустую строку), сохраняем
        u.phone = data.get('phone').strip() if data.get('phone') else None

    db.session.commit()
    return jsonify({
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'phone': u.phone                # возвращаем phone
    }), 200


@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Удаление пользователя (вручную).
    """
    u = UserProfile.query.get(user_id)
    if not u:
        return jsonify({'msg': 'Пользователь не найден'}), 404
    db.session.delete(u)
    db.session.commit()
    return jsonify({'msg': 'Пользователь удалён'}), 200


@user_bp.route('/public/<int:user_id>', methods=['GET'])
def get_user_public(user_id):
    """
    Упрощённый публичный метод (например,
    чтобы notification_service мог получить phone/username без аутентификации).
    """
    u = UserProfile.query.get(user_id)
    if not u:
        return jsonify({'msg': 'Пользователь не найден'}), 404
    return jsonify({
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'role': u.role,
        'phone': u.phone          # возвращаем phone
    }), 200
