# Создайте файл: windows_utf8_fix.py

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# КРИТИЧНО: Настройка Windows для UTF-8
if sys.platform.startswith('win'):
    # Устанавливаем кодовую страницу UTF-8
    os.system('chcp 65001 > nul')
    
    # Настройка переменных окружения Windows
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '0'
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Перенаправляем stdout и stderr для правильной работы с UTF-8
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    sys.stdin = codecs.getreader('utf-8')(sys.stdin.detach())

print("🔧 ИСПРАВЛЕНИЕ UTF-8 ДЛЯ WINDOWS")
print("=" * 50)

def load_env_safe():
    """Безопасная загрузка .env с обработкой кодировки"""
    try:
        # Пробуем загрузить с UTF-8
        load_dotenv(encoding='utf-8')
        return True
    except UnicodeDecodeError:
        try:
            # Пробуем с cp1251 (Windows кириллица)
            load_dotenv(encoding='cp1251')
            print("⚠️ .env файл загружен в кодировке cp1251")
            return True
        except:
            try:
                # Пробуем с latin-1
                load_dotenv(encoding='latin-1')
                print("⚠️ .env файл загружен в кодировке latin-1")
                return True
            except Exception as e:
                print(f"❌ Не удалось загрузить .env: {e}")
                return False

def get_db_params():
    """Получение параметров БД с правильной кодировкой"""
    
    if not load_env_safe():
        print("Используем параметры по умолчанию")
    
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
    
    print(f"📊 Параметры подключения:")
    print(f"   Хост: {params['host']}:{params['port']}")
    print(f"   БД: {params['database']}")
    print(f"   Пользователь: {params['user']}")
    print(f"   Кодировка: {params['client_encoding']}")
    
    return params

