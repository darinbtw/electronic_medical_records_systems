import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging
import os
import sys

# Устанавливаем UTF-8 для всей системы
if sys.platform.startswith('win'):
    # Для Windows устанавливаем кодовую страницу UTF-8
    os.system('chcp 65001 > nul')

# Устанавливаем переменные окружения для UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

# Добавляем корневую папку проекта в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

try:
    from src.config import Config
    config = Config()
except ImportError:
    from dotenv import load_dotenv
    load_dotenv()
    
    class SimpleConfig:
        DB_HOST = os.getenv('DB_HOST')
        DB_PORT = os.getenv('DB_PORT')
        DB_NAME = os.getenv('DB_NAME')
        DB_USER = os.getenv('DB_USER')
        DB_PASSWORD = os.getenv('DB_PASSWORD')
    
    config = SimpleConfig()

# Импортируем TDE только если включен
TDE_ENABLED = os.getenv('TDE_ENABLED', 'False').lower() == 'true'

if TDE_ENABLED:
    try:
        from src.security.tde import TDEDatabaseConnection, TDEManager
        print("🔒 TDE модуль загружен")
    except ImportError as e:
        print(f"⚠️ TDE недоступен: {e}")
        TDE_ENABLED = False


class DatabaseConnection:
    def __init__(self):
        # КРИТИЧНО: Правильные параметры подключения для UTF-8
        self.connection_params = {
            'host': config.DB_HOST,
            'port': int(config.DB_PORT) if config.DB_PORT else 5432,
            'database': config.DB_NAME,
            'user': config.DB_USER,
            'password': config.DB_PASSWORD or '',
            # ОСНОВНЫЕ UTF-8 НАСТРОЙКИ
            'client_encoding': 'UTF8',
            'options': '-c client_encoding=UTF8 -c timezone=UTC'
        }
        
        # Настройка логирования с UTF-8
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Устанавливаем кодировку для логгера
        for handler in logging.root.handlers:
            if hasattr(handler, 'stream') and hasattr(handler.stream, 'reconfigure'):
                try:
                    handler.stream.reconfigure(encoding='utf-8')
                except:
                    pass
        
        self.logger = logging.getLogger(__name__)
        
        # Инициализация TDE если включен
        if TDE_ENABLED:
            self.tde_connection = TDEDatabaseConnection(self.connection_params)
            self.tde_manager = TDEManager()
            self.logger.info("🔒 TDE активирован для базы данных")
        else:
            self.tde_connection = None
            self.tde_manager = None
            self.logger.info("📖 TDE отключен, используется обычное подключение")
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для подключения к БД с UTF-8"""
        if TDE_ENABLED and self.tde_connection:
            # Используем TDE подключение
            with self.tde_connection.get_connection() as conn:
                yield conn
        else:
            # Обычное подключение с UTF-8
            conn = None
            try:
                conn = psycopg2.connect(**self.connection_params)
                
                # КРИТИЧНО: Дополнительная настройка UTF-8 после подключения
                with conn.cursor() as cursor:
                    cursor.execute("SET client_encoding = 'UTF8'")
                    cursor.execute("SET standard_conforming_strings = on")
                    cursor.execute("SET timezone = 'UTC'")
                
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
        """Контекстный менеджер для курсора БД с UTF-8"""
        if TDE_ENABLED and self.tde_connection:
            # Используем TDE курсор
            with self.tde_connection.get_cursor(cursor_factory) as cursor:
                yield cursor
        else:
            # Обычный курсор с UTF-8
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=cursor_factory)
                try:
                    yield cursor
                finally:
                    cursor.close()
    
    def test_connection(self) -> bool:
        """Тест подключения к БД с проверкой UTF-8"""
        try:
            with self.get_cursor() as cursor:
                # Базовый тест подключения
                cursor.execute("SELECT 1 as test")
                
                # Тест UTF-8 с кириллицей
                test_text = "Тест кириллицы: привет мир! 🏥"
                cursor.execute("SELECT %s as test_utf8", (test_text,))
                result = cursor.fetchone()
                
                if result and result['test_utf8'] == test_text:
                    self.logger.info("✅ Подключение и UTF-8 работают корректно")
                    return True
                else:
                    self.logger.error("❌ Проблема с UTF-8 кодировкой")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    def get_connection_info(self):
        """Информация о подключении для отладки"""
        info = {
            'host': self.connection_params['host'],
            'port': self.connection_params['port'],
            'database': self.connection_params['database'],
            'user': self.connection_params['user'],
            'client_encoding': self.connection_params['client_encoding'],
            'tde_enabled': TDE_ENABLED
        }
        
        # Дополнительная информация о кодировке
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SHOW client_encoding")
                info['actual_encoding'] = cursor.fetchone()[0]
                
                cursor.execute("SHOW server_encoding")
                info['server_encoding'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT version()")
                info['postgres_version'] = cursor.fetchone()[0]
                
        except Exception as e:
            info['encoding_error'] = str(e)
        
        if TDE_ENABLED and self.tde_manager:
            info['tde_info'] = self.tde_manager.get_encryption_info()
        
        return info
    
    def fix_encoding_if_needed(self):
        """Автоматическое исправление проблем с кодировкой"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Проверяем текущую кодировку
                cursor.execute("SHOW client_encoding")
                current_encoding = cursor.fetchone()[0]
                
                if current_encoding != 'UTF8':
                    self.logger.warning(f"Неправильная кодировка: {current_encoding}, исправляем...")
                    
                    # Устанавливаем UTF-8
                    cursor.execute("SET client_encoding = 'UTF8'")
                    conn.commit()
                    
                    self.logger.info("✅ Кодировка исправлена на UTF-8")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Ошибка исправления кодировки: {e}")
            return False
    
    def enable_tde_for_existing_data(self):
        """
        Миграция существующих данных под TDE
        ВНИМАНИЕ: Эта операция изменит все существующие данные!
        """
        if not TDE_ENABLED or not self.tde_manager:
            raise ValueError("TDE не активирован")
        
        self.logger.warning("🚨 НАЧИНАЕТСЯ МИГРАЦИЯ ДАННЫХ ПОД TDE")
        
        # Сначала обновляем структуру БД
        from src.security.tde import upgrade_database_for_tde
        upgrade_database_for_tde()
        
        # Затем мигрируем данные
        tables_to_migrate = ['patients', 'doctors', 'medical_records', 'prescriptions']
        
        for table_name in tables_to_migrate:
            self._migrate_table_data(table_name)
        
        self.logger.info("✅ Миграция данных под TDE завершена")
    
    def _migrate_table_data(self, table_name: str):
        """Миграция данных конкретной таблицы"""
        encrypted_fields = self.tde_manager.encrypted_fields.get(table_name, [])
        
        if not encrypted_fields:
            self.logger.info(f"Таблица {table_name}: нет полей для шифрования")
            return
        
        self.logger.info(f"Миграция таблицы {table_name}: {encrypted_fields}")
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                # Получаем все записи
                cursor.execute(f"SELECT * FROM {table_name}")
                records = cursor.fetchall()
                
                self.logger.info(f"Найдено {len(records)} записей в {table_name}")
                
                migrated_count = 0
                
                for record in records:
                    record_dict = dict(record)
                    record_id = record_dict.get('id')
                    
                    # Проверяем, нужна ли миграция
                    needs_migration = False
                    for field in encrypted_fields:
                        iv_field = f"{field}_iv"
                        if field in record_dict and record_dict[field] and not record_dict.get(iv_field):
                            needs_migration = True
                            break
                    
                    if not needs_migration:
                        continue
                    
                    # Шифруем поля
                    update_fields = []
                    update_values = []
                    
                    for field in encrypted_fields:
                        if field in record_dict and record_dict[field]:
                            value = str(record_dict[field])
                            
                            # Проверяем, не зашифровано ли уже
                            iv_field = f"{field}_iv"
                            if record_dict.get(iv_field):
                                continue  # Уже зашифровано
                            
                            ciphertext, iv = self.tde_manager.encrypt_field(table_name, field, value)
                            
                            update_fields.append(f"{field} = %s, {field}_iv = %s")
                            update_values.extend([ciphertext, iv])
                    
                    if update_fields:
                        # Обновляем запись
                        update_query = f"""
                            UPDATE {table_name} 
                            SET {', '.join(update_fields)}
                            WHERE id = %s
                        """
                        update_values.append(record_id)
                        
                        cursor.execute(update_query, update_values)
                        migrated_count += 1
                
                conn.commit()
                self.logger.info(f"✅ Таблица {table_name}: мигрировано {migrated_count} записей")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка миграции {table_name}: {e}")
            raise


