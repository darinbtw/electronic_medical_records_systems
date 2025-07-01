-- =====================================================
-- Миграция базы данных для добавления TDE полей
-- =====================================================

-- Добавляем TDE поля для таблицы patients
DO $$
BEGIN
    -- Добавляем поля для шифрования телефона
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'patients' AND column_name = 'phone_encrypted'
    ) THEN
        ALTER TABLE patients ADD COLUMN phone_encrypted BYTEA;
        RAISE NOTICE 'Добавлен столбец phone_encrypted';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'patients' AND column_name = 'phone_iv'
    ) THEN
        ALTER TABLE patients ADD COLUMN phone_iv BYTEA;
        RAISE NOTICE 'Добавлен столбец phone_iv';
    END IF;

    -- Добавляем поля для шифрования email
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'patients' AND column_name = 'email_encrypted'
    ) THEN
        ALTER TABLE patients ADD COLUMN email_encrypted BYTEA;
        RAISE NOTICE 'Добавлен столбец email_encrypted';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'patients' AND column_name = 'email_iv'
    ) THEN
        ALTER TABLE patients ADD COLUMN email_iv BYTEA;
        RAISE NOTICE 'Добавлен столбец email_iv';
    END IF;

    -- Добавляем поля для шифрования адреса
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'patients' AND column_name = 'address_encrypted'
    ) THEN
        ALTER TABLE patients ADD COLUMN address_encrypted BYTEA;
        RAISE NOTICE 'Добавлен столбец address_encrypted';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'patients' AND column_name = 'address_iv'
    ) THEN
        ALTER TABLE patients ADD COLUMN address_iv BYTEA;
        RAISE NOTICE 'Добавлен столбец address_iv';
    END IF;
END $$;

-- Добавляем TDE поля для таблицы doctors
DO $$
BEGIN
    -- Добавляем поля для шифрования телефона врача
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'doctors' AND column_name = 'phone_encrypted'
    ) THEN
        ALTER TABLE doctors ADD COLUMN phone_encrypted BYTEA;
        RAISE NOTICE 'Добавлен столбец doctors.phone_encrypted';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'doctors' AND column_name = 'phone_iv'
    ) THEN
        ALTER TABLE doctors ADD COLUMN phone_iv BYTEA;
        RAISE NOTICE 'Добавлен столбец doctors.phone_iv';
    END IF;

    -- Добавляем поля для шифрования email врача
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'doctors' AND column_name = 'email_encrypted'
    ) THEN
        ALTER TABLE doctors ADD COLUMN email_encrypted BYTEA;
        RAISE NOTICE 'Добавлен столбец doctors.email_encrypted';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'doctors' AND column_name = 'email_iv'
    ) THEN
        ALTER TABLE doctors ADD COLUMN email_iv BYTEA;
        RAISE NOTICE 'Добавлен столбец doctors.email_iv';
    END IF;
END $;

-- Добавляем TDE поля для таблицы medical_records
DO $
BEGIN
    -- Проверяем, есть ли уже поля для диагноза
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'medical_records' AND column_name = 'diagnosis_encrypted'
    ) THEN
        ALTER TABLE medical_records ADD COLUMN diagnosis_encrypted BYTEA;
        RAISE NOTICE 'Добавлен столбец diagnosis_encrypted';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'medical_records' AND column_name = 'diagnosis_iv'
    ) THEN
        ALTER TABLE medical_records ADD COLUMN diagnosis_iv BYTEA;
        RAISE NOTICE 'Добавлен столбец diagnosis_iv';
    END IF;

    -- Добавляем поля для шифрования жалоб
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'medical_records' AND column_name = 'complaints_encrypted'
    ) THEN
        ALTER TABLE medical_records ADD COLUMN complaints_encrypted BYTEA;
        RAISE NOTICE 'Добавлен столбец complaints_encrypted';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'medical_records' AND column_name = 'complaints_iv'
    ) THEN
        ALTER TABLE medical_records ADD COLUMN complaints_iv BYTEA;
        RAISE NOTICE 'Добавлен столбец complaints_iv';
    END IF;

    -- Добавляем поля для шифрования результатов осмотра
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'medical_records' AND column_name = 'examination_results_encrypted'
    ) THEN
        ALTER TABLE medical_records ADD COLUMN examination_results_encrypted BYTEA;
        RAISE NOTICE 'Добавлен столбец examination_results_encrypted';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'medical_records' AND column_name = 'examination_results_iv'
    ) THEN
        ALTER TABLE medical_records ADD COLUMN examination_results_iv BYTEA;
        RAISE NOTICE 'Добавлен столбец examination_results_iv';
    END IF;
END $;

-- Добавляем TDE поля для таблицы prescriptions
DO $
BEGIN
    -- Добавляем поля для шифрования примечаний к назначениям
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'prescriptions' AND column_name = 'notes_encrypted'
    ) THEN
        ALTER TABLE prescriptions ADD COLUMN notes_encrypted BYTEA;
        RAISE NOTICE 'Добавлен столбец prescriptions.notes_encrypted';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'prescriptions' AND column_name = 'notes_iv'
    ) THEN
        ALTER TABLE prescriptions ADD COLUMN notes_iv BYTEA;
        RAISE NOTICE 'Добавлен столбец prescriptions.notes_iv';
    END IF;
