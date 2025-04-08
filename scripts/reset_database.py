import os
import click
from flask import current_app # Используем current_app для доступа к конфигурации
from flask_migrate import upgrade
from web.app import db # Импортируем db напрямую

def run_reset():
    """Удаляет файл БД SQLite и применяет миграции."""
    db_path_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI')

    if not db_path_uri or not db_path_uri.startswith('sqlite:///'):
        click.echo("Ошибка: Не удалось определить путь к SQLite базе данных или используется не SQLite.", err=True)
        return False # Возвращаем False при ошибке

    # Извлекаем путь к файлу из URI
    if db_path_uri.startswith('sqlite:///'):
        db_file_path = db_path_uri[len('sqlite:///'):]
    else:
         click.echo(f"Неподдерживаемый формат URI базы данных: {db_path_uri}", err=True)
         return False

    # Нормализуем путь (важно для Windows)
    db_file_path = os.path.abspath(db_file_path)
    instance_folder = os.path.dirname(db_file_path) # Папка instance/

    click.echo("-" * 40)
    click.echo(f"ПРЕДУПРЕЖДЕНИЕ: Будет удалена база данных: {db_file_path}")
    if not click.confirm("Вы уверены, что хотите продолжить? ВСЕ ДАННЫЕ БУДУТ ПОТЕРЯНЫ!"):
        click.echo("Операция отменена.")
        return False # Возвращаем False при отмене

    # 1. Удаляем старый файл базы данных
    try:
        if os.path.exists(db_file_path):
            os.remove(db_file_path)
            click.echo(f"Файл базы данных удален: {db_file_path}")
        else:
            click.echo("Файл базы данных не найден, удаление не требуется.")
        # Убедимся, что папка instance существует для новой БД
        os.makedirs(instance_folder, exist_ok=True)

    except OSError as e:
        click.echo(f"Ошибка при удалении файла БД: {e}", err=True)
        return False

    # 2. Применяем миграции (создаем все таблицы)
    click.echo("Применение миграций для создания структуры БД...")
    try:
        # Проверка папки миграций
        migrations_dir = os.path.join(current_app.root_path, '..', 'migrations')
        if not os.path.exists(migrations_dir):
             click.echo(f"ОШИБКА: Папка миграций не найдена по пути: {migrations_dir}", err=True)
             click.echo("Пожалуйста, запустите 'flask db init' и 'flask db migrate' хотя бы один раз.", err=True)
             return False

        upgrade() # Эта функция из flask_migrate создаст таблицы
        click.echo("Структура базы данных создана/обновлена.")
        return True # Возвращаем True при успехе
    except Exception as e:
        click.echo(f"Ошибка во время применения миграций (flask db upgrade): {e}", err=True)
        # Попытаемся откатить сессию, если ошибка произошла на стадии сидинга
        db.session.rollback()
        return False