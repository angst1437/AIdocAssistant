from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # 'user', 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    documents = db.relationship('DocumentApp', backref='author', lazy='dynamic')
    error_reports = db.relationship('ErrorReport', backref='author', lazy='dynamic')
    log_entries = db.relationship('LogEntry', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class DocumentApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    template_id = db.Column(db.Integer, db.ForeignKey('document_template.id'), nullable=True)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, index=True, default=datetime.utcnow, onupdate=datetime.utcnow)

    sections = db.relationship('DocumentSectionContent', backref='document', lazy='dynamic', cascade='all, delete-orphan')
    text_recommendations = db.relationship('TextRecommendation', backref='document', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Document {self.title}>'


class DocumentTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    sections = db.relationship('DocumentSection', backref='template', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('DocumentApp', backref='template', lazy='dynamic')

    def __repr__(self):
        return f'<DocumentTemplate {self.name}>'


class DocumentSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('document_template.id'))
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)  # ТЛ, В, ОЧ и т.д.
    slug = db.Column(db.String(50), nullable=False)  # title-page, introduction, etc.
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False)
    editor_type = db.Column(db.Integer, nullable=False)  # 1 - форма, 2 - редактор с ИИ, 3 - смешанный
    form_schema = db.Column(db.JSON, nullable=True)  # Схема формы в JSON (для типов 1 и 3)

    document_sections = db.relationship('DocumentSectionContent', backref='section_template', lazy='dynamic')

    def __repr__(self):
        return f'<DocumentSection {self.name}>'


class DocumentSectionContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document_app.id'))
    section_id = db.Column(db.Integer, db.ForeignKey('document_section.id'))
    content = db.Column(db.Text)  # HTML-содержимое для редактора
    form_data = db.Column(db.JSON, nullable=True)  # Данные формы в JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<DocumentSectionContent for doc {self.document_id}, section {self.section_id}>'


class TextRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document_app.id'))
    section_id = db.Column(db.Integer, db.ForeignKey('document_section.id'))
    start_char = db.Column(db.Integer)
    end_char = db.Column(db.Integer)
    original_text = db.Column(db.Text)
    suggestion = db.Column(db.Text)
    explanation = db.Column(db.Text)
    type_of_error = db.Column(db.String(50))  # 'grammar', 'style', 'gost', 'water', etc.
    ai_provider = db.Column(db.String(50))  # 'yandex', 'gigachat', 'gemini'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    section = db.relationship('DocumentSection', backref='recommendations')

    def __repr__(self):
        return f'<TextRecommendation {self.id} for doc {self.document_id}, section {self.section_id}>'


class ErrorReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.Text)
    screenshot_url = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='open')  # 'open', 'in_progress', 'closed'

    def __repr__(self):
        return f'<ErrorReport {self.id} by user {self.user_id}>'


class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    level = db.Column(db.String(20))  # 'INFO', 'WARNING', 'ERROR', etc.
    message = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    request_url = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    def __repr__(self):
        return f'<LogEntry {self.id}: {self.level}>'

