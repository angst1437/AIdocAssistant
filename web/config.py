import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'you-will-never-guess'
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'uploads')

    # AI API keys
    YANDEX_GPT_API_KEY = os.environ.get('YANDEX_GPT_API_KEY')
    GIGACHAT_API_KEY = os.environ.get('GIGACHAT_API_KEY')
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

    # Logging configuration
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')

    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

