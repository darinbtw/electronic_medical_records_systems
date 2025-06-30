-- Проверочные ограничения (CHECK constraints)
-- =====================================================

-- Ограничения для таблицы patients
-- =====================================================

-- Проверка корректности даты рождения
ALTER TABLE patients 
ADD CONSTRAINT chk_patients_birth_date 
CHECK (
    birth_date >= '1900-01-01' 
    AND birth_date <= CURRENT_DATE
);

-- Проверка корректности пола
ALTER TABLE patients 
ADD CONSTRAINT chk_patients_gender 
CHECK (gender IN ('M', 'F'));

-- Проверка формата телефона (российские номера)
ALTER TABLE patients 
ADD CONSTRAINT chk_patients_phone_format 
CHECK (
    phone IS NULL 
    OR phone ~ '^\+?[78][0-9\s\-\(\)]{10,15}$'
);

-- Проверка формата email
ALTER TABLE patients 
ADD CONSTRAINT chk_patients_email_format 
CHECK (
    email IS NULL 
    OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
);

-- Проверка что имя и фамилия не пустые
ALTER TABLE patients 
ADD CONSTRAINT chk_patients_names_not_empty 
CHECK (
    LENGTH(TRIM(first_name)) > 0 
    AND LENGTH(TRIM(last_name)) > 0
);

-- Проверка возраста (не более 150 лет)
ALTER TABLE patients 
ADD CONSTRAINT chk_patients_reasonable_age 
CHECK (
    DATE_PART('year', AGE(birth_date)) <= 150
);


-- Ограничения для таблицы doctors
-- =====================================================

-- Проверка формата номера лицензии
ALTER TABLE doctors 
ADD CONSTRAINT chk_doctors_license_format 
CHECK (
    license_number ~ '^[А-Я]{3}-[0-9]{4}-[0-9]{4}$'
    OR license_number ~ '^LIC-[0-9]{4}-[0-9]{3,4}$'
    OR license_number ~ '^ЛИЦ-[0-9]{4}-[0-9]{4}$'
);

-- Проверка что специализация не пустая
ALTER TABLE doctors 
ADD CONSTRAINT chk_doctors_specialization_not_empty 
CHECK (LENGTH(TRIM(specialization)) > 0);

-- Проверка формата телефона врача
ALTER TABLE doctors 
ADD CONSTRAINT chk_doctors_phone_format 
CHECK (
    phone IS NULL 
    OR phone ~ '^\+?[78][0-9\s\-\(\)]{10,15}$'
);

-- Проверка формата email врача
ALTER TABLE doctors 
ADD CONSTRAINT chk_doctors_email_format 
CHECK (
    email IS NULL 
    OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
);

-- Проверка что имена врачей не пустые
ALTER TABLE doctors 
ADD CONSTRAINT chk_doctors_names_not_empty 
CHECK (
    LENGTH(TRIM(first_name)) > 0 
    AND LENGTH(TRIM(last_name)) > 0
);


-- Ограничения для таблицы appointments
-- =====================================================

-- Проверка статуса приема
ALTER TABLE appointments 
ADD CONSTRAINT chk_appointments_status 
CHECK (status IN ('scheduled', 'completed', 'cancelled'));

-- Проверка что дата приема не в прошлом (для новых записей)
-- Используем функцию для гибкости
CREATE OR REPLACE FUNCTION validate_appointment_date() 
RETURNS TRIGGER AS $$
BEGIN
    -- Разрешаем изменение статуса для существующих записей
    IF TG_OP = 'UPDATE' AND OLD.appointment_date = NEW.appointment_date THEN
        RETURN NEW;
    END IF;
    
    -- Для новых записей проверяем дату
    IF NEW.appointment_date < CURRENT_TIMESTAMP - INTERVAL '1 hour' THEN
        RAISE EXCEPTION 'Нельзя создать прием в прошлом (дата: %)', NEW.appointment_date;
    END IF;
    
    -- Проверяем рабочие часы (9:00 - 18:00)
    IF EXTRACT(HOUR FROM NEW.appointment_date) < 9 
       OR EXTRACT(HOUR FROM NEW.appointment_date) >= 18 THEN
        RAISE EXCEPTION 'Приемы возможны только с 09:00 до 18:00';
    END IF;
    
    -- Проверяем рабочие дни (понедельник-пятница)
    IF EXTRACT(DOW FROM NEW.appointment_date) IN (0, 6) THEN
        RAISE EXCEPTION 'Приемы возможны только в рабочие дни (пн-пт)';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Создаем триггер для проверки даты приема
