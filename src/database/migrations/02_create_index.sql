-- Индексы для таблицы patients (пациенты)
-- =====================================================

-- Основной индекс для поиска по ФИО (используется в web_interface.html)
CREATE INDEX IF NOT EXISTS idx_patients_name 
ON patients(last_name, first_name);

-- Индекс для поиска по дате рождения (возрастные группы)
CREATE INDEX IF NOT EXISTS idx_patients_birth_date 
ON patients(birth_date);

-- Индекс для поиска по полу (статистика)
CREATE INDEX IF NOT EXISTS idx_patients_gender 
ON patients(gender);

-- Индекс для поиска по email (уникальные пользователи)
CREATE INDEX IF NOT EXISTS idx_patients_email 
ON patients(email) WHERE email IS NOT NULL;

-- Индекс для поиска по телефону
CREATE INDEX IF NOT EXISTS idx_patients_phone 
ON patients(phone) WHERE phone IS NOT NULL;

-- Составной индекс для фильтрации по полу и возрасту
CREATE INDEX IF NOT EXISTS idx_patients_gender_birth 
ON patients(gender, birth_date);

-- Индекс для сортировки по дате создания
CREATE INDEX IF NOT EXISTS idx_patients_created_at 
ON patients(created_at DESC);


-- Индексы для таблицы doctors (врачи)
-- =====================================================

-- Индекс для поиска врачей по ФИО
CREATE INDEX IF NOT EXISTS idx_doctors_name 
ON doctors(last_name, first_name);

-- Индекс для поиска по специализации (выбор врача в интерфейсе)
CREATE INDEX IF NOT EXISTS idx_doctors_specialization 
ON doctors(specialization);

-- Уникальный индекс для номера лицензии (уже есть в constraint, но для быстрого поиска)
CREATE INDEX IF NOT EXISTS idx_doctors_license 
ON doctors(license_number);

-- Индекс для поиска по email врача
CREATE INDEX IF NOT EXISTS idx_doctors_email 
ON doctors(email) WHERE email IS NOT NULL;


-- Индексы для таблицы appointments (приемы)
-- =====================================================

-- Основной индекс для поиска приемов по дате (расписание)
CREATE INDEX IF NOT EXISTS idx_appointments_date 
ON appointments(appointment_date DESC);

-- Индекс для поиска приемов конкретного пациента
CREATE INDEX IF NOT EXISTS idx_appointments_patient 
ON appointments(patient_id, appointment_date DESC);

-- Индекс для поиска приемов конкретного врача
CREATE INDEX IF NOT EXISTS idx_appointments_doctor 
ON appointments(doctor_id, appointment_date DESC);

-- Индекс для фильтрации по статусу приема
CREATE INDEX IF NOT EXISTS idx_appointments_status 
ON appointments(status, appointment_date DESC);

-- Составной индекс для поиска приемов пациента у врача
CREATE INDEX IF NOT EXISTS idx_appointments_patient_doctor 
ON appointments(patient_id, doctor_id, appointment_date DESC);

-- Индекс для поиска приемов по дате и статусу (веб-интерфейс)
CREATE INDEX IF NOT EXISTS idx_appointments_date_status 
ON appointments(appointment_date, status);

-- Индекс для поиска приемов в определенный день
CREATE INDEX IF NOT EXISTS idx_appointments_date_only 
ON appointments(DATE(appointment_date));


-- Индексы для таблицы medical_records (медицинские записи)
-- =====================================================

-- Индекс для связи с приемом (один к одному)
CREATE UNIQUE INDEX IF NOT EXISTS idx_medical_records_appointment 
ON medical_records(appointment_id);

-- Индекс для поиска записей по дате создания
CREATE INDEX IF NOT EXISTS idx_medical_records_created_at 
ON medical_records(created_at DESC);

-- Индекс для поиска записей с диагнозами
CREATE INDEX IF NOT EXISTS idx_medical_records_diagnosis 
ON medical_records(id) WHERE diagnosis_encrypted IS NOT NULL;

