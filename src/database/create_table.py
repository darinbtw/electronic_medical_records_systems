import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

def create_database_tables():
    """Создание всех таблиц базы данных"""
    
    # Параметры подключения
    connection_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'medical_records'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    # SQL команды для создания таблиц
    create_tables_sql = """
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
    """
    
    # SQL для создания функции и триггера
    create_trigger_sql = """
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
    """
    
    # SQL для создания индексов
    create_indexes_sql = """
    -- Создание индексов
    CREATE INDEX IF NOT EXISTS idx_patients_name ON patients(last_name, first_name);
    CREATE INDEX IF NOT EXISTS idx_patients_birth_date ON patients(birth_date);
    CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
    CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
    CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);
    """
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        print("Подключение к базе данных установлено")
        
        # Создаем таблицы
        print("Создание таблиц...")
        cursor.execute(create_tables_sql)
        conn.commit()
        print("Таблицы созданы")
        
        # Создаем триггер
        print("Создание триггера...")
        cursor.execute(create_trigger_sql)
        conn.commit()
        print("Триггер создан")
        
        # Создаем индексы
        print("Создание индексов...")
        cursor.execute(create_indexes_sql)
        conn.commit()
        print("Индексы созданы")
        
        # Проверяем созданные таблицы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("\nСозданные таблицы:")
        for table in tables:
            print(f"  - {table[0]}")
            
    except psycopg2.Error as e:
        print(f"Ошибка PostgreSQL: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("\nСоединение закрыто")

if __name__ == "__main__":
    create_database_tables()