DROP TRIGGER IF EXISTS trg_validate_appointment_date ON appointments;
CREATE TRIGGER trg_validate_appointment_date
    BEFORE INSERT OR UPDATE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION validate_appointment_date();

-- Проверка что пациент и врач разные (на всякий случай)
ALTER TABLE appointments 
ADD CONSTRAINT chk_appointments_different_ids 
CHECK (patient_id != doctor_id);


-- Ограничения для таблицы medical_records
-- =====================================================

-- Проверка что есть либо зашифрованный диагноз, либо обычное поле
ALTER TABLE medical_records 
ADD CONSTRAINT chk_medical_records_diagnosis_consistency 
CHECK (
    (diagnosis_encrypted IS NOT NULL AND diagnosis_iv IS NOT NULL)
    OR (diagnosis_encrypted IS NULL AND diagnosis_iv IS NULL)
);

-- Проверка что жалобы не пустые (если указаны)
ALTER TABLE medical_records 
ADD CONSTRAINT chk_medical_records_complaints_not_empty 
CHECK (
    complaints IS NULL 
    OR LENGTH(TRIM(complaints)) > 0
);

-- Проверка что результаты осмотра не пустые (если указаны)
ALTER TABLE medical_records 
ADD CONSTRAINT chk_medical_records_examination_not_empty 
CHECK (
    examination_results IS NULL 
    OR LENGTH(TRIM(examination_results)) > 0
);

-- Функция для проверки связанности с завершенным приемом
CREATE OR REPLACE FUNCTION validate_medical_record_appointment() 
RETURNS TRIGGER AS $$
DECLARE
    appointment_status VARCHAR(20);
BEGIN
    -- Получаем статус приема
    SELECT status INTO appointment_status
    FROM appointments 
    WHERE id = NEW.appointment_id;
    
    -- Медицинскую запись можно создать только для завершенного приема
    IF appointment_status != 'completed' THEN
        RAISE EXCEPTION 'Медицинская запись может быть создана только для завершенного приема';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для проверки статуса приема при создании медзаписи
DROP TRIGGER IF EXISTS trg_validate_medical_record_appointment ON medical_records;
CREATE TRIGGER trg_validate_medical_record_appointment
    BEFORE INSERT ON medical_records
    FOR EACH ROW
    EXECUTE FUNCTION validate_medical_record_appointment();


-- Ограничения для таблицы prescriptions
-- =====================================================

-- Проверка что название препарата не пустое
ALTER TABLE prescriptions 
ADD CONSTRAINT chk_prescriptions_medication_not_empty 
CHECK (LENGTH(TRIM(medication_name)) > 0);

-- Проверка формата дозировки (если указана)
ALTER TABLE prescriptions 
ADD CONSTRAINT chk_prescriptions_dosage_format 
CHECK (
    dosage IS NULL 
    OR dosage ~ '^[0-9]+(\.[0-9]+)?\s*(мг|г|мл|ед|таб|капс|кап)\.?$'
);

-- Проверка частоты приема
ALTER TABLE prescriptions 
ADD CONSTRAINT chk_prescriptions_frequency_format 
CHECK (
    frequency IS NULL 
    OR frequency ~ '.*(раз|день|утр|веч|ноч|необходим|час).*'
);

-- Проверка длительности лечения
ALTER TABLE prescriptions 
ADD CONSTRAINT chk_prescriptions_duration_format 
CHECK (
    duration IS NULL 
    OR duration ~ '.*(день|недел|месяц|час|постоянно).*'
);


-- Дополнительные ограничения целостности
-- =====================================================

-- Ограничение уникальности email пациентов (если указан)
ALTER TABLE patients 
ADD CONSTRAINT uq_patients_email_not_null 
UNIQUE (email);

-- Ограничение уникальности email врачей (если указан)  
ALTER TABLE doctors 
ADD CONSTRAINT uq_doctors_email_not_null 
UNIQUE (email);

-- Ограничение: один пациент не может иметь более 5 приемов в день
CREATE OR REPLACE FUNCTION limit_daily_appointments() 
RETURNS TRIGGER AS $$
DECLARE
    daily_count INTEGER;
    appointment_date_only DATE;
BEGIN
    appointment_date_only := DATE(NEW.appointment_date);
    
    SELECT COUNT(*) INTO daily_count
    FROM appointments 
    WHERE patient_id = NEW.patient_id 
    AND DATE(appointment_date) = appointment_date_only
    AND status != 'cancelled'
    AND (TG_OP = 'INSERT' OR id != NEW.id);
    
    IF daily_count >= 5 THEN
        RAISE EXCEPTION 'Пациент не может иметь более 5 приемов в день';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер ограничения приемов в день
