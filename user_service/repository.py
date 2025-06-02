# user_service/repository.py
from models import UserProfile, db
from sqlalchemy.exc import IntegrityError

class UserProfileRepository:
    @staticmethod
    def get_by_id(user_id: int) -> UserProfile:
        return UserProfile.query.get(user_id)

    @staticmethod
    def get_all():
        return UserProfile.query.all()

    @staticmethod
    def create(username: str, email: str, role: str = 'user') -> UserProfile:
        user = UserProfile(username=username, email=email, role=role)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise
        return user

    @staticmethod
    def update(user_id: int, **kwargs) -> UserProfile:
        user = UserProfile.query.get_or_404(user_id)
        if 'username' in kwargs:
            user.username = kwargs['username']
        if 'email' in kwargs:
            user.email = kwargs['email']
        if 'role' in kwargs:
            user.role = kwargs['role']
        db.session.commit()
        return user

    @staticmethod
    def delete(user_id: int):
        user = UserProfile.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
