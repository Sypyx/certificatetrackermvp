# user_service/models.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserProfile(db.Model):
    __tablename__ = 'users'
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    role     = db.Column(db.String(20), nullable=False, default='user')
    phone    = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f'<UserProfile {self.id} {self.username}>'
