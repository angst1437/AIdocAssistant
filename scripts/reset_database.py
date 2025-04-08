import os
import click
from flask import current_app
from flask_migrate import upgrade
from web.app import db

def run_reset():
    """Удаляет файл БД SQLite и применяет миграции."""
    web_folder = os.path.abspath(os.path.join(current_app.root_path, '..'))
    migrations_dir = os.path.join(web_folder, 'migrations')

    db_path_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    db_file_path = None

    if db_path_uri and db_path_uri.startswith('sqlite:///'):
        db_file_path = db_path_uri[len('sqlite:///'):]
        db_file_path = os.path.abspath(db_file_path)
    else:
        click.echo("Ошибка: Не удалось определить путь к SQLite базе данных из конфигурации.", err=True)
        return False

    # --- Удаление БД ---
    click.echo("-" * 40)
    click.echo(f"ПРЕДУПРЕЖДЕНИЕ: Будет удалена база данных: {db_file_path}")
    if not click.confirm("Вы уверены, что хотите продолжить? ВСЕ ДАННЫЕ БУДУТ ПОТЕРЯНЫ!"):
        click.echo("Операция отменена.")
        return False

    # 1. Удаляем старый файл базы данных
    try:
        if os.path.exists(db_file_path):
            os.remove(db_file_path)
            click.echo(f"Файл базы данных удален: {db_file_path}")
        else:
            click.echo("Файл базы данных не найден, удаление не требуется.")
    except OSError as e:
        click.echo(f"Ошибка при удалении файла БД: {e}", err=True)
        return False

    # 2. Применяем миграции (создаем все таблицы)
    click.echo("Применение миграций для создания структуры БД...")
    try:
        # Проверка папки миграций
        click.echo(f"Проверка папки миграций: {migrations_dir}")
        if not os.path.exists(migrations_dir):
            click.echo(f"ОШИБКА: Папка миграций не найдена.", err=True)
            click.echo(f"Убедитесь, что папка '{migrations_dir}' существует.", err=True)
            click.echo("Запустите 'flask db init --directory web/migrations' (если необходимо) и 'flask db migrate'.", err=True)
            return False

        upgrade() # Эта функция из flask_migrate создаст таблицы
        click.echo("Структура базы данных создана/обновлена.")
        return True
    except Exception as e:
        click.echo(f"Ошибка во время применения миграций (flask db upgrade): {e}", err=True)
        # Попытаемся откатить сессию, если ошибка произошла на стадии сидинга
        db.session.rollback()
        return False