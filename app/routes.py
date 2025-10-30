from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from flask_mail import Message
from app import db, mail, jwt
from app.models import User, Port, Report
from app.schemas import PortSchema, ReportSchema, LoginSchema
import pdfplumber
import re
import threading
import tempfile
import os

api_bp = Blueprint('api', __name__)
port_schema = PortSchema()
ports_schema = PortSchema(many=True)
report_schema = ReportSchema()
login_schema = LoginSchema()

# Функция для уведомлений
def send_notification_async(port, message):
    def send():
        if port.subscribers:
            emails = port.subscribers.split(',')
            msg = Message('EcoPorts Alert', sender='noreply@ecoports.com', recipients=emails)
            msg.body = message
            mail.send(msg)
    threading.Thread(target=send).start()

# Логин
@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    errors = login_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token, role=user.role), 200
    return jsonify({'error': 'Invalid credentials'}), 401

# Порты (GET с фильтрами)
@api_bp.route('/ports', methods=['GET'])
def get_ports():
    query = Port.query
    sort_by = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    if sort_by in ['name', 'air_quality', 'water_quality', 'co2_emissions', 'incidents']:
        column = getattr(Port, sort_by)
        query = query.order_by(column.desc() if order == 'desc' else column.asc())
    elif sort_by == 'green_score':
        ports_list = query.all()
        ports_list.sort(key=lambda p: p.green_score, reverse=(order == 'desc'))
        query = ports_list
    
    if isinstance(query, list):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = query[start:end]
        total = len(query)
        pages = (total + per_page - 1) // per_page
        current_page = page
    else:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        ports = query.paginate(page=page, per_page=per_page, error_out=False)
        paginated_items = ports.items
        total = ports.total
        pages = ports.pages
        current_page = ports.page
    
    min_score = request.args.get('min_score', type=float)
    if min_score is not None:
        paginated_items = [p for p in paginated_items if p.green_score >= min_score]
    
    return jsonify({
        'ports': ports_schema.dump(paginated_items),
        'total': total,
        'pages': pages,
        'current_page': current_page
    })

# Конкретный порт
@api_bp.route('/ports/<int:port_id>', methods=['GET'])
def get_port(port_id):
    port = Port.query.get_or_404(port_id)
    return jsonify(port_schema.dump(port))

# Статистика портов
@api_bp.route('/ports/stats', methods=['GET'])
def get_ports_stats():
    ports = Port.query.all()
    if not ports:
        return jsonify({
            'total_ports': 0,
            'avg_green_score': 0,
            'top_polluted': [],
            'air_quality_trend': [],
            'water_quality_trend': [],
            'co2_trend': [],
            'incidents_trend': []
        })
    stats = {
        'total_ports': len(ports),
        'avg_green_score': round(sum(p.green_score for p in ports) / len(ports), 2),
        'top_polluted': [{'name': p.name, 'score': p.green_score} for p in sorted(ports, key=lambda x: x.green_score)[:5]],
        'air_quality_trend': [p.air_quality for p in ports],
        'water_quality_trend': [p.water_quality for p in ports],
        'co2_trend': [p.co2_emissions for p in ports],
        'incidents_trend': [p.incidents for p in ports]
    }
    return jsonify(stats)

# CRUD для портов (только админы)
@api_bp.route('/ports', methods=['POST'])
@jwt_required()
def create_port():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    errors = port_schema.validate(data)  # Добавлено
    if errors:
        return jsonify(errors), 400
    
    try:
        new_port = Port(**data)
        db.session.add(new_port)
        db.session.commit()
        return jsonify(port_schema.dump(new_port)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create port', 'details': str(e)}), 500

@api_bp.route('/ports/<int:port_id>', methods=['PUT'])
@jwt_required()
def update_port(port_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    port = Port.query.get_or_404(port_id)
    data = request.get_json()
    errors = port_schema.validate(data, partial=True)
    if errors:
        return jsonify(errors), 400  # Изменено на 400
    
    try:
        for key, value in data.items():
            setattr(port, key, value)
        db.session.commit()
        if port.air_quality > 50 or port.water_quality > 30:
            send_notification_async(port, f'Alert: High pollution in {port.name}')
        return jsonify(port_schema.dump(port))
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update port', 'details': str(e)}), 500

@api_bp.route('/ports/<int:port_id>', methods=['DELETE'])
@jwt_required()
def delete_port(port_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    
    port = Port.query.get_or_404(port_id)
    try:
        db.session.delete(port)
        db.session.commit()
        return jsonify({'message': 'Port deleted'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete port', 'details': str(e)}), 500

# Загрузка отчета
@api_bp.route('/ports/<int:port_id>/upload_report', methods=['POST'])
@jwt_required()
def upload_report(port_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    file = request.files.get('file')
    if not file or not file.filename or not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Invalid file'}), 400
    
    port = Port.query.get_or_404(port_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        file.save(temp_file.name)
        temp_path = temp_file.name
    
    try:
        with pdfplumber.open(temp_path) as pdf:
            text = ''.join(page.extract_text() for page in pdf.pages)
        
        patterns = {
            'air_quality': r'air\s*quality[:\s]*(\d+\.?\d*)',
            'water_quality': r'water\s*quality[:\s]*(\d+\.?\d*)',
            'co2_emissions': r'co2\s*emissions?[:\s]*(\d+\.?\d*)',
            'incidents': r'incidents?[:\s]*(\d+)'
        }
        updated_fields = []
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1)) if '.' in match.group(1) else int(match.group(1))
                setattr(port, field, value)
                updated_fields.append(field)
        
        if not updated_fields:
            return jsonify({'error': 'No matching data found in PDF'}), 400
        
        db.session.commit()
        return jsonify({'message': f'Report parsed and updated fields: {", ".join(updated_fields)}'})
    except Exception as e:
        return jsonify({'error': 'Failed to parse PDF', 'details': str(e)}), 500
    finally:
        os.unlink(temp_path)

# Подписка
@api_bp.route('/ports/<int:port_id>/subscribe', methods=['POST'])
def subscribe(port_id):
    data = request.get_json()
    email = data.get('email')
    if not email or '@' not in email or '.' not in email:
        return jsonify({'error': 'Invalid email'}), 400
    
    port = Port.query.get_or_404(port_id)
    subscribers_list = port.subscribers.split(',') if port.subscribers else []
    if email in subscribers_list:
        return jsonify({'message': 'Already subscribed'}), 200
    
    subscribers_list.append(email)
    port.subscribers = ','.join(subscribers_list)
    try:
        db.session.commit()
        return jsonify({'message': 'Subscribed'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to subscribe', 'details': str(e)}), 500

# Отчеты
@api_bp.route('/reports', methods=['POST'])
def create_report():
    data = request.get_json()
    errors = report_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    port = Port.query.get(data['port_id'])
    if not port:
        return jsonify({'error': 'Port not found'}), 404
    
    try:
        new_report = Report(**data)
        db.session.add(new_report)
        db.session.commit()
        return jsonify(report_schema.dump(new_report)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create report', 'details': str(e)}), 500

# Получение отчетов (для админов)
@api_bp.route('/reports', methods=['GET'])
@jwt_required()
def get_reports():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    reports = Report.query.all()
    return jsonify(report_schema.dump(reports, many=True))