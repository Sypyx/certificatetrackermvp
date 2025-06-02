# notification_service/sms_sender.py

import os
import requests

SMS_RU_API_URL = "https://sms.ru/sms/send"

def send_sms_via_smsru(phone: str, message: str) -> dict:
    """
    Отправляет SMS через API sms.ru.
    Возвращает словарь с ответом от сервиса (json).
    """
    api_id = os.getenv('SMS_RU_API_KEY')
    if not api_id:
        raise ValueError("Не задан SMS_RU_API_KEY в окружении")

    payload = {
        'api_id': api_id,
        'to':     phone,
        'msg':    message,
        'json':   1
    }
    try:
        resp = requests.post(SMS_RU_API_URL, data=payload, timeout=10)
        return resp.json()  # Словарь вида {'status': 'OK', 'sms': {...}} или {'status': 'ERROR', 'status_code': ..., 'status_text': ...}
    except Exception as e:
        # Можно залогировать ошибки
        return {"status": "ERROR", "status_text": str(e)}
