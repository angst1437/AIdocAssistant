from flask import Blueprint, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from web.app import db
from web.app.models import ErrorReport
from web.app.utils.decorators import log_activity
from datetime import datetime

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/report-error', methods=['POST'])
@login_required
@log_activity(level='INFO', message='Error report submitted')
def report_error():
    description = request.form.get('description')
    
    if not description:
        return jsonify({'error': 'Description is required'}), 400
    
    # Handle screenshot upload
    screenshot_url = None
    if 'screenshot' in request.files:
        file = request.files['screenshot']
        if file and file.filename:
            filename = secure_filename(file.filename)
            # Generate unique filename
            base, ext = os.path.splitext(filename)
            unique_filename = f"{base}_{current_user.id}_{int(datetime.utcnow().timestamp())}{ext}"
            
            # Save file
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'error_reports')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, unique_filename)
            file.save(file_path)
            
            # Store relative path
            screenshot_url = f"uploads/error_reports/{unique_filename}"
    
    # Create error report
    error_report = ErrorReport(
        user_id=current_user.id,
        description=description,
        screenshot_url=screenshot_url,
        status='open'
    )
    
    db.session.add(error_report)
    db.session.commit()
    
    return jsonify({'success': True, 'id': error_report.id})

