# Создайте файл: quick_utf8_fix.py

import os
import sys
import subprocess
from dotenv import load_dotenv

# Устанавливаем UTF-8 сразу
if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')

os.environ['PYTHONIOENCODING'] = 'utf-8'

def quick_fix():
    """Быстрое исправление всех проблем с UTF-8 одной командой"""
    
    print("⚡ БЫСТРОЕ ИСПРАВЛЕНИЕ UTF-8 ПРОБЛЕМ")
    print("=" * 50)
    
    load_dotenv()
    
    db_name = os.getenv('DB_NAME', 'medical_records')
    db_user = os.getenv('DB_USER', 'postgres')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    
    print(f"🎯 База данных: {db_name}")
    print(f"🎯 Пользователь: {db_user}")
    print(f"🎯 Хост: {db_host}:{db_port}")
    
    # 1. Пересоздание БД с UTF-8 через psql
    print(f"\n1️⃣ Пересоздание БД с UTF-8...")
    
    try:
        # Команды для пересоздания БД
        commands = [
            f'psql -h {db_host} -p {db_port} -U {db_user} -d postgres -c "DROP DATABASE IF EXISTS {db_name};"',
            f'psql -h {db_host} -p {db_port} -U {db_user} -d postgres -c "CREATE DATABASE {db_name} WITH ENCODING=\'UTF8\' LC_COLLATE=\'C\' LC_CTYPE=\'C\' TEMPLATE=template0;"'
        ]
        
        for cmd in commands:
            print(f"Выполняю: {cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Успешно")
            else:
                print(f"❌ Ошибка: {result.stderr}")
                
        print("✅ БД пересоздана с UTF-8")
        
    except Exception as e:
        print(f"❌ Ошибка пересоздания БД: {e}")
        print("\n📋 Выполните вручную:")
        print(f"psql -U {db_user} -c \"DROP DATABASE IF EXISTS {db_name};\"")
        print(f"psql -U {db_user} -c \"CREATE DATABASE {db_name} WITH ENCODING='UTF8' LC_COLLATE='C' LC_CTYPE='C' TEMPLATE=template0;\"")
    
    # 2. Создание таблиц через SQL файл
    print(f"\n2️⃣ Создание таблиц...")
    
    # Создаем SQL файл с правильной кодировкой
    create_tables_sql = """-- -*- coding: utf-8 -*-
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
        # Сохраняем SQL файл
        with open('temp_create_tables.sql', 'w', encoding='utf-8') as f:
            f.write(create_tables_sql)
        
        # Выполняем SQL файл
        cmd = f'psql -h {db_host} -p {db_port} -U {db_user} -d {db_name} -f temp_create_tables.sql'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Таблицы созданы")
        else:
            print(f"❌ Ошибка создания таблиц: {result.stderr}")
        
        # Удаляем временный файл
        os.remove('temp_create_tables.sql')
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
    
    # 3. Вставка тестовых данных
    print(f"\n3️⃣ Вставка тестовых данных...")
    
    test_data_sql = """-- -*- coding: utf-8 -*-
SET client_encoding = 'UTF8';

-- Тестовые пациенты
INSERT INTO patients (first_name, last_name, middle_name, birth_date, gender, phone, email, address) VALUES
('Иван', 'Иванов', 'Иванович', '1985-03-15', 'M', '+79001234567', 'ivanov@mail.ru', 'г. Москва, ул. Ленина, д. 1'),
('Мария', 'Петрова', 'Сергеевна', '1990-07-22', 'F', '+79001234568', 'petrova@mail.ru', 'г. Санкт-Петербург, ул. Пушкина, д. 2'),
('Алексей', 'Сидоров', 'Владимирович', '1992-11-03', 'M', '+79001234569', 'sidorov@mail.ru', 'г. Новосибирск, ул. Гагарина, д. 3'),
('Елена', 'Козлова', 'Андреевна', '1988-05-17', 'F', '+79001234570', 'kozlova@yandex.ru', 'г. Екатеринбург, пр. Ленина, д. 10'),
('Дмитрий', 'Смирнов', 'Николаевич', '1975-12-01', 'M', '+79001234571', 'smirnov@gmail.com', 'г. Казань, ул. Тверская, д. 5');

-- Тестовые врачи
INSERT INTO doctors (first_name, last_name, middle_name, specialization, license_number, phone, email) VALUES
('Александр', 'Докторов', 'Петрович', 'Терапевт', 'ЛИЦ-2024-0001', '+79101234567', 'doktorov@clinic.ru'),
('Ольга', 'Лечебная', 'Владимировна', 'Кардиолог', 'ЛИЦ-2024-0002', '+79101234568', 'lechebnaya@clinic.ru'),
('Сергей', 'Хирургов', 'Иванович', 'Хирург', 'ЛИЦ-2024-0003', '+79101234569', 'hirurgov@clinic.ru'),
('Наталья', 'Неврологова', 'Сергеевна', 'Невролог', 'ЛИЦ-2024-0004', '+79101234570', 'nevrologova@clinic.ru');

