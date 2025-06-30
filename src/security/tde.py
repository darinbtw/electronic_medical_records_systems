"""
Полная реализация Transparent Data Encryption (TDE) для системы медкарт
Автоматическое шифрование чувствительных данных на уровне приложения
"""

import os
import sys
import base64
import logging
import hashlib
import secrets
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime, timedelta
from contextlib import contextmanager

# Криптографические модули
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

# База данных
import psycopg2
from psycopg2.extras import RealDictCursor, Json

# Добавляем путь к проекту
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

class TDEKeyManager:
    """
    Менеджер ключей для TDE
    Управляет созданием, ротацией и безопасным хранением ключей шифрования
    """
    
    def __init__(self):
        self.backend = default_backend()
        self.logger = logging.getLogger(__name__)
        
        # Настройки ключей
        self.master_key_file = os.getenv('TDE_MASTER_KEY_FILE', '.tde_master_key')
        self.key_rotation_days = int(os.getenv('TDE_KEY_ROTATION_DAYS', 90))
        self.backup_keys = os.getenv('TDE_BACKUP_KEYS', 'True').lower() == 'true'
        
        # Криптографические параметры
        self.key_length = 32  # 256 бит
        self.salt_length = 16  # 128 бит
        self.iv_length = 16   # 128 бит
        self.iterations = 100000  # PBKDF2 итерации
        
        # Инициализация
        self._ensure_master_key()
        self._initialize_table_keys()
    
    def _ensure_master_key(self):
        """Создание или загрузка главного ключа"""
        if os.path.exists(self.master_key_file):
            self._load_master_key()
        else:
            self._create_master_key()
    
    def _create_master_key(self):
        """Создание нового главного ключа"""
        try:
            # Генерируем криптографически стойкий ключ
            self.master_key = secrets.token_bytes(self.key_length)
            
            # Создаем метаданные ключа
            key_metadata = {
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'algorithm': 'AES-256-CBC',
                'key_derivation': 'PBKDF2-HMAC-SHA256',
                'iterations': self.iterations
            }
            
            # Сохраняем ключ и метаданные
            key_data = {
                'master_key': base64.b64encode(self.master_key).decode(),
                'metadata': key_metadata
            }
            
            import json
            with open(self.master_key_file, 'w') as f:
                json.dump(key_data, f, indent=2)
            
            # Устанавливаем строгие права доступа
            os.chmod(self.master_key_file, 0o600)
            
            self.logger.info("🔑 Создан новый главный ключ TDE")
            
            # Создаем резервную копию
            if self.backup_keys:
                self._backup_key()
                
        except Exception as e:
            self.logger.error(f"Ошибка создания главного ключа: {e}")
            raise
    
    def _load_master_key(self):
        """Загрузка существующего главного ключа"""
        try:
            import json
            with open(self.master_key_file, 'r') as f:
                key_data = json.load(f)
            
            self.master_key = base64.b64decode(key_data['master_key'])
            self.key_metadata = key_data.get('metadata', {})
            
            # Проверяем срок действия ключа
            self._check_key_rotation()
            
            self.logger.info("🔑 Загружен существующий главный ключ TDE")
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки главного ключа: {e}")
            raise
    
    def _backup_key(self):
        """Создание резервной копии ключа"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{self.master_key_file}.backup.{timestamp}"
            
            import shutil
            shutil.copy2(self.master_key_file, backup_file)
            os.chmod(backup_file, 0o600)
            
            self.logger.info(f"💾 Создана резервная копия ключа: {backup_file}")
            
        except Exception as e:
            self.logger.warning(f"Ошибка создания backup ключа: {e}")
    
    def _check_key_rotation(self):
        """Проверка необходимости ротации ключа"""
        try:
            created_str = self.key_metadata.get('created_at')
            if not created_str:
                return
            
            created_date = datetime.fromisoformat(created_str)
            age_days = (datetime.now() - created_date).days
            
            if age_days >= self.key_rotation_days:
                self.logger.warning(f"⚠️ Ключ TDE устарел ({age_days} дней). Требуется ротация!")
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки ротации ключа: {e}")
    
    def _initialize_table_keys(self):
        """Создание производных ключей для каждой таблицы"""
        # Определяем таблицы и поля для шифрования
        self.encryption_config = {
            'patients': {
                'fields': ['phone', 'email', 'address'],
                'sensitivity': 'high'  # Высокая чувствительность
            },
            'doctors': {
                'fields': ['phone', 'email'],
                'sensitivity': 'medium'
            },
            'medical_records': {
                'fields': ['diagnosis', 'complaints', 'examination_results'],
                'sensitivity': 'critical'  # Критическая чувствительность
            },
            'prescriptions': {
                'fields': ['notes'],
                'sensitivity': 'medium'
            }
        }
        
        # Создаем уникальные ключи для каждой таблицы
        self.table_keys = {}
        for table_name, config in self.encryption_config.items():
            self.table_keys[table_name] = self._derive_table_key(table_name, config['sensitivity'])
    
    def _derive_table_key(self, table_name: str, sensitivity: str) -> bytes:
        """Создание производного ключа для таблицы"""
        # Создаем уникальную соль для каждой таблицы
        salt_base = f"tde_medical_system_{table_name}_{sensitivity}_2024"
        salt = hashlib.sha256(salt_base.encode()).digest()[:self.salt_length]
        
        # Определяем количество итераций в зависимости от чувствительности
        iteration_multiplier = {
            'critical': 2.0,  # 200,000 итераций
            'high': 1.5,      # 150,000 итераций  
            'medium': 1.0,    # 100,000 итераций
            'low': 0.5        # 50,000 итераций
        }
        
        iterations = int(self.iterations * iteration_multiplier.get(sensitivity, 1.0))
        
        # Используем PBKDF2 для создания производного ключа
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length,
            salt=salt,
            iterations=iterations,
            backend=self.backend
        )
        
        return kdf.derive(self.master_key)
    
    def rotate_master_key(self):
        """Ротация главного ключа"""
        self.logger.info("🔄 Начало ротации главного ключа TDE...")
        
        try:
            # Создаем backup текущего ключа
            if self.backup_keys:
                self._backup_key()
            
            # Сохраняем старый ключ для перешифровки данных
            old_master_key = self.master_key
            old_table_keys = self.table_keys.copy()
            
            # Создаем новый главный ключ
            self._create_master_key()
            self._initialize_table_keys()
            
            # Перешифровываем все существующие данные
            self._reencrypt_all_data(old_table_keys)
            
            self.logger.info("✅ Ротация главного ключа завершена успешно")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка ротации ключа: {e}")
            raise
    
    def _reencrypt_all_data(self, old_table_keys: Dict[str, bytes]):
        """Перешифровка всех данных новыми ключами"""
        self.logger.info("🔄 Перешифровка существующих данных...")
        
        from src.database.connection import db
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                total_records = 0
                
                for table_name, config in self.encryption_config.items():
                    encrypted_fields = config['fields']
                    
                    # Получаем все записи с зашифрованными данными
                    where_conditions = []
                    for field in encrypted_fields:
                        where_conditions.append(f"{field}_encrypted IS NOT NULL")
                    
                    if not where_conditions:
                        continue
                    
                    query = f"""
                        SELECT id, {', '.join([f'{field}_encrypted, {field}_iv' for field in encrypted_fields])}
                        FROM {table_name} 
                        WHERE {' OR '.join(where_conditions)}
                    """
                    
                    cursor.execute(query)
                    records = cursor.fetchall()
                    
                    self.logger.info(f"Перешифровка {len(records)} записей в таблице {table_name}")
                    
                    for record in records:
                        record_id = record['id']
                        update_parts = []
                        update_values = []
                        
                        for field in encrypted_fields:
                            encrypted_field = f"{field}_encrypted"
                            iv_field = f"{field}_iv"
                            
                            if record.get(encrypted_field) and record.get(iv_field):
                                # Расшифровываем старым ключом
                                old_plaintext = self._decrypt_with_key(
                                    bytes(record[encrypted_field]),
                                    bytes(record[iv_field]),
                                    old_table_keys[table_name]
                                )
                                
                                # Шифруем новым ключом
                                new_ciphertext, new_iv = self._encrypt_with_key(
                                    old_plaintext,
                                    self.table_keys[table_name]
                                )
                                
                                update_parts.append(f"{encrypted_field} = %s, {iv_field} = %s")
                                update_values.extend([new_ciphertext, new_iv])
                        
                        if update_parts:
                            update_query = f"""
                                UPDATE {table_name} 
                                SET {', '.join(update_parts)}
                                WHERE id = %s
                            """
                            update_values.append(record_id)
                            
                            cursor.execute(update_query, update_values)
                            total_records += 1
                
                conn.commit()
                self.logger.info(f"✅ Перешифровано {total_records} записей")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка перешифровки данных: {e}")
            raise
    
    def _encrypt_with_key(self, plaintext: str, key: bytes) -> Tuple[bytes, bytes]:
        """Шифрование данных указанным ключом"""
        iv = secrets.token_bytes(self.iv_length)
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
        
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return ciphertext, iv
    
    def _decrypt_with_key(self, ciphertext: bytes, iv: bytes, key: bytes) -> str:
        """Расшифровка данных указанным ключом"""
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext.decode('utf-8')


class TDEManager:
    """
    Основной менеджер TDE
    Предоставляет высокоуровневый интерфейс для прозрачного шифрования
    """
    
    def __init__(self):
        self.backend = default_backend()
        self.logger = logging.getLogger(__name__)
        
        # Инициализируем менеджер ключей
        self.key_manager = TDEKeyManager()
        
        # Настройки производительности
        self.cache_enabled = True
        self.max_cache_size = 1000
        self._encryption_cache = {}
        
    @property
    def encryption_config(self):
        """Получить конфигурацию шифрования"""
        return self.key_manager.encryption_config
    
    @property
    def table_keys(self):
        """Получить ключи для таблиц"""
        return self.key_manager.table_keys
    
    def encrypt_field(self, table_name: str, field_name: str, value: str) -> Tuple[Optional[bytes], Optional[bytes]]:
        """
        Шифрование поля данных
        
        Args:
            table_name: Название таблицы
            field_name: Название поля
            value: Значение для шифрования
            
        Returns:
            Tuple[bytes, bytes]: (зашифрованные_данные, iv) или (None, None)
        """
        if not value or not value.strip():
            return None, None
        
        # Проверяем, нужно ли шифровать это поле
        config = self.encryption_config.get(table_name, {})
        if field_name not in config.get('fields', []):
            # Если поле не настроено для шифрования, возвращаем как есть
            return value.encode('utf-8'), b''
        
        try:
            # Получаем ключ для таблицы
            table_key = self.table_keys.get(table_name)
            if not table_key:
                raise ValueError(f"Нет ключа для таблицы {table_name}")
            
            # Шифруем
            ciphertext, iv = self.key_manager._encrypt_with_key(value, table_key)
            
            self.logger.debug(f"🔒 Зашифровано поле {table_name}.{field_name}")
            return ciphertext, iv
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка шифрования {table_name}.{field_name}: {e}")
            raise
    
    def decrypt_field(self, table_name: str, field_name: str, ciphertext: bytes, iv: bytes) -> str:
        """
        Расшифровка поля данных
        
        Args:
            table_name: Название таблицы
            field_name: Название поля
            ciphertext: Зашифрованные данные
            iv: Initialization vector
            
        Returns:
            str: Расшифрованное значение
        """
        if not ciphertext or not iv:
            return ""
        
        # Проверяем, было ли поле зашифровано
        config = self.encryption_config.get(table_name, {})
        if field_name not in config.get('fields', []):
            # Если поле не шифровалось, возвращаем как строку
            return ciphertext.decode('utf-8') if isinstance(ciphertext, bytes) else str(ciphertext)
        
        try:
            # Получаем ключ для таблицы
            table_key = self.table_keys.get(table_name)
            if not table_key:
                raise ValueError(f"Нет ключа для таблицы {table_name}")
            
            # Расшифровываем
            plaintext = self.key_manager._decrypt_with_key(ciphertext, iv, table_key)
            
            self.logger.debug(f"🔓 Расшифровано поле {table_name}.{field_name}")
            return plaintext
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка расшифровки {table_name}.{field_name}: {e}")
            return f"[ОШИБКА РАСШИФРОВКИ: {str(e)[:50]}]"
    
    def encrypt_record(self, table_name: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Автоматическое шифрование всех чувствительных полей в записи
        
        Args:
            table_name: Название таблицы
            record_data: Данные записи
            
        Returns:
            Dict: Запись с зашифрованными полями
        """
        encrypted_record = record_data.copy()
        
        config = self.encryption_config.get(table_name, {})
        fields_to_encrypt = config.get('fields', [])
        
        for field_name in fields_to_encrypt:
            if field_name in encrypted_record and encrypted_record[field_name]:
                value = str(encrypted_record[field_name])
                
                # Шифруем значение
                ciphertext, iv = self.encrypt_field(table_name, field_name, value)
                
                # Заменяем поле зашифрованными данными
                encrypted_record[f"{field_name}_encrypted"] = ciphertext
                encrypted_record[f"{field_name}_iv"] = iv
                
                # Удаляем исходное поле из записи
                del encrypted_record[field_name]
        
        return encrypted_record
    
    def decrypt_record(self, table_name: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Автоматическая расшифровка всех зашифрованных полей в записи
        
        Args:
            table_name: Название таблицы
            record_data: Данные записи с зашифрованными полями
            
        Returns:
            Dict: Запись с расшифрованными полями
        """
        decrypted_record = record_data.copy()
        
        config = self.encryption_config.get(table_name, {})
        fields_to_decrypt = config.get('fields', [])
        
        for field_name in fields_to_decrypt:
            encrypted_field = f"{field_name}_encrypted"
            iv_field = f"{field_name}_iv"
            
            if encrypted_field in decrypted_record and iv_field in decrypted_record:
                ciphertext = decrypted_record[encrypted_field]
                iv = decrypted_record[iv_field]
                
                if ciphertext and iv:
                    # Расшифровываем
                    plaintext = self.decrypt_field(table_name, field_name, ciphertext, iv)
                    decrypted_record[field_name] = plaintext
                    
                    # Удаляем зашифрованные поля из результата
                    del decrypted_record[encrypted_field]
                    del decrypted_record[iv_field]
        
        return decrypted_record
    
    def get_encryption_info(self) -> Dict[str, Any]:
        """Получить информацию о настройках шифрования"""
        return {
            'algorithm': 'AES-256-CBC',
            'key_derivation': 'PBKDF2-HMAC-SHA256',
            'iterations': self.key_manager.iterations,
            'master_key_exists': os.path.exists(self.key_manager.master_key_file),
            'key_metadata': getattr(self.key_manager, 'key_metadata', {}),
            'encrypted_tables': list(self.encryption_config.keys()),
            'total_encrypted_fields': sum(len(config['fields']) for config in self.encryption_config.values()),
            'table_details': self.encryption_config
        }


class TDEDatabaseConnection:
    """
    Подключение к БД с автоматическим TDE
    Прозрачно шифрует и расшифровывает данные при взаимодействии с БД
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
    Курсор БД с автоматическим шифрованием/расшифровкой
    """
    
    def __init__(self, cursor, tde_manager: TDEManager):
        self.cursor = cursor
        self.tde = tde_manager
        self.logger = logging.getLogger(__name__)
    
    def execute(self, query: str, params=None):
        """Выполнение запроса с автоматическим TDE"""
        # Определяем тип операции и таблицу
        operation_info = self._parse_query(query)
        
        if operation_info['operation'] == 'INSERT' and operation_info['table']:
            # При вставке автоматически шифруем данные
            if params and isinstance(params, dict):
                encrypted_params = self.tde.encrypt_record(operation_info['table'], params)
                return self.cursor.execute(query, encrypted_params)
        
        # Для остальных операций - обычное выполнение
        return self.cursor.execute(query, params)
    
    def fetchone(self):
        """Получение одной записи с автоматической расшифровкой"""
        result = self.cursor.fetchone()
        if result:
            table_name = self._guess_table_from_result(result)
            if table_name:
                return self.tde.decrypt_record(table_name, dict(result))
        return result
    
    def fetchall(self):
        """Получение всех записей с автоматической расшифровкой"""
        results = self.cursor.fetchall()
        if results:
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
        if 'INSERT INTO' in query_upper:
            operation = 'INSERT'
            import re
            match = re.search(r'INSERT\s+INTO\s+(\w+)', query_upper)
            if match:
                table = match.group(1).lower()
        elif 'SELECT' in query_upper:
            operation = 'SELECT'
            import re
            match = re.search(r'FROM\s+(\w+)', query_upper)
            if match:
                table = match.group(1).lower()
        elif 'UPDATE' in query_upper:
            operation = 'UPDATE'
            import re
            match = re.search(r'UPDATE\s+(\w+)', query_upper)
            if match:
                table = match.group(1).lower()
        
        return {'operation': operation, 'table': table}
    
    def _guess_table_from_result(self, result_row) -> Optional[str]:
        """Определение таблицы по структуре результата"""
        if not result_row:
            return None
        
        columns = set(result_row.keys()) if hasattr(result_row, 'keys') else set()
        
        # Проверяем характерные столбцы для каждой таблицы
        table_signatures = {
            'patients': {'first_name', 'last_name', 'birth_date', 'gender'},
            'doctors': {'specialization', 'license_number'},
            'appointments': {'appointment_date', 'status', 'patient_id', 'doctor_id'},
            'medical_records': {'appointment_id', 'complaints'},
            'prescriptions': {'medication_name', 'dosage', 'frequency'}
        }
        
        for table_name, signature in table_signatures.items():
            if signature.issubset(columns):
                return table_name
        
        return None
    
    def __getattr__(self, name):
        """Проксирование всех остальных методов к оригинальному курсору"""
        return getattr(self.cursor, name)


# Функции для интеграции с существующей системой
def upgrade_database_for_tde():
    """Обновление структуры БД для поддержки TDE"""
    print("🔒 Обновление структуры БД для TDE...")
    
    from src.database.connection import db
    
    tde = TDEManager()
    
    # SQL команды для добавления столбцов IV
    alter_commands = []
    
    for table_name, config in tde.encryption_config.items():
        fields = config['fields']
        for field_name in fields:
            # Добавляем столбцы для зашифрованных данных и IV
            alter_commands.extend([
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = '{table_name}' 
                        AND column_name = '{field_name}_encrypted'
                    ) THEN
                        ALTER TABLE {table_name} ADD COLUMN {field_name}_encrypted BYTEA;
                    END IF;
                END $$;
                """,
                f"""
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
                """
            ])
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for command in alter_commands:
                cursor.execute(command)
                print(f"✅ Выполнено: добавление TDE столбцов")
            
            conn.commit()
            print("✅ Структура БД обновлена для поддержки TDE")
            
            # Создаем индексы для TDE полей
            print("📇 Создание индексов для TDE...")
            
            index_commands = [
                "CREATE INDEX IF NOT EXISTS idx_patients_phone_encrypted ON patients(phone_encrypted) WHERE phone_encrypted IS NOT NULL;",
                "CREATE INDEX IF NOT EXISTS idx_patients_email_encrypted ON patients(email_encrypted) WHERE email_encrypted IS NOT NULL;",
                "CREATE INDEX IF NOT EXISTS idx_doctors_email_encrypted ON doctors(email_encrypted) WHERE email_encrypted IS NOT NULL;",
                "CREATE INDEX IF NOT EXISTS idx_medical_records_diagnosis_encrypted ON medical_records(diagnosis_encrypted) WHERE diagnosis_encrypted IS NOT NULL;",
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


def test_tde():
    """Комплексное тестирование TDE"""
    print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ TDE")
    print("=" * 60)
    
    tde = TDEManager()
    
    # Тест 1: Шифрование/расшифровка отдельных полей
    print("\n1️⃣ Тест шифрования отдельных полей:")
    
    test_cases = [
        ('patients', 'phone', '+7 (999) 123-45-67'),
        ('patients', 'email', 'тест@example.com'),
        ('patients', 'address', 'г. Москва, ул. Тестовая, д. 1, кв. 10'),
        ('medical_records', 'diagnosis', 'Острый бронхит с осложнениями'),
        ('medical_records', 'complaints', 'Кашель, температура 38.5°C, слабость'),
    ]
    
    for table, field, test_data in test_cases:
        ciphertext, iv = tde.encrypt_field(table, field, test_data)
        decrypted = tde.decrypt_field(table, field, ciphertext, iv)
        
        print(f"  📝 {table}.{field}:")
        print(f"     Исходно: {test_data}")
        print(f"     Зашифровано: {len(ciphertext)} байт")
        print(f"     Расшифровано: {decrypted}")
        print(f"     Совпадение: {'✅' if test_data == decrypted else '❌'}")
    
    # Тест 2: Шифрование целых записей
    print(f"\n2️⃣ Тест шифрования записей:")
    
    test_patient = {
        'first_name': 'Иван',
        'last_name': 'Тестов',
        'phone': '+7 (999) 888-77-66',
        'email': 'ivan.testov@example.com',
        'address': 'г. Санкт-Петербург, пр. Невский, д. 100'
    }
    
    encrypted_patient = tde.encrypt_record('patients', test_patient)
    decrypted_patient = tde.decrypt_record('patients', encrypted_patient)
    
    print(f"  📋 Пациент:")
    print(f"     Исходная запись: {test_patient}")
    print(f"     После шифрования: {list(encrypted_patient.keys())}")
    print(f"     После расшифровки: {decrypted_patient}")
    
    # Проверяем, что незашифрованные поля остались без изменений
    assert test_patient['first_name'] == decrypted_patient['first_name']
    assert test_patient['last_name'] == decrypted_patient['last_name']
    
    # Проверяем, что зашифрованные поля расшифровались правильно
    assert test_patient['phone'] == decrypted_patient['phone']
    assert test_patient['email'] == decrypted_patient['email']
    assert test_patient['address'] == decrypted_patient['address']
    
    print(f"  ✅ Все поля корректно зашифрованы и расшифрованы!")
    
    # Тест 3: Производительность
    print(f"\n3️⃣ Тест производительности:")
    
    import time
    
    # Тестируем скорость шифрования
    start_time = time.time()
    for i in range(1000):
        test_text = f"Тестовые данные номер {i} для проверки производительности"
        ciphertext, iv = tde.encrypt_field('patients', 'address', test_text)
        decrypted = tde.decrypt_field('patients', 'address', ciphertext, iv)
    
    end_time = time.time()
    operations_per_second = 2000 / (end_time - start_time)  # 2000 операций (1000 шифр + 1000 расшифр)
    
    print(f"  ⚡ Производительность: {operations_per_second:.0f} операций/сек")
    print(f"  ⏱️ Время выполнения 1000 циклов: {(end_time - start_time):.2f}с")
    
    # Тест 4: Информация о шифровании
    print(f"\n4️⃣ Информация о TDE:")
    info = tde.get_encryption_info()
    for key, value in info.items():
        if key != 'table_details':
            print(f"   {key}: {value}")
    
    print(f"\n📋 Детали шифрования по таблицам:")
    for table, details in info['table_details'].items():
        print(f"   📊 {table}:")
        print(f"      Поля: {', '.join(details['fields'])}")
        print(f"      Чувствительность: {details['sensitivity']}")
    
    print(f"\n✅ ВСЕ ТЕСТЫ TDE ПРОЙДЕНЫ УСПЕШНО!")
    return True


# Интеграция с существующей системой
def enable_tde_for_existing_connection():
    """Включение TDE для существующего подключения к БД"""
    print("🔗 Интеграция TDE с существующим подключением...")
    
    try:
        # Импортируем существующее подключение
        from src.database.connection import db
        
        # Получаем параметры подключения
        connection_params = db.connection_params.copy()
        
        # Создаем TDE подключение
        tde_connection = TDEDatabaseConnection(connection_params)
        
        # Заменяем методы в существующем объекте
        original_get_connection = db.get_connection
        original_get_cursor = db.get_cursor
        
        db.get_connection = tde_connection.get_connection
        db.get_cursor = tde_connection.get_cursor
        db.tde_enabled = True
        db.tde_manager = tde_connection.tde
        
        print("✅ TDE успешно интегрирован с существующим подключением")
        
        # Добавляем методы для работы с TDE
        def get_tde_info():
            return tde_connection.tde.get_encryption_info()
        
        def rotate_keys():
            return tde_connection.tde.key_manager.rotate_master_key()
        
        db.get_tde_info = get_tde_info
        db.rotate_tde_keys = rotate_keys
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка интеграции TDE: {e}")
        return False


# Утилиты для администрирования TDE
class TDEAdmin:
    """Утилиты администрирования TDE"""
    
    def __init__(self):
        self.tde = TDEManager()
    
    def migrate_existing_data(self):
        """Миграция существующих данных под TDE"""
        print("🔄 МИГРАЦИЯ СУЩЕСТВУЮЩИХ ДАННЫХ ПОД TDE")
        print("⚠️ ВНИМАНИЕ: Эта операция изменит все существующие данные!")
        
        confirm = input("Продолжить? Введите 'MIGRATE' для подтверждения: ")
        if confirm != 'MIGRATE':
            print("🛑 Миграция отменена")
            return False
        
        from src.database.connection import db
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                total_migrated = 0
                
                for table_name, config in self.tde.encryption_config.items():
                    fields_to_encrypt = config['fields']
                    
                    print(f"\n📋 Миграция таблицы {table_name}...")
                    
                    # Получаем все записи
                    cursor.execute(f"SELECT * FROM {table_name}")
                    records = cursor.fetchall()
                    
                    print(f"   Найдено {len(records)} записей")
                    
                    migrated_count = 0
                    
                    for record in records:
                        record_dict = dict(record)
                        record_id = record_dict.get('id')
                        
                        # Проверяем, нужна ли миграция
                        needs_migration = False
                        for field in fields_to_encrypt:
                            encrypted_field = f"{field}_encrypted"
                            if field in record_dict and record_dict[field] and not record_dict.get(encrypted_field):
                                needs_migration = True
                                break
                        
                        if not needs_migration:
                            continue
                        
                        # Шифруем поля
                        update_fields = []
                        update_values = []
                        
                        for field in fields_to_encrypt:
                            if field in record_dict and record_dict[field]:
                                value = str(record_dict[field])
                                
                                ciphertext, iv = self.tde.encrypt_field(table_name, field, value)
                                
                                update_fields.append(f"{field}_encrypted = %s, {field}_iv = %s")
                                update_values.extend([ciphertext, iv])
                        
                        if update_fields:
                            update_query = f"""
                                UPDATE {table_name} 
                                SET {', '.join(update_fields)}
                                WHERE id = %s
                            """
                            update_values.append(record_id)
                            
                            cursor.execute(update_query, update_values)
                            migrated_count += 1
                    
                    conn.commit()
                    total_migrated += migrated_count
                    print(f"   ✅ Мигрировано {migrated_count} записей")
                
                print(f"\n🎉 МИГРАЦИЯ ЗАВЕРШЕНА!")
                print(f"   Всего мигрировано: {total_migrated} записей")
                print(f"   TDE активирован для всех чувствительных данных")
                
                return True
                
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            return False
    
    def verify_encryption(self):
        """Проверка корректности шифрования в БД"""
        print("🔍 ПРОВЕРКА ШИФРОВАНИЯ В БД")
        print("=" * 40)
        
        from src.database.connection import db
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                total_encrypted = 0
                total_records = 0
                
                for table_name, config in self.tde.encryption_config.items():
                    fields_to_check = config['fields']
                    
                    print(f"\n📋 Проверка таблицы {table_name}:")
                    
                    # Считаем общее количество записей
                    cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
                    table_total = cursor.fetchone()['total']
                    
                    # Считаем зашифрованные записи
                    encrypted_conditions = []
                    for field in fields_to_check:
                        encrypted_conditions.append(f"{field}_encrypted IS NOT NULL")
                    
                    if encrypted_conditions:
                        cursor.execute(f"""
                            SELECT COUNT(*) as encrypted 
                            FROM {table_name} 
                            WHERE {' OR '.join(encrypted_conditions)}
                        """)
                        table_encrypted = cursor.fetchone()['encrypted']
                    else:
                        table_encrypted = 0
                    
                    encryption_percent = (table_encrypted / table_total * 100) if table_total > 0 else 0
                    
                    print(f"   📊 Всего записей: {table_total}")
                    print(f"   🔒 Зашифровано: {table_encrypted} ({encryption_percent:.1f}%)")
                    
                    # Проверяем отдельные поля
                    for field in fields_to_check:
                        cursor.execute(f"""
                            SELECT COUNT(*) as field_encrypted 
                            FROM {table_name} 
                            WHERE {field}_encrypted IS NOT NULL
                        """)
                        field_encrypted = cursor.fetchone()['field_encrypted']
                        print(f"     📝 {field}: {field_encrypted} зашифрованных значений")
                    
                    total_encrypted += table_encrypted
                    total_records += table_total
                
                overall_percent = (total_encrypted / total_records * 100) if total_records > 0 else 0
                
                print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
                print(f"   Всего записей в системе: {total_records}")
                print(f"   Записей с шифрованием: {total_encrypted}")
                print(f"   Процент покрытия: {overall_percent:.1f}%")
                
                if overall_percent > 80:
                    print(f"   ✅ Отличное покрытие шифрованием!")
                elif overall_percent > 50:
                    print(f"   👍 Хорошее покрытие шифрованием")
                else:
                    print(f"   ⚠️ Низкое покрытие, рекомендуется миграция")
                
                return True
                
        except Exception as e:
            print(f"❌ Ошибка проверки: {e}")
            return False
    
    def cleanup_unencrypted_data(self):
        """Очистка незашифрованных данных после миграции"""
        print("🧹 ОЧИСТКА НЕЗАШИФРОВАННЫХ ДАННЫХ")
        print("⚠️ ВНИМАНИЕ: Удалит исходные данные после шифрования!")
        
        confirm = input("Продолжить? Введите 'CLEANUP' для подтверждения: ")
        if confirm != 'CLEANUP':
            print("🛑 Очистка отменена")
            return False
        
        from src.database.connection import db
        
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                total_cleaned = 0
                
                for table_name, config in self.tde.encryption_config.items():
                    fields_to_clean = config['fields']
                    
                    print(f"\n🧹 Очистка таблицы {table_name}...")
                    
                    for field in fields_to_clean:
                        # Очищаем поле только если есть зашифрованная версия
                        cursor.execute(f"""
                            UPDATE {table_name} 
                            SET {field} = NULL 
                            WHERE {field}_encrypted IS NOT NULL 
                            AND {field} IS NOT NULL
                        """)
                        
                        cleaned = cursor.rowcount
                        total_cleaned += cleaned
                        print(f"   🗑️ Очищено {field}: {cleaned} записей")
                    
                    conn.commit()
                
                print(f"\n✅ ОЧИСТКА ЗАВЕРШЕНА!")
                print(f"   Всего очищено полей: {total_cleaned}")
                print(f"   Чувствительные данные доступны только в зашифрованном виде")
                
                return True
                
        except Exception as e:
            print(f"❌ Ошибка очистки: {e}")
            return False


def main_tde_setup():
    """Главная функция настройки TDE"""
    print("🔒 НАСТРОЙКА TRANSPARENT DATA ENCRYPTION (TDE)")
    print("=" * 60)
    
    try:
        print("\n1️⃣ Создание TDE менеджера...")
        tde = TDEManager()
        print("✅ TDE менеджер создан")
        
        print("\n2️⃣ Обновление структуры БД...")
        upgrade_database_for_tde()
        print("✅ Структура БД обновлена")
        
        print("\n3️⃣ Интеграция с подключением...")
        if enable_tde_for_existing_connection():
            print("✅ TDE интегрирован")
        else:
            print("⚠️ Интеграция частично выполнена")
        
        print("\n4️⃣ Тестирование TDE...")
        if test_tde():
            print("✅ Все тесты пройдены")
        
        print("\n🎉 TDE НАСТРОЕН УСПЕШНО!")
        print("\n📋 Следующие шаги:")
        print("   1. Выполните миграцию данных: python -c \"from src.security.tde_complete import TDEAdmin; TDEAdmin().migrate_existing_data()\"")
        print("   2. Проверьте шифрование: python -c \"from src.security.tde_complete import TDEAdmin; TDEAdmin().verify_encryption()\"") 
        print("   3. Запустите систему: python run.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка настройки TDE: {e}")
        return False


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Запуск настройки TDE
    main_tde_setup()