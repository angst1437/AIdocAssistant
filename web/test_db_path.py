import os
import sqlite3
import sys

db_dir = r'C:\pyProj\nir-assistant-ver2\instance'
# Используем r'' для "raw string", чтобы избежать проблем со слешами,
# хотя '/' обычно работает на Windows в Python.
db_file_path = os.path.join(db_dir, 'app.db')
db_uri = f'sqlite:///{db_file_path}'  # Строим URI для sqlite3

print(f"Python Version: {sys.version}")
print(f"Trying to access directory: {db_dir}")
print(f"Directory exists: {os.path.exists(db_dir)}")
print(f"Is directory writable? (Attempting to create dummy file)")

dummy_file_path = os.path.join(db_dir, 'dummy_test.txt')
can_write = False
try:
    with open(dummy_file_path, 'w') as f:
        f.write('test')
    print(f"  Successfully created/wrote to {dummy_file_path}")
    can_write = True
    os.remove(dummy_file_path)  # Удаляем тестовый файл
    print(f"  Successfully removed dummy file.")
except Exception as e:
    print(f"  ERROR writing to directory: {e}")

if can_write:
    print(f"\nTrying to connect using sqlite3 directly to: {db_file_path}")
    conn = None
    try:
        conn = sqlite3.connect(db_file_path)
        # Эта команда ДОЛЖНА создать файл, если его нет и есть права
        print(f"  Successfully connected/created database file using sqlite3.")

        # Проверим, создался ли файл
        if os.path.exists(db_file_path):
            print(f"  Confirmed: Database file '{db_file_path}' now exists.")
        else:
            print(f"  WARNING: Connection succeeded but file still doesn't exist?")

    except sqlite3.OperationalError as e:
        print(f"  ERROR connecting with sqlite3: {e}")
    except Exception as e:
        print(f"  UNEXPECTED ERROR connecting with sqlite3: {e}")
    finally:
        if conn:
            conn.close()
            print("  Connection closed.")
else:
    print("\nSkipping sqlite3 connection test because directory write failed.")