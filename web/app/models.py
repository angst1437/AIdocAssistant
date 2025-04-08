# models.py

from datetime import datetime
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from web.app import db, login_manager # Assuming db and login_manager are initialized in web/app/__init__.py


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128)) # Consider increasing length for future hash algorithms
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user', 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    documents = db.relationship('DocumentApp', backref='author', lazy='dynamic', cascade='all, delete-orphan') # Cascade delete user's documents
    error_reports = db.relationship('ErrorReport', backref='author', lazy='dynamic', cascade='all, delete-orphan') # Cascade delete user's reports
    log_entries = db.relationship('LogEntry', backref='user', lazy='dynamic') # Don't cascade logs usually

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # Handle cases where password_hash might be None (e.g., user created externally)
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id)) # Use db.session.get for primary key lookup
    except (TypeError, ValueError):
        return None


class DocumentApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey('document_template.id'), nullable=False, index=True) # Usually template is required
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, index=True, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    # Ensure relationship names are clear and backrefs make sense
    # Renamed 'sections' to 'section_contents' for clarity, backref 'document' is good
    section_contents = db.relationship('DocumentSectionContent', backref='document', lazy='dynamic', cascade='all, delete-orphan')
    # backref 'document' for TextRecommendation is good
    text_recommendations = db.relationship('TextRecommendation', backref='document', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<DocumentApp {self.id}: {self.title}>'


class DocumentTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Relationships
    # 'sections' relationship (one-to-many with DocumentSection) seems correct
    sections = db.relationship('DocumentSection', backref='template', lazy='dynamic', cascade='all, delete-orphan', order_by='DocumentSection.order') # Order sections by 'order' field
    # 'documents' relationship (one-to-many with DocumentApp) seems correct
    documents = db.relationship('DocumentApp', backref='template', lazy='dynamic') # No cascade here, deleting template shouldn't delete documents

    __table_args__ = (db.UniqueConstraint('name', name='uq_document_template_name'),)

    def __repr__(self):
        return f'<DocumentTemplate {self.name}>'


class DocumentSection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('document_template.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=True)  # Allow nullable if code isn't always used
    slug = db.Column(db.String(50), nullable=False, index=True) # Slugs should be indexed, maybe unique per template?
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=False, index=True) # Index for ordering
    editor_type = db.Column(db.Integer, nullable=False)  # 1 - form, 2 - rich text, 3 - mixed, 4 - generated etc.
    form_schema = db.Column(db.JSON, nullable=True)  # Schema for form-based sections
    # --- НОВОЕ ПОЛЕ ---
    is_mandatory = db.Column(db.Boolean, default=False, nullable=False) # True if the section must be filled

    # Relationships
    # Renamed 'document_sections' to 'contents' for clarity, backref 'section_template' is okay
    contents = db.relationship('DocumentSectionContent', backref='section_template', lazy='dynamic', cascade='all, delete-orphan')

    # Add unique constraint for slug within a template
    __table_args__ = (db.UniqueConstraint('template_id', 'slug', name='uq_document_section_template_slug'),)

    def __repr__(self):
        return f'<DocumentSection {self.id}: {self.name} (Template {self.template_id})>'


class DocumentSectionContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document_app.id'), nullable=False, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey('document_section.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=True)  # HTML content for rich text editor
    form_data = db.Column(db.JSON, nullable=True)  # JSON data for form editor
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Add unique constraint: one content entry per document/section pair
    __table_args__ = (db.UniqueConstraint('document_id', 'section_id', name='uq_document_section_content'),)

    def __repr__(self):
        return f'<DocumentSectionContent for doc {self.document_id}, section {self.section_id}>'


class TextRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document_app.id'), nullable=False, index=True)
    section_id = db.Column(db.Integer, db.ForeignKey('document_section.id'), nullable=False, index=True) # Link recommendation to specific section content? Maybe section_content_id?
    start_char = db.Column(db.Integer, nullable=True) # Allow null if recommendation applies to whole section
    end_char = db.Column(db.Integer, nullable=True)   # Allow null
    original_text = db.Column(db.Text, nullable=True) # May not always have original text fragment
    suggestion = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    type_of_error = db.Column(db.String(50), index=True)  # Index for filtering
    ai_provider = db.Column(db.String(50), nullable=True) # Could be null if generated differently
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # 'pending', 'accepted', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Consider relating to DocumentSectionContent instead if recommendations are tied to specific content versions
    # section = db.relationship('DocumentSection', backref='recommendations') # This relates to the *template* section, might be okay

    def __repr__(self):
        return f'<TextRecommendation {self.id} for doc {self.document_id}>'


class ErrorReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True) # Allow anonymous reports? nullable=True
    description = db.Column(db.Text, nullable=False)
    screenshot_url = db.Column(db.String(255), nullable=True) # URL might be long
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = db.Column(db.String(20), default='open', nullable=False, index=True)  # 'open', 'in_progress', 'closed'
    page_url = db.Column(db.String(255), nullable=True) # URL where the error occurred

    def __repr__(self):
        user_info = f"user {self.user_id}" if self.user_id else "anonymous"
        return f'<ErrorReport {self.id} by {user_info}>'


class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, nullable=False)
    level = db.Column(db.String(20), index=True, nullable=False)  # 'INFO', 'WARNING', 'ERROR', etc.
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True) # Log entries might not always have a user
    request_url = db.Column(db.String(500), nullable=True) # Allow longer URLs
    ip_address = db.Column(db.String(45), nullable=True) # IPv4/IPv6
    logger_name = db.Column(db.String(100), nullable=True) # Which logger produced this?
    traceback = db.Column(db.Text, nullable=True) # Store traceback for errors

    def __repr__(self):
        return f'<LogEntry {self.id}: {self.level} at {self.timestamp}>'