# notification_service/email_sender.py

import smtplib
from email.mime.text import MIMEText
from config import Config

class EmailSender:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str):
        """
        Отправляет простое текстовое письмо через Gmail SMTP.
        """
        smtp_host = Config.SMTP_HOST
        smtp_port = Config.SMTP_PORT
        user = Config.SMTP_USER
        password = Config.SMTP_PASS

        # Собираем MIME-письмо
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_email

        try:
            # Подключаемся к smtp.gmail.com:587
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
                smtp.ehlo()            # запускаем handshake
                smtp.starttls()        # переключаемся на защищённое соединение
                smtp.ehlo()            # повторно hand­shake поверх TLS
                smtp.login(user, password)
                smtp.send_message(msg)
                smtp.quit()
        except Exception as e:
            # В случае ошибки бросаем дальше, чтобы таск понял, что не удалось отправить
            raise RuntimeError(f"Не удалось отправить e-mail: {e}")
