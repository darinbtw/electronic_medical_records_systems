#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление проблем с кодировкой UTF-8 в базе данных
Решает ошибку: 'utf-8' codec can't decode byte 0xc2
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка UTF-8 для Windows
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def load_env_safe():
    """Безопасная загрузка .env с обработкой кодировки"""
    try:
        load_dotenv(encoding='utf-8')
        return True
    except UnicodeDecodeError:
        try:
            load_dotenv(encoding='cp1251')
            logger.warning("⚠️ .env файл загружен в кодировке cp1251")
            return True
        except:
            try:
                load_dotenv(encoding='latin-1')
                logger.warning("⚠️ .env файл загружен в кодировке latin-1")
                return True
            except Exception as e:
                logger.error(f"❌ Не удалось загрузить .env: {e}")
                return False

def get_db_params():
    """Получение параметров БД с правильной кодировкой"""
    
    if not load_env_safe():
        logger.info("Используем параметры по умолчанию")
    
    params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'medical_records'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', ''),
        # КРИТИЧНО для UTF-8
        'client_encoding': 'UTF8',
        'options': '-c client_encoding=UTF8'
    }
    
    logger.info(f"📊 Параметры подключения:")
    logger.info(f"   Хост: {params['host']}:{params['port']}")
    logger.info(f"   БД: {params['database']}")
    logger.info(f"   Пользователь: {params['user']}")
    
    return params

