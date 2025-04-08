import click
from web.app import db # Импорт db
from web.app.models import User # Импорт модели User

def run_seed():
    """Создает тестовых пользователей."""
    users_data = [
        {'username': 'admin', 'email': 'admin@example.com', 'password': 'admin321', 'role': 'admin'},
        {'username': 'user1', 'email': 'user1@example.com', 'password': 'user12345', 'role': 'user'},
    ]

    click.echo("Создание пользователей...")
    users_created_count = 0
    for user_data in users_data:
        if User.query.filter_by(username=user_data['username']).first() or \
           User.query.filter_by(email=user_data['email']).first():
            click.echo(f"Пользователь {user_data['username']} или email {user_data['email']} уже существует. Пропускаем.")
            continue

        user = User(username=user_data['username'], email=user_data['email'], role=user_data['role'])
        user.set_password(user_data['password'])
        db.session.add(user)
        click.echo(f"Пользователь {user_data['username']} ({user_data['role']}) подготовлен.")
        users_created_count += 1

    if users_created_count > 0:
        click.echo(f"{users_created_count} новых пользователей подготовлены.")
    else:
        click.echo("Новые пользователи не добавлялись (уже существуют).")
    return True # Успех