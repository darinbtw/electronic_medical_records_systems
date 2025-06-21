# === src/database/connection.py ===
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
import os
import sys

# Добавляем корневую папку проекта в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

try:
    from src.config import Config
    config = Config()
except ImportError:
    # Если не удается импортировать Config, используем прямую загрузку .env
    from dotenv import load_dotenv
    load_dotenv()
    
    class SimpleConfig:
        DB_HOST = os.getenv('DB_HOST')
        DB_PORT = os.getenv('DB_PORT')
        DB_NAME = os.getenv('DB_NAME')
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
    
    config = SimpleConfig()

class DatabaseConnection:
    def __init__(self):
        self.connection_params = {
            'host': config.DB_HOST,
            'port': config.DB_PORT,
            'database': config.DB_NAME,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD
        }
        
        # Настройка логирования
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для подключения к БД"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Контекстный менеджер для курсора БД"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
            finally:
                cursor.close()
    
    def test_connection(self) -> bool:
        """Тест подключения к БД"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_connection_info(self):
        """Информация о подключении для отладки"""
        return {
            'host': self.connection_params['host'],
            'port': self.connection_params['port'],
            'database': self.connection_params['database'],
            'user': self.connection_params['user']
        }

# Синглтон для подключения
db = DatabaseConnection()

# Тестирование при прямом запуске
if __name__ == "__main__":
    print("🔍 Тестирование подключения к базе данных...")
    print(f"📋 Параметры подключения: {db.get_connection_info()}")
    
    try:
        if db.test_connection():
            print("✅ Подключение к базе данных успешно!")
            
            # Дополнительная проверка таблиц
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                
                if tables:
                    print(f"✅ Найдено таблиц: {len(tables)}")
                    for table in tables:
                        print(f"   - {table['table_name']}")
                else:
                    print("⚠️  Таблицы не найдены. Возможно, нужно выполнить миграции.")
        else:
            print("❌ Не удалось подключиться к базе данных!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n🔧 Возможные причины:")
        print("1. PostgreSQL не запущен")
        print("2. Неверные данные в .env файле")
        print("3. База данных не создана")
        print("4. Пользователь не имеет прав доступа")