# certificate_service/repository.py
from models import Certificate, db
from sqlalchemy.exc import SQLAlchemyError

class CertificateRepository:
    @staticmethod
    def get_by_id(cert_id: int):
        return Certificate.query.get(cert_id)

    @staticmethod
    def get_all():
        return Certificate.query.all()

    @staticmethod
    def get_by_owner(owner_id: int):
        return Certificate.query.filter_by(owner_id=owner_id).all()

    @staticmethod
    def create(name: str, date_start, date_end, owner_id: int):
        cert = Certificate(name=name, date_start=date_start, date_end=date_end, owner_id=owner_id)
        db.session.add(cert)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise
        return cert

    @staticmethod
    def update(cert: Certificate, **kwargs):
        # kwargs могут содержать name, date_start, date_end, owner_id
        if 'name' in kwargs:
            cert.name = kwargs['name']
        if 'date_start' in kwargs:
            cert.date_start = kwargs['date_start']
        if 'date_end' in kwargs:
            cert.date_end = kwargs['date_end']
        if 'owner_id' in kwargs:
            cert.owner_id = kwargs['owner_id']
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise
        return cert

    @staticmethod
    def delete(cert: Certificate):
        db.session.delete(cert)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def get_expiring_in_days(days: int):
        """
        Возвращает список сертификатов, у которых date_end - today == days
        """
        from datetime import date, timedelta
        target_date = date.today() + timedelta(days=days)
        return Certificate.query.filter(Certificate.date_end == target_date).all()
