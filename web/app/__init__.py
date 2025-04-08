import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
from flask_wtf.csrf import CSRFProtect

web_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
instance_folder_path = os.path.join(web_folder_path, 'instance')
migrations_folder_path = os.path.join(web_folder_path, 'migrations')

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate(directory=migrations_folder_path)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
csrf = CSRFProtect()

def create_app(config_class=None):
    app = Flask(__name__,
                instance_path=instance_folder_path,
                instance_relative_config=True)

    # Load configuration
    try:
        if config_class is None:
            app.config.from_object('web.config.Config')
        else:
            app.config.from_object(config_class)
    except Exception as e:
        logging.exception("!!! ОШИБКА при загрузке конфигурации")
        raise e

    # Initialize extensions with app
    try:
        db.init_app(app)
        migrate.init_app(app, db)
        login_manager.init_app(app)
        csrf.init_app(app)
    except Exception as e:
        logging.exception("!!! ОШИБКА при инициализации расширений")
        raise e

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, 'uploads', 'error_reports'), exist_ok=True)

    # Register blueprints
    try:
        from .routes.auth import auth_bp
        from .routes.documents import documents_bp
        from .routes.ai import ai_bp
        from .routes.feedback import feedback_bp
        from .routes.admin import admin_bp
        from .routes.main import main_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(documents_bp, url_prefix='/documents')
        app.register_blueprint(ai_bp)
        app.register_blueprint(feedback_bp)
        app.register_blueprint(admin_bp)
    except ImportError as e:
        logging.exception(f"!!! Ошибка ИМПОРТА при регистрации блюпринта: {e}")
        raise e
    except Exception as e:
        logging.exception(f"!!! НЕПРЕДВИДЕННАЯ ОШИБКА при регистрации блюпринта: {e}")
        raise e

    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/nir_assistant.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('NIR Assistant startup')

    # Shell context
    @app.shell_context_processor
    def make_shell_context():
        from .models import User, DocumentApp, DocumentSection, DocumentSectionContent, TextRecommendation, ErrorReport, \
            LogEntry
        return {
            'db': db,
            'User': User,
            'Document': DocumentApp,
            'DocumentSection': DocumentSection,
            'DocumentSectionContent': DocumentSectionContent,
            'TextRecommendation': TextRecommendation,
            'ErrorReport': ErrorReport,
            'LogEntry': LogEntry
        }

    # --- Регистрация команд CLI из commands.py ---
    from . import commands  # Импортируем модуль commands.py
    app.cli.add_command(commands.reset_dev_db_command)
    app.cli.add_command(commands.seed_db_command)

    return app