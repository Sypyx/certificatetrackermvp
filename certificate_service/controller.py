# certificate_service/controller.py

import io
import pandas as pd
from datetime import datetime, date
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from service import CertificateService
from utils import role_required

cert_bp = Blueprint('cert_bp', __name__, url_prefix='/certificates')


# -------------------------------
# 1) Существующие CRUD-эндпоинты
# -------------------------------

@cert_bp.route('/', methods=['GET'])
@jwt_required()
def list_certificates():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    certs = CertificateService.list_certificates(current_user_id, role)

    result = []
    for c in certs:
        result.append({
            'id': c.id,
            'name': c.name,
            'date_start': c.date_start.strftime('%Y-%m-%d'),
            'date_end': c.date_end.strftime('%Y-%m-%d'),
            'days_left': c.days_left(),
            'owner_id': c.owner_id
        })
    return jsonify({'certificates': result}), 200


@cert_bp.route('/<int:cert_id>', methods=['GET'])
@jwt_required()
def get_certificate(cert_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    cert, error = CertificateService.get_certificate(cert_id, current_user_id, role)
    if error == 'Not found':
        return jsonify({'msg': 'Сертификат не найден'}), 404
    if error == 'Access denied':
        return jsonify({'msg': 'Доступ запрещён'}), 403

    return jsonify({
        'id': cert.id,
        'name': cert.name,
        'date_start': cert.date_start.strftime('%Y-%m-%d'),
        'date_end': cert.date_end.strftime('%Y-%m-%d'),
        'days_left': cert.days_left(),
        'owner_id': cert.owner_id
    }), 200

@cert_bp.route('/public/<int:cert_id>', methods=['GET'])
def get_certificate_public(cert_id):
    cert = CertificateService.get_certificate_by_id(cert_id)
    if not cert:
        return jsonify({'msg': 'Сертификат не найден'}), 404

    return jsonify({
        'id': cert.id,
        'name': cert.name,
        'date_start': cert.date_start.strftime('%Y-%m-%d'),
        'date_end': cert.date_end.strftime('%Y-%m-%d'),
        'days_left': cert.days_left(),
        'owner_id': cert.owner_id
    }), 200

@cert_bp.route('/', methods=['POST'])
@jwt_required()
@role_required('manager')
def create_certificate():
    """
    Ожидает JSON с полями:
      - name
      - date_start (YYYY-MM-DD)
      - date_end (YYYY-MM-DD)
      - owner_id (владелец, в случае менеджера)
    """
    data = request.get_json()
    try:
        cert = CertificateService.create_certificate(data)
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400

    return jsonify({
        'id': cert.id,
        'name': cert.name,
        'date_start': cert.date_start.strftime('%Y-%m-%d'),
        'date_end': cert.date_end.strftime('%Y-%m-%d'),
        'days_left': cert.days_left(),
        'owner_id': cert.owner_id
    }), 201


@cert_bp.route('/<int:cert_id>', methods=['PUT'])
@jwt_required()
@role_required('manager')
def update_certificate(cert_id):
    data = request.get_json()
    try:
        cert, error = CertificateService.update_certificate(cert_id, data)
    except ValueError as e:
        return jsonify({'msg': str(e)}), 400

    if error == 'Not found':
        return jsonify({'msg': 'Сертификат не найден'}), 404

    return jsonify({
        'id': cert.id,
        'name': cert.name,
        'date_start': cert.date_start.strftime('%Y-%m-%d'),
        'date_end': cert.date_end.strftime('%Y-%m-%d'),
        'days_left': cert.days_left(),
        'owner_id': cert.owner_id
    }), 200


@cert_bp.route('/<int:cert_id>', methods=['DELETE'])
@jwt_required()
@role_required('manager')
def delete_certificate(cert_id):
    error = CertificateService.delete_certificate(cert_id)
    if error == 'Not found':
        return jsonify({'msg': 'Сертификат не найден'}), 404

    return jsonify({'msg': 'Сертификат удалён'}), 200


@cert_bp.route('/expiring/<int:days>', methods=['GET'])
def get_expiring(days):
    expiring_certs = CertificateService.get_expiring_soon(days)

    result = []
    for c in expiring_certs:
        result.append({
            'id': c.id,
            'name': c.name,
            'date_start': c.date_start.strftime('%Y-%m-%d'),
            'date_end': c.date_end.strftime('%Y-%m-%d'),
            'days_left': c.days_left(),
            'owner_id': c.owner_id
        })

    return jsonify({'certificates': result}), 200

@cert_bp.route('/export', methods=['GET'])
@jwt_required()
def export_certificates_excel():
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role', 'user')

    # Получаем список моделей через сервис:
    certs = CertificateService.list_certificates(current_user_id, role)

    # Формируем словари только с нужными полями
    rows = []
    for c in certs:
        rows.append({
            "Проверка": c.name,
            "Начало действия": c.date_start.strftime("%Y-%m-%d"),
            "Конец действия": c.date_end.strftime("%Y-%m-%d")
        })

    # Создаём DataFrame с тремя колонками
    df = pd.DataFrame(rows, columns=["Проверка", "Начало действия", "Конец действия"])

    # Записываем DataFrame в байтовый буфер
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Certificates')
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="certificates_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@cert_bp.route('/import', methods=['POST'])
@jwt_required()
@role_required('manager')
def import_certificates_from_excel():
    if 'file' not in request.files:
        return jsonify({"error": "В запросе должен быть файл с ключом 'file'"}), 400

    # Получаем user_id из тела формы (FormData)
    owner_id = None
    if 'user_id' in request.form:
        try:
            owner_id = int(request.form['user_id'])
        except ValueError:
            return jsonify({"error": "user_id должен быть целым числом"}), 400
    else:
        # Если user_id не передан, берём текущего (хотя обычно менеджер импортирует для выбранного)
        owner_id = get_jwt_identity()

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Имя файла пустое"}), 400

    try:
        df = pd.read_excel(file, engine='openpyxl')
    except Exception as e:
        return jsonify({"error": f"Не удалось прочитать Excel: {str(e)}"}), 400

    required_columns = {"Проверка", "Начало действия", "Конец действия"}
    missing = required_columns - set(df.columns)
    if missing:
        return jsonify({"error": f"Отсутствуют колонки: {', '.join(missing)}"}), 400

    created = []
    errors = []

    for idx, row in df.iterrows():
        row_number = idx + 2  # строка 1 — шапка
        name = str(row["Проверка"]).strip()
        date_start_raw = row["Начало действия"]
        date_end_raw = row["Конец действия"]

        # Проверяем обязательные поля
        if not name or pd.isna(date_start_raw) or pd.isna(date_end_raw):
            errors.append(f"Строка {row_number}: одно из полей пустое")
            continue

        # Парсим дату начала
        try:
            if isinstance(date_start_raw, (pd.Timestamp, datetime)):
                date_start = date_start_raw.date()
            else:
                date_start = datetime.fromisoformat(str(date_start_raw)).date()
        except Exception as e:
            errors.append(f"Строка {row_number}: неверный формат 'Начало действия' ({e})")
            continue

        # Парсим дату окончания
        try:
            if isinstance(date_end_raw, (pd.Timestamp, datetime)):
                date_end = date_end_raw.date()
            else:
                date_end = datetime.fromisoformat(str(date_end_raw)).date()
        except Exception as e:
            errors.append(f"Строка {row_number}: неверный формат 'Конец действия' ({e})")
            continue

        # Данные для создания
        data = {
            "name": name,
            "date_start": date_start.strftime("%Y-%m-%d"),
            "date_end": date_end.strftime("%Y-%m-%d"),
            "owner_id": owner_id
        }

        try:
            cert = CertificateService.create_certificate(data)
            created.append({"row": row_number, "name": cert.name})
        except ValueError as e:
            errors.append(f"Строка {row_number}: {str(e)}")
            continue

    return jsonify({
        "created": created,
        "errors": errors
    }), 200
