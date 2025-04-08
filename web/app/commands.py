import click
from flask.cli import with_appcontext
from . import db

# Импортируем функции из папки scripts (в корне проекта)
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
scripts_path = os.path.join(project_root, 'scripts')
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

try:
    from reset_database import run_reset as reset_db_script
    from seed_templates import run_seed as seed_templates_script
    from seed_users import run_seed as seed_users_script
    scripts_imported = True
    print(f"--- web/app/commands.py: Скрипты из '{scripts_path}' успешно импортированы ---")
except ImportError as e:
    click.echo(f"ПРЕДУПРЕЖДЕНИЕ: Не удалось импортировать скрипты из папки '{scripts_path}': {e}", err=True)
    click.echo("Команды reset-dev-db и seed-db могут быть недоступны.", err=True)
    scripts_imported = False

    def reset_db_script(): click.echo("Скрипт сброса недоступен.", err=True); return False
    def seed_templates_script(): click.echo("Скрипт сидинга шаблонов недоступен.", err=True); return False
    def seed_users_script(): click.echo("Скрипт сидинга пользователей недоступен.", err=True); return False


# --- Определяем команды ---
@click.command("reset-dev-db") # Имя команды для вызова из CLI
@with_appcontext # Нужен для доступа к current_app и db
def reset_dev_db_command():
    """Полностью пересоздает базу данных для разработки (УДАЛЯЕТ ВСЕ ДАННЫЕ!)."""
    if not scripts_imported:
         click.echo("Выполнение команды невозможно: скрипты не были импортированы.", err=True)
         return

    click.echo("Запуск полного сброса и сидинга базы данных...")
    # reset_db_script может использовать current_app, который дает with_appcontext
    if not reset_db_script():
         click.echo("Ошибка на шаге сброса БД. Прерывание.", err=True)
         return
    try:
         # seed скрипты используют db, доступный через контекст
         templates_ok = seed_templates_script()
         users_ok = seed_users_script()
         if templates_ok and users_ok:
             db.session.commit()
             click.echo("База данных успешно заполнена!")
             click.echo("-" * 40)
             click.echo("Скрипт reset-dev-db успешно завершен.")
         else:
             # Если какой-то сидинг вернул False явно
             if not templates_ok: click.echo("Сидинг шаблонов не удался.", err=True)
             if not users_ok: click.echo("Сидинг пользователей не удался.", err=True)
             raise Exception("Одна из операций сидинга не удалась.")
    except Exception as e:
         db.session.rollback()
         click.echo(f"Ошибка во время заполнения базы данных: {e}", err=True)
         click.echo("Изменения сидинга отменены.", err=True)


@click.command("seed-db") # Имя команды
@with_appcontext
def seed_db_command():
    """Запускает сидинг шаблонов и пользователей (без сброса БД)."""
    if not scripts_imported:
         click.echo("Выполнение команды невозможно: скрипты не были импортированы.", err=True)
         return

    click.echo("Запуск сидинга базы данных...")
    try:
         templates_ok = seed_templates_script()
         users_ok = seed_users_script()
         if templates_ok and users_ok:
             db.session.commit()
             click.echo("Сидинг успешно завершен.")
         else:
             if not templates_ok: click.echo("Сидинг шаблонов не удался.", err=True)
             if not users_ok: click.echo("Сидинг пользователей не удался.", err=True)
             raise Exception("Одна из операций сидинга не удалась.")
    except Exception as e:
         db.session.rollback()
         click.echo(f"Ошибка во время сидинга: {e}", err=True)
