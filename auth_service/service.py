# auth_service/service.py

from repository import UserRepository
from passlib.hash import bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import datetime, timedelta

class AuthService:
    @staticmethod
    def register_user(username: str, password: str, email: str, role: str = 'user', phone: str = None):
        # Проверка заполненности полей
        if not (username and password and email):
            raise ValueError("username, password и email обязательны")
        # Пробуем создать, передаём phone
        try:
            user = UserRepository.create_user(username, password, email, role, phone)
        except Exception:
            # IntegrityError → уже есть такой username или email
            raise ValueError("Пользователь с таким именем или e-mail уже существует")
        return user

    @staticmethod
    def authenticate(username: str, password: str):
        user = UserRepository.find_by_username(username)
        if not user or not user.check_password(password):
            return None
        return user

    @staticmethod
    def generate_tokens(user):
        additional_claims = {'role': user.role}
        access_token  = create_access_token(identity=user.id, additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=user.id, additional_claims=additional_claims)
        return access_token, refresh_token
