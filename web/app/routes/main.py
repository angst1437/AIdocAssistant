from flask import Blueprint, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def root():
    if current_user.is_authenticated:
        # Перенаправляем на список документов
        return redirect(url_for('documents.index'))
    else:
        # Перенаправляем на страницу логина
        return redirect(url_for('auth.login'))