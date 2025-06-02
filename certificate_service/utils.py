# certificate_service/utils.py
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from functools import wraps
from flask import jsonify

def role_required(required_role):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()  # убеждаемся, что токен есть и валиден
            claims = get_jwt()
            user_role = claims.get('role', '')
            if user_role != required_role:
                return jsonify({'msg': 'Недостаточно прав (нужна роль ' + required_role + ')'}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper
