-- Таблица пациентов
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
    license_number VARCHAR(50) UNIQUE NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Каскадное удаление для безопасности
CREATE TABLE appointments(
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE RESTRICT,
    appointment_date TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_appointment UNIQUE (patient_id, doctor_id, appointment_date)
);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_patients_updated_at BEFORE UPDATE
    ON patients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Таблица медицинских записей
CREATE TABLE medical_records(
    id SERIAL PRIMARY KEY,
    appointment_id INTEGER NOT NULL REFERENCES appointments(id),
    diagnosis_encrypted BYTEA,
    diagnosis_iv BYTEA,
    complaints TEXT,
    examination_results TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
);

-- Таблица назначений
CREATE TABLE prescriptions(
    id SERIAL PRIMARY KEY,
    medical_record_id INTEGER NOT NULL REFERENCES medical_records(id),
    medication_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100),
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