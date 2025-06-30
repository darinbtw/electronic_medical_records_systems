# Создайте файл: src/security/tde.py

import os
import base64
import logging
from typing import Optional, Dict, Any, List
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

class TDEManager:
    """
    Transparent Data Encryption Manager
    Автоматическое шифрование чувствительных данных
    """
    
    def __init__(self):
        self.backend = default_backend()
        self.logger = logging.getLogger(__name__)
        
        # Поля, которые должны шифроваться автоматически
        self.encrypted_fields = {
            'patients': ['phone', 'email', 'address'],
            'doctors': ['phone', 'email'],
            'medical_records': ['diagnosis_encrypted', 'complaints', 'examination_results'],
            'prescriptions': ['notes']
        }
        
        # Загружаем или создаем главный ключ
        self.master_key = self._load_or_create_master_key()
        
        # Создаем производные ключи для разных таблиц
        self.table_keys = self._derive_table_keys()
    
    def _load_or_create_master_key(self) -> bytes:
        """Загрузка или создание главного ключа TDE"""
        key_file = os.getenv('TDE_MASTER_KEY_FILE', '.tde_master_key')
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Создаем новый главный ключ
            master_key = os.urandom(32)  # 256 бит
            
            with open(key_file, 'wb') as f:
                f.write(master_key)
            
            # Устанавливаем права доступа только для владельца
            os.chmod(key_file, 0o600)
            self.logger.info("Создан новый главный ключ TDE")
            
            return master_key
    
    def _derive_table_keys(self) -> Dict[str, bytes]:
        """Создание производных ключей для каждой таблицы"""
        table_keys = {}
        
        for table_name in self.encrypted_fields.keys():
            # Используем PBKDF2 для создания уникального ключа для каждой таблицы
            salt = table_name.encode('utf-8') + b'_tde_salt_2024'
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            
            table_keys[table_name] = kdf.derive(self.master_key)
        
        return table_keys
    
    def encrypt_field(self, table_name: str, field_name: str, value: str) -> tuple[bytes, bytes]:
        """Шифрование отдельного поля"""
        if not value:
            return None, None
        
        # Проверяем, нужно ли шифровать это поле
        if field_name not in self.encrypted_fields.get(table_name, []):
            # Если поле не в списке для шифрования, возвращаем как есть
            return value.encode('utf-8'), b''
        
        try:
            # Генерируем уникальный IV для каждого значения
            iv = os.urandom(16)
            
            # Получаем ключ для таблицы
            table_key = self.table_keys.get(table_name)
            if not table_key:
                raise ValueError(f"Нет ключа для таблицы {table_name}")
            
            # Создаем шифр
            cipher = Cipher(algorithms.AES(table_key), modes.CBC(iv), backend=self.backend)
            encryptor = cipher.encryptor()
            
            # Добавляем padding
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(value.encode('utf-8')) + padder.finalize()
            
            # Шифруем
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            self.logger.debug(f"Поле {table_name}.{field_name} зашифровано")
            return ciphertext, iv
            
        except Exception as e:
            self.logger.error(f"Ошибка шифрования {table_name}.{field_name}: {e}")
            raise
    
    def decrypt_field(self, table_name: str, field_name: str, ciphertext: bytes, iv: bytes) -> str:
        """Расшифровка отдельного поля"""
        if not ciphertext or not iv:
            return ""
        
        # Если поле не должно шифроваться, возвращаем как строку
        if field_name not in self.encrypted_fields.get(table_name, []):
            return ciphertext.decode('utf-8') if isinstance(ciphertext, bytes) else str(ciphertext)
        
        try:
            # Получаем ключ для таблицы
            table_key = self.table_keys.get(table_name)
            if not table_key:
                raise ValueError(f"Нет ключа для таблицы {table_name}")
            
            # Создаем дешифратор
            cipher = Cipher(algorithms.AES(table_key), modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            
            # Расшифровываем
            padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Убираем padding
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
            
            result = plaintext.decode('utf-8')
            self.logger.debug(f"Поле {table_name}.{field_name} расшифровано")
            return result
            
        except Exception as e:
            self.logger.error(f"Ошибка расшифровки {table_name}.{field_name}: {e}")
            return f"[ОШИБКА РАСШИФРОВКИ: {str(e)[:50]}]"
    
    def encrypt_record(self, table_name: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Автоматическое шифрование записи перед вставкой в БД"""
        encrypted_record = record_data.copy()
        
        # Получаем список полей для шифрования
        fields_to_encrypt = self.encrypted_fields.get(table_name, [])
        
        for field_name in fields_to_encrypt:
            if field_name in encrypted_record and encrypted_record[field_name]:
                value = str(encrypted_record[field_name])
                
                # Шифруем значение
                ciphertext, iv = self.encrypt_field(table_name, field_name, value)
                
                # Заменяем в записи на зашифрованные данные
                encrypted_record[field_name] = ciphertext
                encrypted_record[f"{field_name}_iv"] = iv
                
                self.logger.debug(f"Автошифрование: {table_name}.{field_name}")
        
        return encrypted_record
    
    def decrypt_record(self, table_name: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Автоматическая расшифровка записи после извлечения из БД"""
        decrypted_record = record_data.copy()
        
        # Получаем список полей для расшифровки
        fields_to_decrypt = self.encrypted_fields.get(table_name, [])
        
        for field_name in fields_to_decrypt:
            ciphertext_field = field_name
            iv_field = f"{field_name}_iv"
            
            if ciphertext_field in decrypted_record and iv_field in decrypted_record:
                ciphertext = decrypted_record[ciphertext_field]
                iv = decrypted_record[iv_field]
                
                if ciphertext and iv:
                    # Расшифровываем
                    plaintext = self.decrypt_field(table_name, field_name, ciphertext, iv)
                    decrypted_record[field_name] = plaintext
                    
                    # Удаляем служебные поля из результата
                    if f"{field_name}_iv" in decrypted_record:
                        del decrypted_record[f"{field_name}_iv"]
                    
                    self.logger.debug(f"Авторасшифровка: {table_name}.{field_name}")
        
        return decrypted_record
    
    def get_encryption_info(self) -> Dict[str, Any]:
        """Получение информации о настройках шифрования"""
        return {
            'algorithm': 'AES-256-CBC',
            'key_derivation': 'PBKDF2-HMAC-SHA256',
            'iterations': 100000,
            'encrypted_tables': list(self.encrypted_fields.keys()),
            'total_encrypted_fields': sum(len(fields) for fields in self.encrypted_fields.values()),
            'master_key_exists': os.path.exists(os.getenv('TDE_MASTER_KEY_FILE', '.tde_master_key'))
        }


class TDEDatabaseConnection:
    """
    Обертка для подключения к БД с автоматическим TDE
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        self.connection_params = connection_params
        self.tde = TDEManager()
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для подключения с TDE"""
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
        """Контекстный менеджер для курсора с TDE"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield TDECursor(cursor, self.tde)
            finally:
                cursor.close()


class TDECursor:
    """
    Обертка для курсора с автоматическим шифрованием/расшифровкой
    """
    
    def __init__(self, cursor, tde_manager: TDEManager):
        self.cursor = cursor
        self.tde = tde_manager
        self.logger = logging.getLogger(__name__)
        
        # Паттерны для определения операций
        self.insert_patterns = ['INSERT INTO', 'insert into']
        self.select_patterns = ['SELECT', 'select']
        self.update_patterns = ['UPDATE', 'update']
    
    def execute(self, query: str, params=None):
        """Выполнение запроса с автоматическим TDE"""
        
        # Определяем тип операции и таблицу
        operation_info = self._parse_query(query)
        
        if operation_info['operation'] == 'INSERT' and operation_info['table']:
            # При вставке автоматически шифруем данные
            if params and isinstance(params, dict):
                encrypted_params = self.tde.encrypt_record(operation_info['table'], params)
                return self.cursor.execute(query, encrypted_params)
            elif params and isinstance(params, (list, tuple)):
                # Для позиционных параметров - без автошифрования
                return self.cursor.execute(query, params)
        
        # Для всех остальных операций - обычное выполнение
        return self.cursor.execute(query, params)
    
    def fetchone(self):
        """Получение одной записи с автоматической расшифровкой"""
        result = self.cursor.fetchone()
        if result:
            # Пытаемся определить таблицу из последнего запроса
            table_name = self._guess_table_from_result(result)
            if table_name:
                return self.tde.decrypt_record(table_name, dict(result))
        return result
    
    def fetchall(self):
        """Получение всех записей с автоматической расшифровкой"""
        results = self.cursor.fetchall()
        if results:
            # Пытаемся определить таблицу
            table_name = self._guess_table_from_result(results[0])
            if table_name:
                return [self.tde.decrypt_record(table_name, dict(row)) for row in results]
        return results
    
    def fetchmany(self, size=None):
        """Получение нескольких записей с автоматической расшифровкой"""
        results = self.cursor.fetchmany(size)
        if results:
            table_name = self._guess_table_from_result(results[0])
            if table_name:
                return [self.tde.decrypt_record(table_name, dict(row)) for row in results]
        return results
    
    def _parse_query(self, query: str) -> Dict[str, str]:
        """Парсинг запроса для определения операции и таблицы"""
        query_upper = query.upper().strip()
        
        operation = None
        table = None
        
        # Определяем операцию
        if any(pattern.upper() in query_upper for pattern in self.insert_patterns):
            operation = 'INSERT'
            # Ищем таблицу после INSERT INTO
            import re
            match = re.search(r'INSERT\s+INTO\s+(\w+)', query_upper)
            if match:
                table = match.group(1).lower()
        
        elif any(pattern.upper() in query_upper for pattern in self.select_patterns):
            operation = 'SELECT'
            # Ищем таблицу после FROM
            import re
            match = re.search(r'FROM\s+(\w+)', query_upper)
            if match:
                table = match.group(1).lower()
        
        elif any(pattern.upper() in query_upper for pattern in self.update_patterns):
            operation = 'UPDATE'
            # Ищем таблицу после UPDATE
            import re
            match = re.search(r'UPDATE\s+(\w+)', query_upper)
            if match:
                table = match.group(1).lower()
        
        return {'operation': operation, 'table': table}
    
    def _guess_table_from_result(self, result_row) -> Optional[str]:
        """Попытка определить таблицу по структуре результата"""
        if not result_row:
            return None
        
        columns = set(result_row.keys()) if hasattr(result_row, 'keys') else set()
        
        # Проверяем характерные столбцы для каждой таблицы
        table_signatures = {
            'patients': {'first_name', 'last_name', 'birth_date', 'gender'},
            'doctors': {'specialization', 'license_number'},
            'appointments': {'appointment_date', 'status', 'patient_id', 'doctor_id'},
            'medical_records': {'diagnosis_encrypted', 'complaints', 'examination_results'},
            'prescriptions': {'medication_name', 'dosage', 'frequency'}
        }
        
        for table_name, signature in table_signatures.items():
            if signature.issubset(columns):
                return table_name
        
        return None
    
    def __getattr__(self, name):
        """Проксирование всех остальных методов к оригинальному курсору"""
        return getattr(self.cursor, name)


# Функция для обновления структуры БД под TDE
def upgrade_database_for_tde():
    """
    Обновление структуры базы данных для поддержки TDE
    Добавляет столбцы _iv для зашифрованных полей
    """
    
    from src.database.connection import db
    
    tde = TDEManager()
    
    # SQL команды для добавления столбцов IV
    alter_commands = []
    
    for table_name, fields in tde.encrypted_fields.items():
        for field_name in fields:
            # Добавляем столбец для IV, если его еще нет
            alter_commands.append(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_name = '{field_name}_iv'
                    ) THEN
                        ALTER TABLE {table_name} ADD COLUMN {field_name}_iv BYTEA;
                    END IF;
                END $$;
            """)
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            print("🔒 Обновление структуры БД для TDE...")
            
            for command in alter_commands:
                cursor.execute(command)
                print(f"✅ Выполнено: {command.strip()[:60]}...")
            
            conn.commit()
            print("✅ Структура БД обновлена для поддержки TDE")
            
            # Создаем индексы для зашифрованных полей
            print("📇 Создание индексов для TDE...")
            
            index_commands = [
                "CREATE INDEX IF NOT EXISTS idx_patients_phone_encrypted ON patients(phone) WHERE phone IS NOT NULL;",
                "CREATE INDEX IF NOT EXISTS idx_patients_email_encrypted ON patients(email) WHERE email IS NOT NULL;",
                "CREATE INDEX IF NOT EXISTS idx_doctors_email_encrypted ON doctors(email) WHERE email IS NOT NULL;",
            ]
            
            for command in index_commands:
                try:
                    cursor.execute(command)
                    print(f"✅ Индекс создан")
                except Exception as e:
                    print(f"⚠️ Индекс не создан: {e}")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Ошибка обновления БД: {e}")
        raise


# Функция для тестирования TDE
def test_tde():
    """Тестирование TDE функциональности"""
    
    tde = TDEManager()
    
    print("🧪 ТЕСТИРОВАНИЕ TDE")
    print("=" * 50)
    
    # Тест 1: Шифрование/расшифровка отдельного поля
    test_data = "Тест данных для шифрования 🔒"
    
    ciphertext, iv = tde.encrypt_field('patients', 'phone', test_data)
    decrypted = tde.decrypt_field('patients', 'phone', ciphertext, iv)
    
    print(f"Исходные данные: {test_data}")
    print(f"Зашифровано: {base64.b64encode(ciphertext).decode()[:50]}...")
    print(f"Расшифровано: {decrypted}")
    print(f"Совпадение: {'✅' if test_data == decrypted else '❌'}")
    
    # Тест 2: Шифрование записи
    print(f"\n📝 Тест шифрования записи:")
    
    patient_record = {
        'first_name': 'Иван',
        'last_name': 'Иванов', 
        'phone': '+7 999 123-45-67',
        'email': 'ivan@example.com',
        'address': 'г. Москва, ул. Тестовая, д. 1'
    }
    
    encrypted_record = tde.encrypt_record('patients', patient_record)
    decrypted_record = tde.decrypt_record('patients', encrypted_record)
    
    print(f"Исходная запись: {patient_record}")
    print(f"Расшифрованная: {decrypted_record}")
    
    # Проверяем, что незашифрованные поля остались без изменений
    assert patient_record['first_name'] == decrypted_record['first_name']
    assert patient_record['last_name'] == decrypted_record['last_name']
    
    # Проверяем, что зашифрованные поля расшифровались правильно
    assert patient_record['phone'] == decrypted_record['phone']
    assert patient_record['email'] == decrypted_record['email']
    assert patient_record['address'] == decrypted_record['address']
    
    print("✅ Все тесты TDE пройдены!")
    
    # Информация о шифровании
    print(f"\n📊 Информация о TDE:")
    info = tde.get_encryption_info()
    for key, value in info.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    test_tde()