-- Создание базы данных
CREATE DATABASE medical_records_db;

-- Подключение к базе данных
\c medical_records_db;

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Таблица пациентов
CREATE TABLE patients (
    patient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    date_of_birth DATE NOT NULL,
    gender CHAR(1) CHECK (gender IN ('M', 'F')),
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    insurance_number VARCHAR(50) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица врачей
CREATE TABLE doctors (
    doctor_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    specialization VARCHAR(100) NOT NULL,
    license_number VARCHAR(50) UNIQUE NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица отделений
CREATE TABLE departments (
    department_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица медицинских записей
CREATE TABLE medical_records (
    record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctors(doctor_id),
    department_id UUID REFERENCES departments(department_id),
    visit_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    diagnosis_encrypted TEXT, -- Зашифрованный диагноз
    symptoms TEXT,
    examination_results TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица типов назначений
CREATE TABLE appointment_types (
    type_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Таблица назначений
CREATE TABLE appointments (
    appointment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    record_id UUID NOT NULL REFERENCES medical_records(record_id) ON DELETE CASCADE,
    type_id UUID NOT NULL REFERENCES appointment_types(type_id),
    description TEXT NOT NULL,
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    duration VARCHAR(100),
    status VARCHAR(20) DEFAULT 'назначено' CHECK (status IN ('назначено', 'выполнено', 'отменено')),
    appointment_date DATE NOT NULL,
    completion_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица аудита
CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id UUID NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);