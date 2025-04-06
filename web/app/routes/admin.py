from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from web.app import db
from web.app.models import User, ErrorReport, LogEntry
from web.app.utils.decorators import admin_required, log_activity

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@admin_required
def index():
    return render_template('admin/index.html', title='Admin Dashboard')

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', title='User Management', users=users)

@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
@log_activity(level='INFO', message='User status toggled')
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent self-deactivation
    if user.id == current_user.id:
        return jsonify({'error': 'You cannot deactivate your own account'}), 400
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    return jsonify({'success': True, 'status': status})

@admin_bp.route('/error-reports')
@login_required
@admin_required
def error_reports():
    status_filter = request.args.get('status', 'all')
    
    query = ErrorReport.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    reports = query.order_by(ErrorReport.timestamp.desc()).all()
    return render_template('admin/error_reports.html', title='Error Reports', reports=reports)

@admin_bp.route('/error-reports/<int:report_id>/update-status', methods=['POST'])
@login_required
@admin_required
@log_activity(level='INFO', message='Error report status updated')
def update_error_report_status(report_id):
    report = ErrorReport.query.get_or_404(report_id)
    status = request.form.get('status')
    
    if status not in ['open', 'in_progress', 'closed']:
        return jsonify({'error': 'Invalid status'}), 400
    
    report.status = status
    db.session.commit()
    
    return jsonify({'success': True})

@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    level_filter = request.args.get('level', 'all')
    user_filter = request.args.get('user_id', 'all')
    
    query = LogEntry.query
    
    if level_filter != 'all':
        query = query.filter_by(level=level_filter)
    
    if user_filter != 'all':
        query = query.filter_by(user_id=user_filter)
    
    logs = query.order_by(LogEntry.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    users = User.query.all()
    
    return render_template(
        'admin/logs.html', 
        title='System Logs', 
        logs=logs,
        users=users,
        level_filter=level_filter,
        user_filter=user_filter
    )

