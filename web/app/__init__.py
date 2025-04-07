import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
csrf = CSRFProtect()
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def create_app(config_class=None):
    app = Flask(__name__,
                instance_path=os.path.join(project_root, 'instance'),
                instance_relative_config=True)


    print(f"DEBUG: Project Root: {project_root}")
    print(f"DEBUG: Calculated Instance Path: {app.instance_path}")


    # Load configuration
    if config_class is None:
        app.config.from_object('config.Config')
    else:
        app.config.from_object(config_class)

    print(f"DEBUG: SQLALCHEMY_DATABASE_URI from config: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.instance_path, 'uploads', 'error_reports'), exist_ok=True)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.documents import documents_bp
    from .routes.ai import ai_bp
    from .routes.feedback import feedback_bp
    from .routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(admin_bp)
    
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
        from web.app.models import User, DocumentApp, DocumentBlock, Recommendation, ErrorReport, LogEntry
        return {
            'db': db, 
            'User': User, 
            'Document': DocumentApp,
            'DocumentBlock': DocumentBlock,
            'Recommendation': Recommendation,
            'ErrorReport': ErrorReport,
            'LogEntry': LogEntry
        }
    
    return app