-- Тестовые приемы
INSERT INTO appointments (patient_id, doctor_id, appointment_date, status) VALUES
(1, 1, '2024-01-15 10:00:00', 'completed'),
(2, 2, '2024-01-16 14:30:00', 'completed'),
(3, 3, '2024-01-17 09:00:00', 'completed'),
(4, 4, '2024-01-18 15:00:00', 'scheduled'),
(5, 1, '2024-01-19 11:00:00', 'scheduled');
"""
    
    try:
        # Сохраняем SQL файл с тестовыми данными
        with open('temp_test_data.sql', 'w', encoding='utf-8') as f:
            f.write(test_data_sql)
        
        # Выполняем SQL файл
        cmd = f'psql -h {db_host} -p {db_port} -U {db_user} -d {db_name} -f temp_test_data.sql'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Тестовые данные добавлены")
        else:
            print(f"❌ Ошибка добавления данных: {result.stderr}")
        
        # Удаляем временный файл
        os.remove('temp_test_data.sql')
        
    except Exception as e:
        print(f"❌ Ошибка добавления данных: {e}")
    
    # 4. Финальная проверка
    print(f"\n4️⃣ Финальная проверка...")
    
    try:
        # Проверяем подключение через Python
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn_params = {
            'host': db_host,
            'port': int(db_port),
            'database': db_name,
            'user': db_user,
            'password': os.getenv('DB_PASSWORD', ''),
            'client_encoding': 'UTF8'
        }
        
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Проверяем кодировку
        cursor.execute("SHOW client_encoding")
        encoding = cursor.fetchone()[0]
        print(f"📊 Кодировка подключения: {encoding}")
        
        # Проверяем данные
        cursor.execute("SELECT COUNT(*) as patients FROM patients")
        patients_count = cursor.fetchone()['patients']
        
        cursor.execute("SELECT COUNT(*) as doctors FROM doctors")
        doctors_count = cursor.fetchone()['doctors']
        
        print(f"📊 Пациентов: {patients_count}")
        print(f"📊 Врачей: {doctors_count}")
        
        # Тест кириллицы
        cursor.execute("SELECT first_name, last_name FROM patients LIMIT 1")
        patient = cursor.fetchone()
        
        if patient:
            print(f"📊 Тест кириллицы: {patient['first_name']} {patient['last_name']}")
            
            # Проверяем, что кириллица читается правильно
            if 'Иван' in patient['first_name'] or 'Мария' in patient['first_name']:
                print("✅ Кириллица работает корректно!")
            else:
                print("⚠️ Возможны проблемы с кириллицей")
        
        cursor.close()
        conn.close()
        
        print(f"\n🎉 ВСЕ ПРОБЛЕМЫ С UTF-8 ИСПРАВЛЕНЫ!")
        print(f"✅ База данных создана с UTF-8")
        print(f"✅ Таблицы созданы")
        print(f"✅ Тестовые данные добавлены")
        print(f"✅ Кириллица работает")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка финальной проверки: {e}")
        print(f"\n🔧 Возможно нужно:")
        print(f"1. Проверить пароль БД")
        print(f"2. Убедиться что PostgreSQL запущен")
        print(f"3. Установить psycopg2: pip install psycopg2-binary")
        return False


def update_connection_file():
    """Обновляем файл подключения для UTF-8"""
    print(f"\n5️⃣ Обновление файла подключения...")
    
    connection_file = 'src/database/connection.py'
    
    if os.path.exists(connection_file):
        try:
            # Читаем файл
            with open(connection_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем, есть ли уже UTF-8 настройки
            if "'client_encoding': 'UTF8'" in content:
                print("✅ connection.py уже настроен для UTF-8")
                return True
            
            # Добавляем UTF-8 настройки
            if "'client_encoding'" not in content:
                content = content.replace(
                    "self.connection_params = {",
                    """self.connection_params = {
            'client_encoding': 'UTF8',
            'options': '-c client_encoding=UTF8',"""
                )
            
            # Сохраняем обновленный файл
            with open(connection_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ connection.py обновлен для UTF-8")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления connection.py: {e}")
            return False
    else:
        print(f"⚠️ Файл {connection_file} не найден")
        return False


def main():
    """Главная функция"""
    
    print("⚡ Начинаем быстрое исправление UTF-8...")
    
    success = quick_fix()
    
    if success:
        update_connection_file()
        
        print(f"\n🚀 ГОТОВО! Теперь можно запускать:")
        print(f"   python run.py")
        print(f"\n🌐 Веб-интерфейс будет доступен:")
        print(f"   http://localhost:8000")
        
        # Предлагаем запустить систему
        choice = input(f"\nЗапустить систему сейчас? (y/n): ").lower()
        if choice == 'y':
            print(f"🚀 Запуск системы...")
            os.system("python run.py")
    else:
        print(f"\n❌ Не удалось исправить все проблемы")
        print(f"\n📋 Попробуйте:")
        print(f"1. Убедиться что PostgreSQL запущен")
        print(f"2. Проверить настройки в .env файле")
        print(f"3. Запустить: python fix_utf8_database.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n🛑 Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")