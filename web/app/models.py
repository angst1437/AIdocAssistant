from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from web.app import db, login_manager

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # 'user', 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    documents = db.relationship('Document', backref='author', lazy='dynamic')
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

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, index=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    blocks = db.relationship('DocumentBlock', backref='document', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Document {self.title}>'

class DocumentBlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'))
    block_type = db.Column(db.String(50))  # 'heading', 'paragraph', 'list', etc.
    content = db.Column(db.Text)
    order = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    recommendations = db.relationship('Recommendation', backref='block', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<DocumentBlock {self.id} of {self.document_id}>'

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    block_id = db.Column(db.Integer, db.ForeignKey('document_block.id'))
    start_char = db.Column(db.Integer)
    end_char = db.Column(db.Integer)
    original_text = db.Column(db.Text)
    suggestion = db.Column(db.Text)
    explanation = db.Column(db.Text)
    type_of_error = db.Column(db.String(50))  # 'grammar', 'style', 'gost', etc.
    ai_provider = db.Column(db.String(50))  # 'yandex', 'gigachat', 'gemini'
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Recommendation {self.id} for block {self.block_id}>'

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

