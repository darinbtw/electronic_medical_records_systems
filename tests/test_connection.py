import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import db

try:
    with db.get_cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as count FROM patients")
        result = cursor.fetchone()
        print(f"Подключение работает! Пациентов в базе: {result['count']}")
except Exception as e:
    print(f"Ошибка: {e}")
