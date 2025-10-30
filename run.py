from app import create_app, db
from flask_migrate import upgrade  # Если используете миграции

app = create_app()

with app.app_context():
    upgrade()  # Применит миграции

if __name__ == '__main__':
    app.run()