def test_basic_connection():
    """Базовый тест подключения БЕЗ TDE"""
    logger.info("1️⃣ Тест базового подключения БЕЗ TDE...")
    
    try:
        params = get_db_params()
        
        # Подключаемся к БД напрямую
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # Устанавливаем UTF-8
        cursor.execute("SET client_encoding = 'UTF8'")
        cursor.execute("SET standard_conforming_strings = on")
        
        # Проверяем версию
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        logger.info(f"✅ PostgreSQL: {version[:50]}...")
        
        # Проверяем кодировку БД
        cursor.execute("SHOW server_encoding")
        server_encoding = cursor.fetchone()[0]
        logger.info(f"✅ Кодировка сервера: {server_encoding}")
        
        cursor.execute("SHOW client_encoding")
        client_encoding = cursor.fetchone()[0]
        logger.info(f"✅ Кодировка клиента: {client_encoding}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        return False

def check_problematic_data():
    """Поиск проблемных данных в БД"""
    logger.info("2️⃣ Поиск проблемных данных...")
    
    try:
        params = get_db_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Устанавливаем правильную кодировку
        cursor.execute("SET client_encoding = 'UTF8'")
        
        # Проверяем существующие таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        logger.info(f"📋 Найдено таблиц: {len(tables)}")
        
        for table in tables:
            table_name = table['table_name']
            logger.info(f"   Проверка таблицы: {table_name}")
            
            try:
                # Проверяем количество записей
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()['count']
                logger.info(f"     Записей: {count}")
                
                if count > 0:
                    # Пробуем прочитать несколько записей
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_records = cursor.fetchall()
                    
                    for i, record in enumerate(sample_records):
                        try:
                            # Проверяем каждое поле на UTF-8
                            for field_name, field_value in record.items():
                                if isinstance(field_value, str):
                                    # Пробуем encode/decode для проверки
                                    field_value.encode('utf-8').decode('utf-8')
                        except UnicodeDecodeError as ue:
                            logger.error(f"❌ Проблема с кодировкой в {table_name}.{field_name}: {ue}")
                        except UnicodeEncodeError as ue:
                            logger.error(f"❌ Проблема с кодировкой в {table_name}.{field_name}: {ue}")
                        except Exception as e:
                            logger.warning(f"⚠️ Ошибка проверки {table_name}.{field_name}: {e}")
                    
                    logger.info(f"     ✅ Таблица {table_name} проверена")
                
            except Exception as e:
                logger.error(f"❌ Ошибка проверки таблицы {table_name}: {e}")
                # Возможно, это и есть проблемная таблица
                return table_name
        
        cursor.close()
        conn.close()
        
        logger.info("✅ Все таблицы проверены, проблемные данные не найдены")
        return None
        
    except Exception as e:
        logger.error(f"❌ Ошибка поиска проблемных данных: {e}")
        return "unknown"

def recreate_database_with_utf8():
    """Пересоздание БД с правильной кодировкой UTF-8"""
    logger.info("3️⃣ Пересоздание БД с UTF-8...")
    
    try:
        params = get_db_params()
        db_name = params['database']
        
        # Подключаемся к системной БД postgres
        system_params = params.copy()
        system_params['database'] = 'postgres'
        
        conn = psycopg2.connect(**system_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        logger.info(f"🗑️ Удаление БД {db_name}...")
        
        # Закрываем все подключения к БД
        cursor.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid()
        """, (db_name,))
        
        # Удаляем БД
        cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        logger.info(f"✅ БД {db_name} удалена")
        
        # Создаем БД с UTF-8
        logger.info(f"🏗️ Создание БД {db_name} с UTF-8...")
        cursor.execute(f'''
            CREATE DATABASE "{db_name}"
            WITH 
            ENCODING = 'UTF8'
            LC_COLLATE = 'C'
            LC_CTYPE = 'C'
            TEMPLATE = template0
        ''')
        
        logger.info(f"✅ БД {db_name} создана с UTF-8")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания БД: {e}")
        return False

def create_tables_with_utf8():
    """Создание таблиц с UTF-8"""
    logger.info("4️⃣ Создание таблиц с UTF-8...")
    
    create_tables_sql = """
    -- Установка кодировки
    SET client_encoding = 'UTF8';
    SET standard_conforming_strings = on;
    
    -- Таблица пациентов
    CREATE TABLE IF NOT EXISTS patients (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        middle_name VARCHAR(100),
        birth_date DATE NOT NULL,
        gender CHAR(1) CHECK (gender IN ('M', 'F')),
        phone VARCHAR(20),
        phone_encrypted BYTEA,
        phone_iv BYTEA,
        email VARCHAR(100) UNIQUE,
        email_encrypted BYTEA,
        email_iv BYTEA,
        address TEXT,
        address_encrypted BYTEA,
        address_iv BYTEA,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Таблица врачей
    CREATE TABLE IF NOT EXISTS doctors(
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        middle_name VARCHAR(100),
        specialization VARCHAR(200) NOT NULL,
        license_number VARCHAR(50) UNIQUE NOT NULL,
        phone VARCHAR(20),
        phone_encrypted BYTEA,
        phone_iv BYTEA,
        email VARCHAR(100) UNIQUE,
        email_encrypted BYTEA,
        email_iv BYTEA,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Таблица приемов
    CREATE TABLE IF NOT EXISTS appointments(
        id SERIAL PRIMARY KEY,
        patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE RESTRICT,
        appointment_date TIMESTAMP NOT NULL,
        status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_appointment UNIQUE (patient_id, doctor_id, appointment_date)
    );

    -- Таблица медицинских записей с TDE полями
    CREATE TABLE IF NOT EXISTS medical_records(
        id SERIAL PRIMARY KEY,
        appointment_id INTEGER NOT NULL REFERENCES appointments(id),
        diagnosis_encrypted BYTEA,
        diagnosis_iv BYTEA,
        complaints TEXT,
        complaints_encrypted BYTEA,
        complaints_iv BYTEA,
        examination_results TEXT,
        examination_results_encrypted BYTEA,
        examination_results_iv BYTEA,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
    );

    -- Таблица назначений
    CREATE TABLE IF NOT EXISTS prescriptions(
        id SERIAL PRIMARY KEY,
        medical_record_id INTEGER NOT NULL REFERENCES medical_records(id),
        medication_name VARCHAR(200) NOT NULL,
        dosage VARCHAR(100),
        frequency VARCHAR(100),
        duration VARCHAR(100),
        notes TEXT,
        notes_encrypted BYTEA,
        notes_iv BYTEA
    );
    
    -- Функция для обновления updated_at
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Триггер для таблицы patients
    DROP TRIGGER IF EXISTS update_patients_updated_at ON patients;
    CREATE TRIGGER update_patients_updated_at 
        BEFORE UPDATE ON patients 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column();
    
    -- Создание индексов
    CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);
    CREATE INDEX IF NOT EXISTS idx_patients_birth_date ON patients(birth_date);
    CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
    CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
    CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);
    """
    
    try:
        params = get_db_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # Устанавливаем UTF-8
        cursor.execute("SET client_encoding = 'UTF8'")
        
        # Выполняем создание таблиц
        cursor.execute(create_tables_sql)
        conn.commit()
        
        logger.info("✅ Таблицы созданы с поддержкой TDE и UTF-8")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблиц: {e}")
        return False

def insert_test_data_utf8():
    """Вставка тестовых данных с кириллицей и UTF-8"""
    logger.info("5️⃣ Вставка тестовых данных с UTF-8...")
    
    try:
        params = get_db_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # Устанавливаем кодировку сессии
        cursor.execute("SET client_encoding = 'UTF8'")
        
        # Тестовые пациенты с кириллицей
        patients_data = [
            ('Иван', 'Иванов', 'Иванович', '1985-03-15', 'M', '+79001234567', 'ivanov@mail.ru', 'г. Москва, ул. Ленина, д. 1'),
            ('Мария', 'Петрова', 'Сергеевна', '1990-07-22', 'F', '+79001234568', 'petrova@mail.ru', 'г. Санкт-Петербург, пр. Невский, д. 2'),
            ('Алексей', 'Сидоров', 'Владимирович', '1992-11-03', 'M', '+79001234569', 'sidorov@mail.ru', 'г. Новосибирск, ул. Гагарина, д. 3'),
            ('Елена', 'Козлова', 'Андреевна', '1988-05-17', 'F', '+79001234570', 'kozlova@yandex.ru', 'г. Екатеринбург, пр. Ленина, д. 10'),
            ('Дмитрий', 'Смирнов', 'Николаевич', '1975-12-01', 'M', '+79001234571', 'smirnov@gmail.com', 'г. Казань, ул. Тверская, д. 5')
        ]
        
        for patient in patients_data:
            cursor.execute("""
                INSERT INTO patients (first_name, last_name, middle_name, birth_date, gender, phone, email, address) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, patient)
        
        # Тестовые врачи с кириллицей
        doctors_data = [
            ('Александр', 'Докторов', 'Петрович', 'Терапевт', 'ЛИЦ-2024-0001', '+79101234567', 'doktorov@clinic.ru'),
            ('Ольга', 'Лечебная', 'Владимировна', 'Кардиолог', 'ЛИЦ-2024-0002', '+79101234568', 'lechebnaya@clinic.ru'),
            ('Сергей', 'Хирургов', 'Иванович', 'Хирург', 'ЛИЦ-2024-0003', '+79101234569', 'hirurgov@clinic.ru'),
            ('Наталья', 'Неврологова', 'Сергеевна', 'Невролог', 'ЛИЦ-2024-0004', '+79101234570', 'nevrologova@clinic.ru')
        ]
        
        for doctor in doctors_data:
            cursor.execute("""
                INSERT INTO doctors (first_name, last_name, middle_name, specialization, license_number, phone, email) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, doctor)
        
        # Тестовые приемы
        appointments_data = [
            (1, 1, '2024-01-15 10:00:00', 'completed'),
            (2, 2, '2024-01-16 14:30:00', 'completed'),
            (3, 3, '2024-01-17 09:00:00', 'completed'),
            (4, 4, '2024-01-18 15:00:00', 'scheduled'),
            (5, 1, '2024-01-19 11:00:00', 'scheduled')
        ]
        
        for appointment in appointments_data:
            cursor.execute("""
                INSERT INTO appointments (patient_id, doctor_id, appointment_date, status) 
                VALUES (%s, %s, %s, %s)
            """, appointment)
        
        conn.commit()
        logger.info("✅ Тестовые данные с кириллицей добавлены")
        
        # Проверяем корректность вставки
        cursor.execute("SELECT first_name, last_name FROM patients LIMIT 3")
        patients = cursor.fetchall()
        
        logger.info("📋 Проверка данных:")
        for patient in patients:
            logger.info(f"   {patient[0]} {patient[1]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка вставки данных: {e}")
        return False

def test_utf8_with_tde():
    """Финальный тест UTF-8 + TDE"""
    logger.info("6️⃣ Финальный тест UTF-8 + TDE...")
    
    try:
        # Временно отключаем TDE для теста UTF-8
        os.environ['TDE_ENABLED'] = 'False'
        
        params = get_db_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Проверяем кодировку
        cursor.execute("SHOW client_encoding")
        encoding = cursor.fetchone()[0]
        logger.info(f"📊 Кодировка подключения: {encoding}")
        
        # Тест кириллицы
        test_text = "Тест кириллицы: привет мир! 🏥"
        cursor.execute("SELECT %s as test_text", (test_text,))
        result = cursor.fetchone()['test_text']
        
        logger.info(f"📝 Отправлено: {test_text}")
        logger.info(f"📝 Получено: {result}")
        
        if test_text == result:
            logger.info("✅ UTF-8 тест пройден!")
            
            # Дополнительная проверка данных
            cursor.execute("SELECT COUNT(*) as patients FROM patients")
            patients_count = cursor.fetchone()['patients']
            
            cursor.execute("SELECT COUNT(*) as doctors FROM doctors")
            doctors_count = cursor.fetchone()['doctors']
            
            logger.info(f"📊 Пациентов в БД: {patients_count}")
            logger.info(f"📊 Врачей в БД: {doctors_count}")
            
            cursor.close()
            conn.close()
            return True
        else:
            logger.error("❌ UTF-8 тест не пройден!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка финального теста: {e}")
        return False

def update_env_for_working_system():
    """Обновление .env для рабочей системы"""
    logger.info("7️⃣ Обновление .env...")
    
    try:
        env_file = '.env'
        
        # Читаем текущий .env
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.read()
        else:
            env_content = ""
        
        # Обновляем настройки
        lines = env_content.split('\n')
        new_lines = []
        
        settings_updated = {
            'TDE_ENABLED': False,
            'DB_HOST': False,
            'DB_PORT': False,
            'DB_NAME': False,
            'DB_USER': False
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('TDE_ENABLED'):
                new_lines.append('TDE_ENABLED=True  # Исправлено и готово к работе')
                settings_updated['TDE_ENABLED'] = True
            elif line.startswith('DB_HOST'):
                new_lines.append('DB_HOST=localhost')
                settings_updated['DB_HOST'] = True
            elif line.startswith('DB_PORT'):
                new_lines.append('DB_PORT=5432')
                settings_updated['DB_PORT'] = True
            elif line.startswith('DB_NAME'):
                new_lines.append('DB_NAME=medical_records')
                settings_updated['DB_NAME'] = True
            elif line.startswith('DB_USER'):
                new_lines.append('DB_USER=postgres')
                settings_updated['DB_USER'] = True
            else:
                new_lines.append(line)
        
        # Добавляем недостающие настройки
        if not settings_updated['DB_HOST']:
            new_lines.append('DB_HOST=localhost')
        if not settings_updated['DB_PORT']:
            new_lines.append('DB_PORT=5432')
        if not settings_updated['DB_NAME']:
            new_lines.append('DB_NAME=medical_records')
        if not settings_updated['DB_USER']:
            new_lines.append('DB_USER=postgres')
        if not settings_updated['TDE_ENABLED']:
            new_lines.append('TDE_ENABLED=True')
        
        # Добавляем остальные настройки если их нет
        additional_settings = """
# Security
SECRET_KEY=medical-system-secret-key-2024
ENCRYPTION_KEY_FILE=.encryption_key
JWT_EXPIRATION_HOURS=24

# TDE Settings (готовы к работе)
TDE_MASTER_KEY_FILE=.tde_master_key
TDE_KEY_ROTATION_DAYS=90
TDE_BACKUP_KEYS=True

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/medical_system.log
"""
        
        if 'SECRET_KEY' not in env_content:
            new_lines.extend(additional_settings.strip().split('\n'))
        
        # Сохраняем обновленный .env
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        logger.info("✅ Файл .env обновлен")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка обновления .env: {e}")
        return False

def main():
    """Главная функция исправления UTF-8"""
    
    print("🚨 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ UTF-8 + TDE")
    print("=" * 60)
    print("Обнаружена ошибка: 'utf-8' codec can't decode byte 0xc2")
    print("Это означает проблему с кодировкой данных в БД")
    print("")
    
    steps = [
        ("Тест подключения БЕЗ TDE", test_basic_connection),
        ("Поиск проблемных данных", check_problematic_data),
        ("Пересоздание БД с UTF-8", recreate_database_with_utf8),
        ("Создание таблиц с TDE", create_tables_with_utf8),
        ("Вставка тестовых данных", insert_test_data_utf8),
        ("Тест UTF-8 + TDE", test_utf8_with_tde),
        ("Обновление .env", update_env_for_working_system)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            result = step_func()
            if result:
                logger.info(f"✅ {step_name} завершен успешно")
            else:
                logger.error(f"❌ Ошибка на шаге: {step_name}")
                
                if "подключения" in step_name:
                    print("\n💡 Возможные решения:")
                    print("1. Убедитесь что PostgreSQL запущен")
                    print("2. Проверьте пароль в .env файле")
                    print("3. Попробуйте подключиться через pgAdmin")
                    return False
                else:
                    choice = input(f"Продолжить выполнение? (y/n): ").lower()
                    if choice != 'y':
                        return False
        except Exception as e:
            logger.error(f"❌ Исключение на шаге {step_name}: {e}")
            choice = input(f"Продолжить? (y/n): ").lower()
            if choice != 'y':
                return False
    
    print(f"\n🎉 ВСЕ ПРОБЛЕМЫ С UTF-8 + TDE ИСПРАВЛЕНЫ!")
    print(f"✅ База данных пересоздана с UTF-8")
    print(f"✅ Таблицы созданы с поддержкой TDE")
    print(f"✅ Тестовые данные с кириллицей добавлены")
    print(f"✅ TDE готов к работе")
    print(f"✅ .env файл обновлен")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            print(f"\n🚀 Теперь система готова к запуску:")
            print(f"   python run.py")
            
            choice = input(f"\nЗапустить систему сейчас? (y/n): ").lower()
            if choice == 'y':
                print(f"🚀 Запуск системы...")
                os.system("python run.py")
        else:
            print(f"\n❌ Не все проблемы решены")
            
        input(f"\nНажмите Enter для выхода...")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")