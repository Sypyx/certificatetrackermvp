# certificate_service/service.py
from repository import CertificateRepository
from datetime import datetime
from models import Certificate

class CertificateService:
    @staticmethod
    def list_certificates(user_id: int, role: str):
        """
        Если role == 'manager' → возвращаем все
        Иначе (user) → только свои
        """
        if role == 'manager':
            return CertificateRepository.get_all()
        return CertificateRepository.get_by_owner(user_id)

    @staticmethod
    def get_certificate(cert_id: int, user_id: int, role: str):
        cert = CertificateRepository.get_by_id(cert_id)
        if not cert:
            return None, 'Not found'
        if role == 'user' and cert.owner_id != user_id:
            return None, 'Access denied'
        return cert, None

    @staticmethod
    def create_certificate(data: dict):
        """
        Ожидаем data: { name, date_start (строка 'YYYY-MM-DD'), date_end, owner_id }
        """
        try:
            ds = datetime.strptime(data['date_start'], '%Y-%m-%d').date()
            de = datetime.strptime(data['date_end'], '%Y-%m-%d').date()
        except Exception:
            raise ValueError("Неверный формат даты. Используйте 'YYYY-MM-DD'")

        if de < ds:
            raise ValueError("Дата окончания должна быть не ранее даты начала")

        return CertificateRepository.create(
            name=data['name'],
            date_start=ds,
            date_end=de,
            owner_id=data['owner_id']
        )

    @staticmethod
    def update_certificate(cert_id: int, data: dict):
        cert = CertificateRepository.get_by_id(cert_id)
        if not cert:
            return None, 'Not found'
        kwargs = {}
        if 'name' in data:
            kwargs['name'] = data['name']
        if 'date_start' in data:
            try:
                kwargs['date_start'] = datetime.strptime(data['date_start'], '%Y-%m-%d').date()
            except:
                raise ValueError("Неверный формат date_start")
        if 'date_end' in data:
            try:
                kwargs['date_end'] = datetime.strptime(data['date_end'], '%Y-%m-%d').date()
            except:
                raise ValueError("Неверный формат date_end")
        if 'owner_id' in data:
            kwargs['owner_id'] = data['owner_id']
        # Проверка логики чистоты дат
        if 'date_start' in kwargs and 'date_end' in kwargs and kwargs['date_end'] < kwargs['date_start']:
            raise ValueError("date_end < date_start")

        updated = CertificateRepository.update(cert, **kwargs)
        return updated, None

    @staticmethod
    def delete_certificate(cert_id: int):
        cert = CertificateRepository.get_by_id(cert_id)
        if not cert:
            return 'Not found'
        CertificateRepository.delete(cert)
        return None

    @staticmethod
    def get_expiring_soon(days: int = 30):
        """Возвращает список сертификатов, у которых осталось ровно `days` дней."""
        return CertificateRepository.get_expiring_in_days(days)

    @staticmethod
    def get_certificate_by_id(cert_id: int):
        """
        Возвращает объект Certificate по его ID или None, если не найден.
        Без проверки прав и JWT. Используется публичный маршрут.
        """
        return Certificate.query.filter_by(id=cert_id).first()