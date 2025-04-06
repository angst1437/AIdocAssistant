from functools import wraps
from flask import abort, request, current_app
from flask_login import current_user
from web.app.models import LogEntry
from web.app import db

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def log_activity(level='INFO', message=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                
                # Create log entry
                log_entry = LogEntry(
                    level=level,
                    message=message or f"{f.__name__} was called",
                    user_id=current_user.id if current_user.is_authenticated else None,
                    request_url=request.path,
                    ip_address=request.remote_addr
                )
                db.session.add(log_entry)
                db.session.commit()
                
                return result
            except Exception as e:
                # Log the error
                error_log = LogEntry(
                    level='ERROR',
                    message=f"Error in {f.__name__}: {str(e)}",
                    user_id=current_user.id if current_user.is_authenticated else None,
                    request_url=request.path,
                    ip_address=request.remote_addr
                )
                db.session.add(error_log)
                db.session.commit()
                
                # Re-raise the exception
                raise
        return decorated_function
    return decorator

