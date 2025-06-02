# notification_service/tasks.py

from celery_app import celery
from celery import shared_task
from config import Config
import requests
from email_sender import EmailSender
from datetime import datetime, date
from sms_sender import send_sms_via_smsru

# ----------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ «ПУБЛИЧНЫЕ» ФУНКЦИИ
# ----------------------------------------

def _get_certificate_public(cert_id: int):
    """
    Публичный GET /certificates/public/<cert_id>
    без JWT. Возвращает JSON-сертификат или None.
    """
    try:
        url = f"{Config.CERT_SERVICE_URL}/certificates/public/{cert_id}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()  # словарь: {'id':..., 'name':..., 'date_start':...,'date_end':...,'days_left':...,'owner_id':...}
    except Exception as e:
        print(f"[notification_service] Не удалось получить public-сертификат {cert_id}: {e}")
        return None

def _get_user_public(user_id: int):
    """
    Публичный GET /users/public/<user_id>
    без JWT. Возвращает JSON-пользователь с полями {id, username, email, phone} или None.
    """
    try:
        url = f"{Config.USER_SERVICE_URL}/users/public/{user_id}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        return resp.json()  # словарь: {'id':..., 'username':..., 'email':..., 'phone': ...}
    except Exception as e:
        print(f"[notification_service] Не удалось получить public-пользователя {user_id}: {e}")
        return None

# ----------------------------------------
#   1) ЕДИНИЧНЫЕ УВЕДОМЛЕНИЯ (e-mail и SMS)
# ----------------------------------------

@shared_task(name='tasks.send_single_notification')
def send_single_notification(certificate_id: int):
    """
    Единичное уведомление по конкретному сертификату (e-mail).
    Использует публичный эндпоинт /certificates/public/<id> и /users/public/<owner_id>.
    """
    # 1. «Публично» получаем сертификат
    cert_data = _get_certificate_public(certificate_id)
    if not cert_data:
        print(f"[notification_service] send_single_notification: сертификат {certificate_id} не найден")
        return {"status": "ERROR", "status_text": f"cert not found ({certificate_id})"}

    owner_id = cert_data.get('owner_id')
    cert_name = cert_data.get('name')
    date_end = cert_data.get('date_end')  # строка 'YYYY-MM-DD'

    # 2. «Публично» получаем пользователя
    user_data = _get_user_public(owner_id)
    if not user_data:
        print(f"[notification_service] send_single_notification: пользователь {owner_id} не найден")
        return {"status": "ERROR", "status_text": f"user not found ({owner_id})"}

    email = user_data.get('email')
    username = user_data.get('username')

    if not email:
        print(f"[notification_service] send_single_notification: у пользователя {owner_id} нет e-mail")
        return {"status": "ERROR", "status_text": "no email"}

    # 3. Считаем days_left
    try:
        days_left = (datetime.fromisoformat(date_end).date() - date.today()).days
    except Exception:
        days_left = None

    # 4. Формируем тему и тело письма
    subject = f"Напоминание: сертификат '{cert_name}' истекает"
    if days_left is not None:
        subject += f" через {days_left} дней"
    body = (
        f"Здравствуйте, {username}!\n\n"
        f"Сертификат «{cert_name}» (ID {certificate_id}) "
        f"заканчивается {date_end}"
        f"{f' (осталось {days_left} дней)' if days_left is not None else ''}.\n"
        "Пожалуйста, продлите сертификат заранее.\n\n"
        "С уважением,\n"
        "Служба управления сертификатами"
    )

    # 5. Пытаемся отправить письмо через Gmail SMTP
    try:
        EmailSender.send_email(to_email=email, subject=subject, body=body)
        print(f"[notification_service] send_single_notification: e-mail отправлен {email}")
        return {"status": "OK", "status_text": f"email sent to {email}"}
    except Exception as e:
        print(f"[notification_service] send_single_notification: ошибка при отправке e-mail {email}: {e}")
        return {"status": "ERROR", "status_text": str(e)}

@shared_task(name='tasks.send_sms_notification_for_cert')
def send_sms_notification_for_cert(cert_id: int):
    """
    Единичное SMS-уведомление по конкретному сертификату.
    Использует публичные эндпоинты /certificates/public/... и /users/public/...
    """
    # 1) «Публично» получаем сертификат
    cert_data = _get_certificate_public(cert_id)
    if not cert_data:
        print(f"[notification_service] send_sms_notification_for_cert: сертификат {cert_id} не найден")
        return {"status": "ERROR", "status_text": f"cert not found ({cert_id})"}

    owner_id = cert_data.get('owner_id')
    cert_name = cert_data.get('name')
    date_end = cert_data.get('date_end')  # строка 'YYYY-MM-DD'

    # 2) «Публично» получаем пользователя
    user_data = _get_user_public(owner_id)
    if not user_data:
        print(f"[notification_service] send_sms_notification_for_cert: пользователь {owner_id} не найден")
        return {"status": "ERROR", "status_text": f"user not found ({owner_id})"}

    phone = user_data.get('phone')
    username = user_data.get('username')

    if not phone:
        print(f"[notification_service] send_sms_notification_for_cert: у пользователя {owner_id} нет телефона")
        return {"status": "ERROR", "status_text": "no phone"}

    # 3) Считаем days_left
    try:
        days_left = (datetime.fromisoformat(date_end).date() - date.today()).days
    except Exception:
        days_left = None

    # 4) Формируем текст SMS
    message = (
        f"Здравствуйте, {username}! Сертификат «{cert_name}» "
        f"истекает"
        f"{f' через {days_left} дней' if days_left is not None else ''} ({date_end})."
    )

    # 5) Отправляем через SMS-RU
    try:
        sms_result = send_sms_via_smsru(phone, message)
        print(f"[notification_service] send_sms_notification_for_cert: sms_ru result для cert {cert_id}: {sms_result}")
        return sms_result
    except Exception as e:
        print(f"[notification_service] send_sms_notification_for_cert: ошибка при отправке SMS {phone}: {e}")
        return {"status": "ERROR", "status_text": str(e)}

