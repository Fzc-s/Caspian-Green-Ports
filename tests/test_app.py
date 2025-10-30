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
            db.drop_all()
            db.create_all()
            
            # Создаем тестового админа
            user = User(username='testadmin', role='admin')
            user.set_password('testpass')
            db.session.add(user)
            
            # Создаем тестовый порт (id=1) — добавлено для тестов
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
            db.session.commit()
            
            yield client

# Тест для логина
def test_login(client):
    response = client.post('/api/login', json={'username': 'testadmin', 'password': 'testpass'})
    assert response.status_code == 200
    assert 'access_token' in response.get_json()

# Тест для получения списка портов
def test_get_ports(client):
    response = client.get('/api/ports')
    assert response.status_code == 200
    assert isinstance(response.get_json(), dict)
    assert 'ports' in response.get_json()

# Тест для создания нового порта (исправлены данные для валидации)
def test_create_port(client):
    access_token = get_access_token(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.post('/api/ports', headers=headers, json={
        'name': 'New Test Port',
        'lat': 40.0,  # Валидно
        'lng': 50.0,
        'air_quality': 21.0,  # >=0
        'water_quality': 9.0,
        'co2_emissions': 680.0,
        'incidents': 43
    })
    print(response.get_json())
    assert response.status_code == 201
    assert 'name' in response.get_json()
    

# Тест для обновления информации о порте (исправлены данные)
def test_update_port(client):
    access_token = get_access_token(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.put('/api/ports/1', headers=headers, json={
        'name': 'Updated Port',
        'air_quality': 22.0,
        'water_quality': 10.0,
        'co2_emissions': 700.0,
        'incidents': 50
    })
    assert response.status_code == 200
    assert 'name' in response.get_json()

# Тест для удаления порта
def test_delete_port(client):
    access_token = get_access_token(client)
    headers = {'Authorization': f'Bearer {access_token}'}
    response = client.delete('/api/ports/1', headers=headers)
    assert response.status_code == 200
    assert 'message' in response.get_json()

# Тест для загрузки отчета (убран, так как файл test_report.pdf может отсутствовать)
# def test_upload_report(client):
#     ...

# Тест для подписки на уведомления
def test_subscribe(client):
    response = client.post('/api/ports/1/subscribe', json={'email': 'test@example.com'})
    assert response.status_code == 200
    assert 'message' in response.get_json()

# Тест для создания отчета от граждан
def test_create_report(client):
    response = client.post('/api/reports', json={
        'port_id': 1,
        'user_email': 'test@example.com',
        'description': 'Test report'
    })
    assert response.status_code == 201
    assert 'id' in response.get_json()

# Вспомогательная функция для получения JWT
def get_access_token(client):
    response = client.post('/api/login', json={'username': 'testadmin', 'password': 'testpass'})
    return response.get_json()['access_token']