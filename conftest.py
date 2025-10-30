import os
import sys
import pytest
from app import create_app, db
from app.models import User, Port

# Добавляем корневую папку в PYTHONPATH
sys.path.insert(0, os.path.abspath('.'))

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            
            # Создаем тестового админа
            user = User(username='testadmin', role='admin')
            user.set_password('testpass')
            db.session.add(user)
            
            # Создаем тестовый порт (id=1)
            port = Port(
                name='Test Port',
                lat=40.0,
                lng=50.0,
                air_quality=20.0,
                water_quality=10.0,
                co2_emissions=500.0,
                incidents=2
            )
            db.session.add(port)
            db.session.commit()  # Добавлено commit
            
            yield client