# ----------------------------------------
# 2) АВТОМАТИЧЕСКИЕ «ЕЖЕДНЕВНЫЕ» РАССЫЛКИ
# ----------------------------------------

@celery.task(name='tasks.send_expiry_notifications_30')
def send_expiry_notifications_30(bearer_token: str = None):
    """
    Автоматическая рассылка «за 30 дней до окончания».
    Использует публичный GET /certificates/expiring/30 и /users/public/<owner_id>.
    """
    days = 30
    try:
        url = f"{Config.CERT_SERVICE_URL}/certificates/expiring/{days}"
        resp = requests.get(url, timeout=5)  # публичный
        resp.raise_for_status()
        certs = resp.json().get('certificates', [])
    except Exception as e:
        print(f"[notification_service] Не удалось получить expiring/{days}: {e}")
        certs = []

    if not certs:
        print(f"[notification_service] Нет сертификатов, expiring {days} дней")
        return

    notified = set()
    for cert in certs:
        owner_id = cert.get('owner_id')
        cert_name = cert.get('name')
        date_end = cert.get('date_end')

        if owner_id in notified:
            continue

        # --- Отправка e-mail ---
        user_data = _get_user_public(owner_id)
        if user_data and user_data.get('email'):
            email = user_data['email']
            subject = f"Напоминание: сертификат '{cert_name}' истекает через {days} дней"
            body = (
                f"Здравствуйте, {user_data['username']}!\n\n"
                f"Сертификат «{cert_name}» заканчивается {date_end} (через {days} дней).\n"
                "Пожалуйста, продлите сертификат заранее.\n\n"
                "С уважением,\n"
                "Служба управления сертификатами"
            )
            try:
                EmailSender.send_email(to_email=email, subject=subject, body=body)
                print(f"[notification_service] 30-дневное e-mail напоминание отправлено: {email}")
            except Exception as e:
                print(f"[notification_service] Ошибка 30-дневного e-mail для {email}: {e}")
        else:
            print(f"[notification_service] У пользователя {owner_id} нет e-mail, пропускаем.")

        # --- Отправка SMS ---
        if user_data and user_data.get('phone'):
            phone = user_data['phone']
            username = user_data['username']
            try:
                days_left = (datetime.fromisoformat(date_end).date() - date.today()).days
            except Exception:
                days_left = None
            sms_message = (
                f"Здравствуйте, {username}! Сертификат «{cert_name}» "
                f"истекает через {days} дней ({date_end})."
            )
            try:
                sms_result = send_sms_via_smsru(phone, sms_message)
                print(f"[notification_service] 30-дневное SMS-напоминание отправлено: {sms_result}")
            except Exception as e:
                print(f"[notification_service] Ошибка 30-дневного SMS для {owner_id}: {e}")
        else:
            print(f"[notification_service] У пользователя {owner_id} нет телефона, пропускаем SMS.")

        notified.add(owner_id)

@celery.task(name='tasks.send_expiry_notifications_10')
def send_expiry_notifications_10(bearer_token: str = None):
    """
    Автоматическая рассылка «за 10 дней до окончания».
    """
    days = 10
    try:
        url = f"{Config.CERT_SERVICE_URL}/certificates/expiring/{days}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        certs = resp.json().get('certificates', [])
    except Exception as e:
        print(f"[notification_service] Не удалось получить expiring/{days}: {e}")
        certs = []

    if not certs:
        print(f"[notification_service] Нет сертификатов, expiring {days} дней")
        return

    notified = set()
    for cert in certs:
        owner_id = cert.get('owner_id')
        cert_name = cert.get('name')
        date_end = cert.get('date_end')

        if owner_id in notified:
            continue

        # --- E-mail ---
        user_data = _get_user_public(owner_id)
        if user_data and user_data.get('email'):
            email = user_data['email']
            subject = f"Напоминание: сертификат '{cert_name}' истекает через {days} дней"
            body = (
                f"Здравствуйте, {user_data['username']}!\n\n"
                f"Сертификат «{cert_name}» заканчивается {date_end} (через {days} дней).\n"
                "Пожалуйста, продлите сертификат заранее.\n\n"
                "С уважением,\n"
                "Служба управления сертификатами"
            )
            try:
                EmailSender.send_email(to_email=email, subject=subject, body=body)
                print(f"[notification_service] 10-дневное e-mail напоминание отправлено: {email}")
            except Exception as e:
                print(f"[notification_service] Ошибка 10-дневного e-mail для {email}: {e}")
        else:
            print(f"[notification_service] У пользователя {owner_id} нет e-mail, пропускаем.")

        # --- SMS ---
        if user_data and user_data.get('phone'):
            phone = user_data['phone']
            username = user_data['username']
            try:
                days_left = (datetime.fromisoformat(date_end).date() - date.today()).days
            except Exception:
                days_left = None
            sms_message = (
                f"Здравствуйте, {username}! Сертификат «{cert_name}» "
                f"истекает через {days} дней ({date_end})."
            )
            try:
                sms_result = send_sms_via_smsru(phone, sms_message)
                print(f"[notification_service] 10-дневное SMS-напоминание отправлено: {sms_result}")
            except Exception as e:
                print(f"[notification_service] Ошибка 10-дневного SMS для {owner_id}: {e}")
        else:
            print(f"[notification_service] У пользователя {owner_id} нет телефона, пропускаем SMS.")

        notified.add(owner_id)
