-- Таблица пицентов
CREATE TABLE patients (
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
CREATE TABLE doctors(
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    specialization VARCHAR(200) NOT NULL,
    license_number VARCHAR(50) UNIQUE NOT NULL,-- номер лицензиии врача после получения права на мед. деятельность
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица приемов
CREATE TABLE appointments(
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCECS patients(id),
    doctors_id INTEGER NOT NULL REFERENCECS doctors(id),
    appointment_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uniqie_appointment UNIQUE (patient_id, appointment_date, doctors_id),
);

-- Таблица медицинских записей
CREATE TABLE medical_records(
    id SERIAL PRIMARY KEY,
    appointment_id INTEGER NOT NULL REFERENCECS appointments(id),
    diagnosis_encrypted BYTEA, -- Зашифрованный диагноз
    diagnosis_iv BYTEA, -- Вектор инициализации для AES
    complaints TEXT,
    examination_results TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
);

-- Таблица назначений
CREATE TABLE prescriptions(
    id SERIAL PRIMARY KEY,
    medical_record_id INTEGER NOT NULL REFERENCECS medical_records(id),
    medication_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100),
    duration VARCHAR(100),
    notes TEXT
);

-- Создание индексов
CREATE INDEX idx_patients_name ON patients(last_name, first_name);
CREATE INDEX idx_patients_birth_date ON patients(birth_date);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);