-- Частичный индекс для записей с жалобами
CREATE INDEX IF NOT EXISTS idx_medical_records_complaints 
ON medical_records(id) WHERE complaints IS NOT NULL AND complaints != '';


-- Индексы для таблицы prescriptions (назначения)
-- =====================================================

-- Индекс для поиска назначений по медицинской записи
CREATE INDEX IF NOT EXISTS idx_prescriptions_medical_record 
ON prescriptions(medical_record_id);

-- Индекс для поиска по названию препарата (статистика)
CREATE INDEX IF NOT EXISTS idx_prescriptions_medication 
ON prescriptions(medication_name);

-- Составной индекс для поиска назначений конкретного препарата в записи
CREATE INDEX IF NOT EXISTS idx_prescriptions_record_medication 
ON prescriptions(medical_record_id, medication_name);


-- Полнотекстовые индексы для поиска (PostgreSQL)
-- =====================================================

-- Полнотекстовый поиск по ФИО пациентов (русский язык)
CREATE INDEX IF NOT EXISTS idx_patients_fulltext 
ON patients USING gin(to_tsvector('russian', 
    COALESCE(last_name, '') || ' ' || 
    COALESCE(first_name, '') || ' ' || 
    COALESCE(middle_name, '')
));

-- Полнотекстовый поиск по ФИО врачей
CREATE INDEX IF NOT EXISTS idx_doctors_fulltext 
ON doctors USING gin(to_tsvector('russian', 
    COALESCE(last_name, '') || ' ' || 
    COALESCE(first_name, '') || ' ' || 
    COALESCE(middle_name, '') || ' ' || 
    COALESCE(specialization, '')
));

-- Полнотекстовый поиск по жалобам и результатам осмотра
CREATE INDEX IF NOT EXISTS idx_medical_records_fulltext 
ON medical_records USING gin(to_tsvector('russian', 
    COALESCE(complaints, '') || ' ' || 
    COALESCE(examination_results, '')
));


-- Составные индексы для оптимизации сложных запросов
-- =====================================================

-- Для запросов "приемы пациента за период"
CREATE INDEX IF NOT EXISTS idx_appointments_patient_period 
ON appointments(patient_id, appointment_date, status) 
WHERE status IN ('completed', 'scheduled');

-- Для запросов "приемы врача за день"
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_day 
ON appointments(doctor_id, DATE(appointment_date), status);

-- Для поиска свободного времени врача
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_schedule 
ON appointments(doctor_id, appointment_date) 
WHERE status != 'cancelled';


-- Индексы для производительности веб-интерфейса
-- =====================================================

-- Для пагинации пациентов (сортировка по фамилии)
CREATE INDEX IF NOT EXISTS idx_patients_pagination 
ON patients(last_name, first_name, id);

-- Для пагинации приемов (сортировка по дате убывания)
CREATE INDEX IF NOT EXISTS idx_appointments_pagination 
ON appointments(appointment_date DESC, id);

-- Для пагинации медицинских записей
CREATE INDEX IF NOT EXISTS idx_medical_records_pagination 
ON medical_records(created_at DESC, id);


-- Обновление статистики для оптимизатора запросов
-- =====================================================
ANALYZE patients;
ANALYZE doctors;
ANALYZE appointments;
ANALYZE medical_records;
ANALYZE prescriptions;

-- Информация о созданных индексах
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes 
    WHERE schemaname = 'public' 
    AND indexname LIKE 'idx_%';
    
    RAISE NOTICE 'Создано индексов: %', index_count;
    RAISE NOTICE 'Индексы оптимизируют:';
    RAISE NOTICE '  ✅ Поиск пациентов по ФИО';
    RAISE NOTICE '  ✅ Фильтрацию приемов по дате и статусу';
    RAISE NOTICE '  ✅ Поиск врачей по специализации';
    RAISE NOTICE '  ✅ Полнотекстовый поиск на русском языке';
    RAISE NOTICE '  ✅ Пагинацию в веб-интерфейсе';
    RAISE NOTICE '  ✅ Связи между таблицами (FK)';
    RAISE NOTICE '  ✅ Статистические запросы';
END $$;