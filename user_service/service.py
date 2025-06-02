# user_service/service.py
from repository import UserProfileRepository

class UserService:
    @staticmethod
    def get_user(user_id: int):
        return UserProfileRepository.get_by_id(user_id)

    @staticmethod
    def list_users():
        return UserProfileRepository.get_all()

    @staticmethod
    def create_user(username: str, email: str, role: str = 'user'):
        return UserProfileRepository.create(username, email, role)

    @staticmethod
    def update_user(user_id: int, **kwargs):
        return UserProfileRepository.update(user_id, **kwargs)

    @staticmethod
    def delete_user(user_id: int):
        return UserProfileRepository.delete(user_id)
