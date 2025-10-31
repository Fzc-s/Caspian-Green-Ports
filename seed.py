from flask import Blueprint
from app import db
from app.models import User, Port, Report

seed_bp = Blueprint('seed', __name__)

@seed_bp.cli.command('run')
def run_seed():
    seed_database()

def seed_database():
    # Убрали db.create_all() — используйте миграции
    # Добавление пользователей с проверками
    if not User.query.filter_by(username='admin').first():
        admin = User()
        admin.username = 'admin'
        admin.role = 'admin'
        admin.set_password('adminpass')
        db.session.add(admin)
    
    if not User.query.filter_by(username='user').first():
        user = User()
        user.username = 'user'
        user.role = 'user'
        user.set_password('userpass')
        db.session.add(user)
    
    if not User.query.filter_by(username='moderator').first():
        user2 = User()
        user2.username = 'moderator'
        user2.role = 'user'
        user2.set_password('modpass')
        db.session.add(user2)
    
    if not User.query.filter_by(username='citizen').first():
        user3 = User()
        user3.username = 'citizen'
        user3.role = 'user'
        user3.set_password('citizenpass')
        db.session.add(user3)
    
    # Порты
    ports_data = [
        {'name': 'Port of Baku', 'lat': 40.37, 'lng': 49.89, 'air_quality': 45.0, 'water_quality': 25.0, 'co2_emissions': 800.0, 'incidents': 3},
        {'name': 'Port of Aktau', 'lat': 43.65, 'lng': 51.16, 'air_quality': 50.0, 'water_quality': 30.0, 'co2_emissions': 600.0, 'incidents': 2},
        {'name': 'Port of Astrakhan', 'lat': 46.35, 'lng': 48.04, 'air_quality': 40.0, 'water_quality': 20.0, 'co2_emissions': 500.0, 'incidents': 1},
        {'name': 'Port of Turkmenbashi', 'lat': 40.02, 'lng': 52.97, 'air_quality': 55.0, 'water_quality': 35.0, 'co2_emissions': 700.0, 'incidents': 4},
        {'name': 'Port of Makhachkala', 'lat': 42.97, 'lng': 47.50, 'air_quality': 42.0, 'water_quality': 22.0, 'co2_emissions': 550.0, 'incidents': 2},
        {'name': 'Port of Bandar Anzali', 'lat': 37.47, 'lng': 49.46, 'air_quality': 48.0, 'water_quality': 28.0, 'co2_emissions': 650.0, 'incidents': 3},
        {'name': 'Port of Neka', 'lat': 36.65, 'lng': 53.30, 'air_quality': 52.0, 'water_quality': 32.0, 'co2_emissions': 720.0, 'incidents': 5},
        {'name': 'Port of Amirabad', 'lat': 36.87, 'lng': 54.02, 'air_quality': 47.0, 'water_quality': 27.0, 'co2_emissions': 680.0, 'incidents': 2},
        {'name': 'Port of Nowshahr', 'lat': 36.65, 'lng': 51.50, 'air_quality': 44.0, 'water_quality': 24.0, 'co2_emissions': 590.0, 'incidents': 1},
        {'name': 'Port of Lagan', 'lat': 45.40, 'lng': 47.35, 'air_quality': 38.0, 'water_quality': 18.0, 'co2_emissions': 450.0, 'incidents': 0},
    ]
    for port_data in ports_data:
        if not Port.query.filter_by(name=port_data['name']).first():
            port = Port(**port_data)
            db.session.add(port)
    
    # Отчеты
    reports_data = [
        {'port_id': 1, 'user_email': 'citizen@example.com', 'description': 'High pollution in Baku port area.'},
        {'port_id': 2, 'user_email': 'sailor@example.com', 'description': 'Oil spill observed near Aktau.'},
        {'port_id': 3, 'user_email': 'environmentalist@example.com', 'description': 'Water contamination in Astrakhan.'},
        {'port_id': 4, 'user_email': 'local@example.com', 'description': 'Excessive emissions in Turkmenbashi.'},
        {'port_id': 5, 'user_email': 'fisherman@example.com', 'description': 'Fish die-off near Makhachkala.'},
        {'port_id': 6, 'user_email': 'traveler@example.com', 'description': 'Poor air quality in Bandar Anzali.'},
        {'port_id': 7, 'user_email': 'worker@example.com', 'description': 'Industrial waste in Neka.'},
        {'port_id': 8, 'user_email': 'activist@example.com', 'description': 'Noise pollution in Amirabad.'},
        {'port_id': 9, 'user_email': 'resident@example.com', 'description': 'Chemical smell in Nowshahr.'},
        {'port_id': 10, 'user_email': 'scientist@example.com', 'description': 'Low pollution levels in Lagan.'},
    ]
    for report_data in reports_data:
        if not Report.query.filter_by(port_id=report_data['port_id'], description=report_data['description']).first():
            report = Report(**report_data)
            db.session.add(report)
    
    db.session.commit()
    print("Seed completed!")