# certificate_service/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Certificate(db.Model):
    __tablename__ = 'certificates'
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(200), nullable=False)
    date_start = db.Column(db.Date, nullable=False)
    date_end   = db.Column(db.Date, nullable=False)
    owner_id   = db.Column(db.Integer, nullable=False)  # Внешний ключ необязательно здесь; просто сохраняем id

    def days_left(self):
        today = date.today()
        if today > self.date_end:
            return 0
        return (self.date_end - today).days
