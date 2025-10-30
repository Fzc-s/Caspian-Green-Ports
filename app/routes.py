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

api_bp = Blueprint('api', __name__)  # Исправлено: __name__
port_schema = PortSchema()
ports_schema = PortSchema(many=True)
report_schema = ReportSchema()
login_schema = LoginSchema()

# Функция для уведомлений (асинхронно)
def send_notification_async(port, message):
    def send():
        if port.subscribers:
            emails = port.subscribers.split(',')
            msg = Message('EcoPorts Alert', sender='noreply@ecoports.com', recipients=emails)
            msg.body = message
            mail.send(msg)
    threading.Thread(target=send).start()

# Логин (возвращает JWT)
@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    errors = login_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token, role=user.role), 200
    return jsonify({'error': 'Invalid credentials'}), 401

# Публичные маршруты (GET без JWT) — улучшены для адаптивности
@api_bp.route('/ports', methods=['GET'])
def get_ports():
    # Добавлены фильтры, сортировка и пагинация для веб-приложения
    query = Port.query
    
    # Фильтр по min_score убран (невозможно в SQL, так как green_score — property)
    # Вместо этого фильтр применяется после загрузки
    
    # Сортировка (например, ?sort=green_score&order=desc)
    sort_by = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    if sort_by in ['name', 'air_quality', 'water_quality', 'co2_emissions', 'incidents']:
        column = getattr(Port, sort_by)
        query = query.order_by(column.desc() if order == 'desc' else column.asc())
    elif sort_by == 'green_score':
        # Сортировка по green_score: загрузим и отсортируем в Python
        ports_list = query.all()
        ports_list.sort(key=lambda p: p.green_score, reverse=(order == 'desc'))
        query = ports_list  # Теперь это список
    
    # Пагинация
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
    
    # Фильтр по min_score (применяем после загрузки)
    min_score = request.args.get('min_score', type=float)
    if min_score is not None:
        paginated_items = [p for p in paginated_items if p.green_score >= min_score]
    
    return jsonify({
        'ports': ports_schema.dump(paginated_items),
        'total': total,
        'pages': pages,
        'current_page': current_page
    })

@api_bp.route('/ports/<int:port_id>', methods=['GET'])  # Исправлено: <int:port_id>
def get_port(port_id):
    port = Port.query.get_or_404(port_id)
    return jsonify(port_schema.dump(port))

# Новый эндпоинт: Статистика для графиков (адаптивно для frontend)
@api_bp.route('/ports/stats', methods=['GET'])
def get_ports_stats():
    ports = Port.query.all()
    stats = {
        'total_ports': len(ports),
        'avg_green_score': round(sum(p.green_score for p in ports) / len(ports), 2) if ports else 0,
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
    errors = port_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    new_port = Port(**data)
    db.session.add(new_port)
    db.session.commit()
    return jsonify(port_schema.dump(new_port)), 201

@api_bp.route('/ports/<int:port_id>', methods=['PUT'])  # Исправлено: <int:port_id>
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
        return jsonify(errors), 400
    
    for key, value in data.items():
        setattr(port, key, value)
    db.session.commit()
    
    # Уведомления при превышениях
    if port.air_quality > 50 or port.water_quality > 30:
        send_notification_async(port, f'Alert: High pollution in {port.name}')
    
    return jsonify(port_schema.dump(port))

@api_bp.route('/ports/<int:port_id>', methods=['DELETE'])  # Исправлено: <int:port_id>
@jwt_required()
def delete_port(port_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    port = Port.query.get_or_404(port_id)
    db.session.delete(port)
    db.session.commit()
    return jsonify({'message': 'Port deleted'})

# Загрузка отчёта
@api_bp.route('/ports/<int:port_id>/upload_report', methods=['POST'])  # Исправлено: <int:port_id>
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
    
    # Временное сохранение файла для pdfplumber
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        file.save(temp_file.name)
        temp_path = temp_file.name
    
    try:
        with pdfplumber.open(temp_path) as pdf:
            text = ''.join(page.extract_text() for page in pdf.pages)
        
        # Гибкий парсинг
        patterns = {
            'air_quality': r'air\s*quality[:\s]*(\d+\.?\d*)',
            'water_quality': r'water\s*quality[:\s]*(\d+\.?\d*)',
            'co2_emissions': r'co2\s*emissions?[:\s]*(\d+\.?\d*)',
            'incidents': r'incidents?[:\s]*(\d+)'
        }
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1)) if '.' in match.group(1) else int(match.group(1))
                setattr(port, field, value)
        
        db.session.commit()
        return jsonify({'message': 'Report parsed and updated'})
    finally:
        os.unlink(temp_path)

# Подписка
@api_bp.route('/ports/<int:port_id>/subscribe', methods=['POST'])  # Исправлено: <int:port_id>
def subscribe(port_id):
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    port = Port.query.get_or_404(port_id)
    if email not in port.subscribers:
        port.subscribers += f',{email}' if port.subscribers else email
        db.session.commit()
    return jsonify({'message': 'Subscribed'})

# Отчёты от граждан
@api_bp.route('/reports', methods=['POST'])
def create_report():
    data = request.get_json()
    errors = report_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    new_report = Report(**data)
    db.session.add(new_report)
    db.session.commit()
    return jsonify(report_schema.dump(new_report)), 201
