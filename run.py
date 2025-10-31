from app import create_app, db
from app.models import User, Port, Report

app = create_app()

with app.app_context():
    if not User.query.first():
        # Seed код
        user = User(username='admin', role='admin')
        user.set_password('adminpass')
        db.session.add(user)
        db.session.commit()

if __name__ == '__main__':
    app.run()