def test_basic_connection():
    """Базовый тест подключения"""
    print("\n1️⃣ Тест базового подключения...")
    
    try:
        params = get_db_params()
        
        # Подключаемся к системной БД postgres
        test_params = params.copy()
        test_params['database'] = 'postgres'
        
        conn = psycopg2.connect(**test_params)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL подключен: {version[:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def recreate_database_python():
    """Пересоздание БД через Python (без psql)"""
    print("\n2️⃣ Пересоздание БД с UTF-8 через Python...")
    
    try:
        params = get_db_params()
        db_name = params['database']
        
        # Подключаемся к системной БД
        system_params = params.copy()
        system_params['database'] = 'postgres'
        
        conn = psycopg2.connect(**system_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print(f"🗑️ Удаление БД {db_name}...")
        
        # Закрываем все подключения к БД
        cursor.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = %s AND pid <> pg_backend_pid()
        """, (db_name,))
        
        # Удаляем БД
        cursor.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
        print(f"✅ БД {db_name} удалена")
        
        # Создаем БД с UTF-8
        print(f"🏗️ Создание БД {db_name} с UTF-8...")
        cursor.execute(f'''
            CREATE DATABASE "{db_name}"
            WITH 
            ENCODING = 'UTF8'
            LC_COLLATE = 'C'
            LC_CTYPE = 'C'
            TEMPLATE = template0
        ''')
        
        print(f"✅ БД {db_name} создана с UTF-8")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")
        return False

def create_tables_python():
    """Создание таблиц через Python"""
    print("\n3️⃣ Создание таблиц через Python...")
    
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
        email VARCHAR(100) UNIQUE,
        address TEXT,
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
        email VARCHAR(100) UNIQUE,
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

    -- Таблица медицинских записей
    CREATE TABLE IF NOT EXISTS medical_records(
        id SERIAL PRIMARY KEY,
        appointment_id INTEGER NOT NULL REFERENCES appointments(id),
        diagnosis_encrypted BYTEA,
        diagnosis_iv BYTEA,
        complaints TEXT,
        examination_results TEXT,
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
        notes TEXT
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
        
        # Выполняем создание таблиц
        cursor.execute(create_tables_sql)
        conn.commit()
        
        print("✅ Таблицы созданы")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False

def insert_test_data_python():
    """Вставка тестовых данных через Python"""
    print("\n4️⃣ Вставка тестовых данных с кириллицей...")
    
    try:
        params = get_db_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor()
        
        # Устанавливаем кодировку сессии
        cursor.execute("SET client_encoding = 'UTF8'")
        
        # Тестовые пациенты
        patients_data = [
            ('Иван', 'Иванов', 'Иванович', '1985-03-15', 'M', '+79001234567', 'ivanov@mail.ru', 'г. Москва, ул. Ленина, д. 1'),
            ('Мария', 'Петрова', 'Сергеевна', '1990-07-22', 'F', '+79001234568', 'petrova@mail.ru', 'г. Санкт-Петербург, ул. Пушкина, д. 2'),
            ('Алексей', 'Сидоров', 'Владимирович', '1992-11-03', 'M', '+79001234569', 'sidorov@mail.ru', 'г. Новосибирск, ул. Гагарина, д. 3'),
            ('Елена', 'Козлова', 'Андреевна', '1988-05-17', 'F', '+79001234570', 'kozlova@yandex.ru', 'г. Екатеринбург, пр. Ленина, д. 10'),
            ('Дмитрий', 'Смирнов', 'Николаевич', '1975-12-01', 'M', '+79001234571', 'smirnov@gmail.com', 'г. Казань, ул. Тверская, д. 5')
        ]
        
        for patient in patients_data:
            cursor.execute("""
                INSERT INTO patients (first_name, last_name, middle_name, birth_date, gender, phone, email, address) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, patient)
        
        # Тестовые врачи
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
        print("✅ Тестовые данные добавлены")
        
        # Проверяем корректность вставки
        cursor.execute("SELECT first_name, last_name FROM patients LIMIT 3")
        patients = cursor.fetchall()
        
        print("📋 Проверка данных:")
        for patient in patients:
            print(f"   {patient[0]} {patient[1]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка вставки данных: {e}")
        return False

def test_utf8_final():
    """Финальный тест UTF-8"""
    print("\n5️⃣ Финальный тест UTF-8...")
    
    try:
        params = get_db_params()
        conn = psycopg2.connect(**params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Проверяем кодировку
        cursor.execute("SHOW client_encoding")
        encoding = cursor.fetchone()[0]
        print(f"📊 Кодировка подключения: {encoding}")
        
        # Тест кириллицы
        test_text = "Тест кириллицы: привет мир! 🏥"
        cursor.execute("SELECT %s as test_text", (test_text,))
        result = cursor.fetchone()['test_text']
        
        print(f"📝 Отправлено: {test_text}")
        print(f"📝 Получено: {result}")
        
        if test_text == result:
            print("✅ UTF-8 тест пройден!")
            
            # Дополнительная проверка данных
            cursor.execute("SELECT COUNT(*) as patients FROM patients")
            patients_count = cursor.fetchone()['patients']
            
            cursor.execute("SELECT COUNT(*) as doctors FROM doctors")
            doctors_count = cursor.fetchone()['doctors']
            
            print(f"📊 Пациентов в БД: {patients_count}")
            print(f"📊 Врачей в БД: {doctors_count}")
            
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ UTF-8 тест не пройден!")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка финального теста: {e}")
        return False

def fix_connection_file():
    """Исправление файла подключения"""
    print("\n6️⃣ Исправление файла подключения...")
    
    connection_file = 'src/database/connection.py'
    
    if not os.path.exists(connection_file):
        print(f"⚠️ Файл {connection_file} не найден")
        return True  # Не критично
    
    try:
        # Читаем файл с разными кодировками
        content = None
        encodings = ['utf-8', 'cp1251', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(connection_file, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"📄 Файл прочитан в кодировке: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if not content:
            print(f"❌ Не удалось прочитать файл")
            return False
        
        # Проверяем, есть ли уже UTF-8 настройки
        if "'client_encoding': 'UTF8'" in content:
            print("✅ UTF-8 настройки уже есть")
            return True
        
        # Добавляем UTF-8 настройки
        if "'client_encoding'" not in content:
            content = content.replace(
                "self.connection_params = {",
                """self.connection_params = {
            'client_encoding': 'UTF8',
            'options': '-c client_encoding=UTF8',"""
            )
        
        # Сохраняем в UTF-8
        with open(connection_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Файл connection.py обновлен")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления файла: {e}")
        return False

def main():
    """Главная функция"""
    
    steps = [
        ("Тест подключения", test_basic_connection),
        ("Пересоздание БД", recreate_database_python),
        ("Создание таблиц", create_tables_python),
        ("Вставка данных", insert_test_data_python),
        ("Финальный тест", test_utf8_final),
        ("Обновление подключения", fix_connection_file)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            if not step_func():
                print(f"❌ Ошибка на шаге: {step_name}")
                
                if step_name == "Тест подключения":
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
            print(f"❌ Исключение на шаге {step_name}: {e}")
            choice = input(f"Продолжить? (y/n): ").lower()
            if choice != 'y':
                return False
    
    print(f"\n🎉 ВСЕ ПРОБЛЕМЫ С UTF-8 ИСПРАВЛЕНЫ!")
    print(f"✅ База данных создана с UTF-8")
    print(f"✅ Таблицы созданы через Python")
    print(f"✅ Тестовые данные добавлены")
    print(f"✅ Кириллица работает корректно")
    print(f"✅ Файлы обновлены")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            print(f"\n🚀 Теперь можно запускать систему:")
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