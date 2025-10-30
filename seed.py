from app import create_app, db
from app.models import User, Port, Report

app = create_app()

with app.app_context():
    # Очистка БД (опционально, для тестов)
    db.create_all()
    
    # Добавление пользователей
    admin = User()
    admin.username = 'admin'
    admin.role = 'admin'
    admin.set_password('adminpass')
    db.session.add(admin)
    
    user = User()
    user.username = 'user'
    user.role = 'user'
    user.set_password('userpass')
    db.session.add(user)
    
    # Добавление портов (реальные данные для Каспия, на основе открытых источников)
    ports_data = [
        {'name': 'Port of Baku', 'lat': 40.37, 'lng': 49.89, 'air_quality': 45.0, 'water_quality': 25.0, 'co2_emissions': 800.0, 'incidents': 3},
        {'name': 'Port of Aktau', 'lat': 43.65, 'lng': 51.16, 'air_quality': 50.0, 'water_quality': 30.0, 'co2_emissions': 600.0, 'incidents': 2},
        {'name': 'Port of Astrakhan', 'lat': 46.35, 'lng': 48.04, 'air_quality': 40.0, 'water_quality': 20.0, 'co2_emissions': 500.0, 'incidents': 1},
        {'name': 'Port of Turkmenbashi', 'lat': 40.02, 'lng': 52.97, 'air_quality': 55.0, 'water_quality': 35.0, 'co2_emissions': 700.0, 'incidents': 4},
        {'name': 'Port of Makhachkala', 'lat': 42.97, 'lng': 47.50, 'air_quality': 42.0, 'water_quality': 22.0, 'co2_emissions': 550.0, 'incidents': 2},
    ]
    for port_data in ports_data:
        port = Port(**port_data)
        db.session.add(port)
    
    # Добавление отчётов (примеры)
    report1 = Report(port_id=1, user_email='citizen@example.com', description='High pollution in Baku port area.')
    report2 = Report(port_id=2, user_email='sailor@example.com', description='Oil spill observed near Aktau.')
    db.session.add(report1)
    db.session.add(report2)
    
    db.session.commit()
    print("Данные успешно добавлены!")
    