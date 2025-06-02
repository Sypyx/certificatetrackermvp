# auth_service/repository.py

from models import User, db
from sqlalchemy.exc import IntegrityError

class UserRepository:
    @staticmethod
    def create_user(username: str, password: str, email: str, role: str = 'user', phone: str = None) -> User:
        user = User(username=username, email=email, role=role, phone=phone)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return user

    @staticmethod
    def find_by_username(username: str):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def find_by_id(user_id: int):
        return User.query.get(user_id)

    @staticmethod
    def find_by_email(email: str):
        return User.query.filter_by(email=email).first()
