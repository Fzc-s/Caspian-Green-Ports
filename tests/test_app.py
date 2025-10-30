import pytest
from app import create_app, db
from app.models import User, Port

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            # Очистка и пересоздание БД для чистоты тестов
            db.drop_all()
            db.create_all()
            # Создайте тестового пользователя (исправлен конструктор)
            user = User()
            user.username = 'testadmin'
            user.role = 'admin'
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
        yield client

def test_get_ports(client):
    response = client.get('/api/ports')
    assert response.status_code == 200
    assert isinstance(response.get_json(), dict)  # Теперь возвращает dict с пагинацией
    assert 'ports' in response.get_json()