DROP TRIGGER IF EXISTS trg_limit_daily_appointments ON appointments;
CREATE TRIGGER trg_limit_daily_appointments
    BEFORE INSERT OR UPDATE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION limit_daily_appointments();

-- Ограничение: врач не может иметь более 20 приемов в день
CREATE OR REPLACE FUNCTION limit_doctor_daily_appointments() 
RETURNS TRIGGER AS $$
DECLARE
    daily_count INTEGER;
    appointment_date_only DATE;
BEGIN
    appointment_date_only := DATE(NEW.appointment_date);
    
    SELECT COUNT(*) INTO daily_count
    FROM appointments 
    WHERE doctor_id = NEW.doctor_id 
    AND DATE(appointment_date) = appointment_date_only
    AND status != 'cancelled'
    AND (TG_OP = 'INSERT' OR id != NEW.id);
    
    IF daily_count >= 20 THEN
        RAISE EXCEPTION 'Врач не может иметь более 20 приемов в день';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер ограничения приемов врача в день
DROP TRIGGER IF EXISTS trg_limit_doctor_daily_appointments ON appointments;
CREATE TRIGGER trg_limit_doctor_daily_appointments
    BEFORE INSERT OR UPDATE ON appointments
    FOR EACH ROW
    EXECUTE FUNCTION limit_doctor_daily_appointments();


-- Проверка целостности данных
-- =====================================================

-- Функция для проверки консистентности шифрования
CREATE OR REPLACE FUNCTION validate_encryption_consistency() 
RETURNS TRIGGER AS $$
BEGIN
    -- Если есть зашифрованные данные, должен быть и IV
    IF (NEW.diagnosis_encrypted IS NOT NULL AND NEW.diagnosis_iv IS NULL) 
       OR (NEW.diagnosis_encrypted IS NULL AND NEW.diagnosis_iv IS NOT NULL) THEN
        RAISE EXCEPTION 'Нарушена консистентность шифрования: diagnosis_encrypted и diagnosis_iv должны быть одновременно NULL или NOT NULL';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер проверки консистентности шифрования
DROP TRIGGER IF EXISTS trg_validate_encryption_consistency ON medical_records;
CREATE TRIGGER trg_validate_encryption_consistency
    BEFORE INSERT OR UPDATE ON medical_records
    FOR EACH ROW
    EXECUTE FUNCTION validate_encryption_consistency();


-- Логирование изменений важных данных
-- =====================================================

-- Таблица аудита для изменений пациентов
CREATE TABLE IF NOT EXISTS patients_audit (
    audit_id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    operation CHAR(1) NOT NULL, -- I, U, D
    old_data JSONB,
    new_data JSONB,
    changed_by TEXT DEFAULT current_user,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Функция аудита пациентов
CREATE OR REPLACE FUNCTION audit_patients() 
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO patients_audit (patient_id, operation, old_data)
        VALUES (OLD.id, 'D', row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO patients_audit (patient_id, operation, old_data, new_data)
        VALUES (NEW.id, 'U', row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO patients_audit (patient_id, operation, new_data)
        VALUES (NEW.id, 'I', row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Триггер аудита пациентов
DROP TRIGGER IF EXISTS trg_audit_patients ON patients;
CREATE TRIGGER trg_audit_patients
    AFTER INSERT OR UPDATE OR DELETE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION audit_patients();


-- Информация о созданных ограничениях
-- =====================================================
DO $$
DECLARE
    constraint_count INTEGER;
    trigger_count INTEGER;
BEGIN
    -- Считаем ограничения
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.table_constraints 
    WHERE table_schema = 'public' 
    AND constraint_name LIKE 'chk_%';
    
    -- Считаем триггеры
    SELECT COUNT(*) INTO trigger_count
    FROM information_schema.triggers 
    WHERE trigger_schema = 'public'
    AND trigger_name LIKE 'trg_%';
    
    RAISE NOTICE 'Создано ограничений CHECK: %', constraint_count;
    RAISE NOTICE 'Создано триггеров: %', trigger_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Ограничения обеспечивают:';
    RAISE NOTICE '  ✅ Корректность дат рождения и приемов';
    RAISE NOTICE '  ✅ Валидацию форматов телефонов и email';
    RAISE NOTICE '  ✅ Проверку рабочих часов (9:00-18:00)';
    RAISE NOTICE '  ✅ Ограничение приемов в день (пациент: 5, врач: 20)';
    RAISE NOTICE '  ✅ Консистентность шифрования диагнозов';
    RAISE NOTICE '  ✅ Аудит изменений критичных данных';
    RAISE NOTICE '  ✅ Бизнес-правила медицинского учреждения';
END $$;