# Синглтон для подключения
db = DatabaseConnection()

# Тестирование при прямом запуске
if __name__ == "__main__":
    print("🔧 Тестирование подключения к базе данных с UTF-8...")
    
    # Проверяем кодировку Python
    print(f"📊 Кодировка Python: {sys.getdefaultencoding()}")
    print(f"📊 Кодировка stdout: {sys.stdout.encoding}")
    print(f"📊 Платформа: {sys.platform}")
    
    connection_info = db.get_connection_info()
    print(f"\n📊 Параметры подключения:")
    for key, value in connection_info.items():
        if key not in ['tde_info', 'postgres_version']:
            print(f"  {key}: {value}")
    
    if connection_info.get('postgres_version'):
        print(f"\n📊 PostgreSQL: {connection_info['postgres_version'][:50]}...")
    
    if connection_info.get('tde_info'):
        print("\n🔒 Информация TDE:")
        for key, value in connection_info['tde_info'].items():
            print(f"  {key}: {value}")
    
    try:
        print(f"\n🧪 Тест подключения с UTF-8...")
        if db.test_connection():
            print("✅ УСПЕХ: Подключение к базе данных работает с UTF-8!")
            
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
                    print(f"\n📋 Найдено таблиц: {len(tables)}")
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) as count FROM {table['table_name']}")
                        count = cursor.fetchone()['count']
                        print(f"   - {table['table_name']}: {count} записей")
                        
                        # Тест кириллицы если есть данные
                        if count > 0 and table['table_name'] in ['patients', 'doctors']:
                            cursor.execute(f"SELECT * FROM {table['table_name']} LIMIT 1")
                            sample = cursor.fetchone()
                            if sample and 'first_name' in sample:
                                print(f"     Пример: {sample['first_name']} {sample.get('last_name', '')}")
                    
                    # Тест TDE если включен
                    if TDE_ENABLED and db.tde_manager:
                        print("\n🔒 Тест TDE с UTF-8...")
                        
                        # Создаем тестовую запись с кириллицей
                        test_patient = {
                            'first_name': 'Тест',
                            'last_name': 'Тестович',
                            'middle_name': 'Тестовый',
                            'birth_date': '1990-01-01',
                            'gender': 'M',
                            'phone': '+7 999 000-00-00',
                            'email': 'тест@example.ru',
                            'address': 'г. Москва, ул. Тестовая, д. 1, кв. 2'
                        }
                        
                        try:
                            # Вставляем с автоматическим шифрованием
                            cursor.execute("""
                                INSERT INTO patients 
                                (first_name, last_name, middle_name, birth_date, gender, phone, email, address)
                                VALUES (%(first_name)s, %(last_name)s, %(middle_name)s, %(birth_date)s, 
                                        %(gender)s, %(phone)s, %(email)s, %(address)s)
                                RETURNING id
                            """, test_patient)
                            
                            test_id = cursor.fetchone()['id']
                            print(f"✅ TDE+UTF8 тест: запись создана с ID {test_id}")
                            
                            # Читаем с автоматической расшифровкой
                            cursor.execute("SELECT * FROM patients WHERE id = %s", (test_id,))
                            result = cursor.fetchone()
                            
                            if result:
                                print(f"✅ TDE+UTF8 тест: запись прочитана и расшифрована")
                                print(f"   Имя: {result.get('first_name', 'N/A')}")
                                print(f"   Телефон: {result.get('phone', 'N/A')}")
                                print(f"   Email: {result.get('email', 'N/A')}")
                                print(f"   Адрес: {result.get('address', 'N/A')}")
                                
                                # Проверяем, что кириллица не повреждена
                                if (result['first_name'] == test_patient['first_name'] and 
                                    result['phone'] == test_patient['phone'] and
                                    result['email'] == test_patient['email'] and
                                    result['address'] == test_patient['address']):
                                    print("✅ TDE+UTF8 работает корректно!")
                                else:
                                    print("❌ TDE+UTF8: данные не совпадают")
                                    print(f"   Ожидаемый email: {test_patient['email']}")
                                    print(f"   Полученный email: {result['email']}")
                            
                            # Удаляем тестовую запись
                            cursor.execute("DELETE FROM patients WHERE id = %s", (test_id,))
                            print("🧹 Тестовая запись удалена")
                            
                        except Exception as e:
                            print(f"❌ Ошибка TDE+UTF8 теста: {e}")
                
                else:
                    print("\n⚠️  Таблицы не найдены. Создайте их:")
                    print("python fix_utf8_database.py")
        else:
            print("❌ ОШИБКА: Не удалось подключиться к базе данных!")
            print("\n🔧 Попробуйте запустить:")
            print("python fix_utf8_database.py")
            
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        print("\nВозможные причины:")
        print("1. PostgreSQL не запущен")
        print("2. Неверные данные в .env файле")
        print("3. База данных создана с неправильной кодировкой")
        print("4. Проблемы с настройкой кодировки клиента")
        print("\n🔧 Решение:")
        print("python fix_utf8_database.py")