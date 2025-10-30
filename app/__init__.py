from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from config import Config  

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)  # Для React
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    
    # Регистрация blueprints
    from app.routes import api_bp  # Явный импорт для линтера
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Глобальные обработчики ошибок
    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning(f'404 error: {error}')
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'500 error: {error}')
        return {'error': 'Internal server error'}, 500
    
    # Shell-контекст для Flask-Migrate
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'User': User, 'Port': Port, 'Report': Report}
    
    return app

# Импорты моделей для shell-контекста
from app.models import User, Port, Report