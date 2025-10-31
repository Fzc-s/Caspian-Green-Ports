# run.py
from app import create_app, db
from app.models import User
from seed import seed_database  # Импорт функции seed из соседнего файла seed.py

app = create_app()

with app.app_context():
    if not User.query.first():
        seed_database()  # Запуск seed-кода из seed.py

if __name__ == '__main__':
    app.run()