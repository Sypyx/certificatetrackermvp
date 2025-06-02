# notification_service/app.py

import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from tasks import send_single_notification, send_sms_notification_for_cert

# Настраиваем базовый логгер
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.from_object(Config)

# Разрешаем запросы с фронтенда (http://localhost:8080), в том числе заголовок 'Authorization'
CORS(
    app,
    resources={r"/notify/*": {"origins": "http://localhost:8080"}},
    allow_headers=["Authorization", "Content-Type"],
    methods=["POST", "OPTIONS"]
)

@app.route('/notify/certificate/<int:cert_id>', methods=['OPTIONS', 'POST'])
def notify_certificate(cert_id):
    """
    Единичная отправка e-mail (через Celery). JWT уже не проверяется здесь,
    потому что /certificates/public/<id> публичный и не требует токена.
    """
    # Если это preflight-запрос (OPTIONS), вернём 200 и нужные CORS-заголовки
    if request.method == 'OPTIONS':
        return jsonify({'msg': 'OK'}), 200

    # Получаем body или header, но нам не нужен Authorization: работаем публично
    # (если вы ещё ранее передавали JWT сюда, можете просто игнорировать его или валидировать,
    # но в «публичном» варианте мы не хотим падать из-за отсутсвия токена).
    #
    # Запускаем Celery-задачу «send_single_notification», передаём только cert_id.
    # Внутри таска он делает public GET /certificates/public/{cert_id}.
    send_single_notification.delay(cert_id)
    return jsonify({'msg': f'Email-уведомление для сертификата {cert_id} поставлено в очередь.'}), 200

@app.route('/notify/sms/<int:cert_id>', methods=['OPTIONS', 'POST'])
def notify_sms(cert_id):
    """
    Единичная отправка SMS (через Celery). JWT не проверяется, т. к.
    в таске мы обращаемся публично к /certificates/public/ и /users/public/.
    """
    if request.method == 'OPTIONS':
        return jsonify({'msg': 'OK'}), 200

    # Никакой JWT/Authorization из фронтенда нам здесь по сути не нужен.
    # Запускаем Celery-задачу, передаём только cert_id.
    send_sms_notification_for_cert.delay(cert_id)
    return jsonify({'msg': f'SMS-уведомление для сертификата {cert_id} поставлено в очередь.'}), 200

if __name__ == '__main__':
    # В режиме debug=True можно видеть traceback в консоли Docker
    app.run(host='0.0.0.0', port=5004, debug=True)