END $;

-- Создаем индексы для TDE полей
CREATE INDEX IF NOT EXISTS idx_patients_phone_encrypted 
ON patients(phone_encrypted) WHERE phone_encrypted IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_patients_email_encrypted 
ON patients(email_encrypted) WHERE email_encrypted IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_patients_address_encrypted 
ON patients(address_encrypted) WHERE address_encrypted IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_doctors_phone_encrypted 
ON doctors(phone_encrypted) WHERE phone_encrypted IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_doctors_email_encrypted 
ON doctors(email_encrypted) WHERE email_encrypted IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_medical_records_diagnosis_encrypted 
ON medical_records(diagnosis_encrypted) WHERE diagnosis_encrypted IS NOT NULL;

-- Добавляем ограничения для консистентности TDE
ALTER TABLE patients 
ADD CONSTRAINT chk_patients_phone_tde_consistency 
CHECK (
    (phone_encrypted IS NULL AND phone_iv IS NULL) 
    OR (phone_encrypted IS NOT NULL AND phone_iv IS NOT NULL)
);

ALTER TABLE patients 
ADD CONSTRAINT chk_patients_email_tde_consistency 
CHECK (
    (email_encrypted IS NULL AND email_iv IS NULL) 
    OR (email_encrypted IS NOT NULL AND email_iv IS NOT NULL)
);

ALTER TABLE patients 
ADD CONSTRAINT chk_patients_address_tde_consistency 
CHECK (
    (address_encrypted IS NULL AND address_iv IS NULL) 
    OR (address_encrypted IS NOT NULL AND address_iv IS NOT NULL)
);

ALTER TABLE doctors 
ADD CONSTRAINT chk_doctors_phone_tde_consistency 
CHECK (
    (phone_encrypted IS NULL AND phone_iv IS NULL) 
    OR (phone_encrypted IS NOT NULL AND phone_iv IS NOT NULL)
);

ALTER TABLE doctors 
ADD CONSTRAINT chk_doctors_email_tde_consistency 
CHECK (
    (email_encrypted IS NULL AND email_iv IS NULL) 
    OR (email_encrypted IS NOT NULL AND email_iv IS NOT NULL)
);

ALTER TABLE medical_records 
ADD CONSTRAINT chk_medical_records_diagnosis_tde_consistency 
CHECK (
    (diagnosis_encrypted IS NULL AND diagnosis_iv IS NULL) 
    OR (diagnosis_encrypted IS NOT NULL AND diagnosis_iv IS NOT NULL)
);

-- Комментарии для документации
COMMENT ON COLUMN patients.phone_encrypted IS 'Зашифрованный телефон пациента (TDE)';
COMMENT ON COLUMN patients.phone_iv IS 'Initialization Vector для телефона';
COMMENT ON COLUMN patients.email_encrypted IS 'Зашифрованный email пациента (TDE)';
COMMENT ON COLUMN patients.email_iv IS 'Initialization Vector для email';
COMMENT ON COLUMN patients.address_encrypted IS 'Зашифрованный адрес пациента (TDE)';
COMMENT ON COLUMN patients.address_iv IS 'Initialization Vector для адреса';

COMMENT ON COLUMN doctors.phone_encrypted IS 'Зашифрованный телефон врача (TDE)';
COMMENT ON COLUMN doctors.phone_iv IS 'Initialization Vector для телефона врача';
COMMENT ON COLUMN doctors.email_encrypted IS 'Зашифрованный email врача (TDE)';
COMMENT ON COLUMN doctors.email_iv IS 'Initialization Vector для email врача';

COMMENT ON COLUMN medical_records.diagnosis_encrypted IS 'Зашифрованный диагноз (TDE)';
COMMENT ON COLUMN medical_records.diagnosis_iv IS 'Initialization Vector для диагноза';
COMMENT ON COLUMN medical_records.complaints_encrypted IS 'Зашифрованные жалобы (TDE)';
COMMENT ON COLUMN medical_records.complaints_iv IS 'Initialization Vector для жалоб';
COMMENT ON COLUMN medical_records.examination_results_encrypted IS 'Зашифрованные результаты осмотра (TDE)';
COMMENT ON COLUMN medical_records.examination_results_iv IS 'Initialization Vector для результатов';

COMMENT ON COLUMN prescriptions.notes_encrypted IS 'Зашифрованные примечания к назначению (TDE)';
COMMENT ON COLUMN prescriptions.notes_iv IS 'Initialization Vector для примечаний';

-- Выводим итоговую информацию
DO $
DECLARE
    tde_columns_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO tde_columns_count
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND column_name LIKE '%_encrypted';
    
    RAISE NOTICE '✅ TDE миграция завершена!';
    RAISE NOTICE 'Добавлено зашифрованных полей: %', tde_columns_count;
    RAISE NOTICE 'Таблицы с TDE поддержкой:';
    RAISE NOTICE '  - patients: phone, email, address';
    RAISE NOTICE '  - doctors: phone, email';
    RAISE NOTICE '  - medical_records: diagnosis, complaints, examination_results';
    RAISE NOTICE '  - prescriptions: notes';
    RAISE NOTICE '';
    RAISE NOTICE '🔒 Для активации TDE установите переменную окружения:';
    RAISE NOTICE 'TDE_ENABLED=true';
END $;