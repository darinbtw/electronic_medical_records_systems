-- Генерация данных для схемы с зашифрованными диагнозами

-- Очистка существующих данных
-- TRUNCATE TABLE prescriptions, medical_records, appointments, doctors, patients RESTART IDENTITY CASCADE;

-- Функция для генерации случайного телефона
CREATE OR REPLACE FUNCTION random_phone() RETURNS VARCHAR AS $$
BEGIN
    RETURN '+7' || (900 + floor(random() * 100))::text || 
           (1000000 + floor(random() * 8999999))::text;
END;
$$ LANGUAGE plpgsql;

-- Исправленная функция для генерации уникального email
CREATE OR REPLACE FUNCTION random_email(base_name VARCHAR, unique_id INT) RETURNS VARCHAR AS $$
BEGIN
    RETURN lower(base_name) || '_' || unique_id::text || '_' || floor(random() * 1000)::text || '@' || 
           (ARRAY['mail.ru', 'gmail.com', 'yandex.ru', 'outlook.com', 'rambler.ru'])[floor(random() * 5 + 1)];
END;
$$ LANGUAGE plpgsql;

-- Функция для простого "шифрования" диагноза (имитация)
-- В реальности будет использоваться AES через Python
CREATE OR REPLACE FUNCTION mock_encrypt_diagnosis(diagnosis TEXT) RETURNS BYTEA AS $$
BEGIN
    -- Простое кодирование в Base64 для демонстрации
    -- В реальности это будет AES-256 шифрование
    RETURN encode(diagnosis::bytea, 'base64')::bytea;
END;
$$ LANGUAGE plpgsql;

-- Генерация случайного IV (16 байт)
CREATE OR REPLACE FUNCTION generate_mock_iv() RETURNS BYTEA AS $$
BEGIN
    -- Генерация псевдослучайного IV
    RETURN decode(
        lpad(floor(random() * 16777216)::text, 8, '0') || 
        lpad(floor(random() * 16777216)::text, 8, '0') || 
        lpad(floor(random() * 16777216)::text, 8, '0') || 
        lpad(floor(random() * 16777216)::text, 8, '0'), 
        'hex'
    );
END;
$$ LANGUAGE plpgsql;

-- Генерация 1000 пациентов
INSERT INTO patients (first_name, last_name, middle_name, birth_date, gender, phone, email, address)
SELECT 
    (CASE 
        WHEN gender_choice = 'M' THEN 
            (ARRAY['Иван', 'Петр', 'Сергей', 'Александр', 'Андрей', 'Дмитрий', 'Максим', 'Алексей', 'Николай', 'Владимир'])[1 + floor(random() * 10)]
        ELSE 
            (ARRAY['Анна', 'Мария', 'Елена', 'Наталья', 'Ольга', 'Татьяна', 'Ирина', 'Светлана', 'Екатерина', 'Людмила'])[1 + floor(random() * 10)]
    END) AS first_name,
    (ARRAY['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев', 'Соколов', 'Лебедев', 'Козлов', 'Новиков', 'Морозов'])[1 + floor(random() * 12)] AS last_name,
    (CASE 
        WHEN gender_choice = 'M' THEN 
            (ARRAY['Иванович', 'Петрович', 'Сергеевич', 'Александрович', 'Андреевич', 'Дмитриевич', 'Николаевич', 'Владимирович'])[1 + floor(random() * 8)]
        ELSE 
            (ARRAY['Ивановна', 'Петровна', 'Сергеевна', 'Александровна', 'Андреевна', 'Дмитриевна', 'Николаевна', 'Владимировна'])[1 + floor(random() * 8)]
    END) AS middle_name,
    DATE '1950-01-01' + (random() * (DATE '2005-01-01' - DATE '1950-01-01'))::int AS birth_date,
    gender_choice AS gender,
    random_phone() AS phone,
    random_email('patient', generate_series) AS email,
    'г. ' || (ARRAY['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань', 'Нижний Новгород', 'Челябинск', 'Самара'])[1 + floor(random() * 8)] || 
    ', ул. ' || (ARRAY['Ленина', 'Пушкина', 'Гагарина', 'Мира', 'Победы', 'Советская', 'Молодежная', 'Центральная'])[1 + floor(random() * 8)] || 
    ', д. ' || floor(random() * 100 + 1)::text || 
    CASE WHEN random() > 0.5 THEN ', кв. ' || floor(random() * 200 + 1)::text ELSE '' END AS address
FROM generate_series(1, 1000),
     (SELECT (ARRAY['M', 'F'])[1 + floor(random() * 2)] AS gender_choice) AS gender_subquery;

-- Генерация 50 врачей
INSERT INTO doctors (first_name, last_name, middle_name, specialization, license_number, phone, email)
SELECT
    (CASE 
        WHEN gender_choice = 'M' THEN 
            (ARRAY['Александр', 'Сергей', 'Виктор', 'Михаил', 'Андрей', 'Дмитрий', 'Владимир', 'Игорь', 'Евгений', 'Алексей'])[1 + floor(random() * 10)]
        ELSE 
            (ARRAY['Ольга', 'Наталья', 'Елена', 'Татьяна', 'Марина', 'Ирина', 'Светлана', 'Людмила', 'Галина', 'Вера'])[1 + floor(random() * 10)]
    END) AS first_name,
    (ARRAY['Докторов', 'Медведев', 'Хирургов', 'Терапевтов', 'Кардиологов', 'Неврологов', 'Педиатров', 'Стоматологов', 'Лечебников', 'Здоровьев'])[1 + floor(random() * 10)] AS last_name,
    (CASE 
        WHEN gender_choice = 'M' THEN 
            (ARRAY['Сергеевич', 'Петрович', 'Андреевич', 'Николаевич', 'Михайлович', 'Александрович', 'Владимирович', 'Дмитриевич'])[1 + floor(random() * 8)]
        ELSE 
            (ARRAY['Сергеевна', 'Владимировна', 'Петровна', 'Андреевна', 'Николаевна', 'Ивановна', 'Михайловна', 'Александровна'])[1 + floor(random() * 8)]
    END) AS middle_name,
    (ARRAY['Терапевт', 'Кардиолог', 'Хирург', 'Невролог', 'Педиатр', 'Офтальмолог', 'ЛОР', 'Дерматолог', 'Гинеколог', 'Уролог', 'Эндокринолог', 'Гастроэнтеролог'])[1 + floor(random() * 12)] AS specialization,
    'ЛИЦ-' || to_char(CURRENT_DATE, 'YYYY') || '-' || lpad((5000 + generate_series)::text, 4, '0') AS license_number,
    random_phone() AS phone,
    random_email('doctor', generate_series) AS email
FROM generate_series(1, 50),
     (SELECT (ARRAY['M', 'F'])[1 + floor(random() * 2)] AS gender_choice) AS gender_subquery;

-- Генерация 5000 приемов за последний год
INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
SELECT
    1 + floor(random() * 1000)::int AS patient_id,
    1 + floor(random() * 50)::int AS doctor_id,
    CURRENT_DATE - (random() * 365)::int + 
    (floor(random() * 9 + 9) || ' hours')::interval + -- 9-17 часов
    (floor(random() * 6) * 10 || ' minutes')::interval AS appointment_date, -- кратно 10 минутам
    (ARRAY['completed', 'completed', 'completed', 'completed', 'scheduled', 'cancelled'])[1 + floor(random() * 6)] AS status
FROM generate_series(1, 5000);

-- Генерация медицинских записей для завершенных приемов
INSERT INTO medical_records (appointment_id, diagnosis_encrypted, diagnosis_iv, complaints, examination_results)
SELECT 
    a.id,
    mock_encrypt_diagnosis(diagnosis_text) AS diagnosis_encrypted,
    generate_mock_iv() AS diagnosis_iv,
    complaints_text AS complaints,
    'Температура ' || (36.0 + random() * 3)::numeric(3,1) || '°C, давление ' || 
    (110 + floor(random() * 40))::text || '/' || (70 + floor(random() * 20))::text || ' мм.рт.ст., ' ||
    'пульс ' || (60 + floor(random() * 40))::text || ' уд/мин' AS examination_results
FROM appointments a
CROSS JOIN (
    SELECT 
        (ARRAY['ОРВИ', 'Гипертония', 'Мигрень', 'Гастрит', 'Остеохондроз', 'Аллергия', 'Синусит', 'Артрит', 'Бронхит', 'Дерматит'])[1 + floor(random() * 10)] AS diagnosis_text,
        (ARRAY['Головная боль', 'Повышенная температура', 'Кашель', 'Боль в горле', 'Усталость', 'Головокружение', 'Боль в спине', 'Насморк'])[1 + floor(random() * 8)] || ', ' ||
        (ARRAY['слабость', 'тошнота', 'насморк', 'боль в мышцах', 'бессонница', 'потеря аппетита', 'озноб', 'повышенная потливость'])[1 + floor(random() * 8)] AS complaints_text
) AS random_data
WHERE a.status = 'completed';

-- Генерация назначений (1-3 назначения на каждую медкарту)
INSERT INTO prescriptions (medical_record_id, medication_name, dosage, frequency, duration, notes)
SELECT
    mr.id,
    (ARRAY['Парацетамол', 'Ибупрофен', 'Амоксициллин', 'Цитрамон', 'АЦЦ', 'Супрастин', 'Но-шпа', 'Анальгин', 'Аспирин', 'Лоратадин', 'Нурофен', 'Фервекс'])[1 + floor(random() * 12)] AS medication_name,
    (ARRAY['500мг', '200мг', '1000мг', '250мг', '600мг', '100мг', '50мг', '400мг', '300мг'])[1 + floor(random() * 9)] AS dosage,
    (ARRAY['1 раз в день', '2 раза в день', '3 раза в день', 'по необходимости', 'утром и вечером'])[1 + floor(random() * 5)] AS frequency,
    (ARRAY['3 дня', '5 дней', '7 дней', '10 дней', '14 дней', '30 дней', '1 месяц'])[1 + floor(random() * 7)] AS duration,
    CASE 
        WHEN random() > 0.8 THEN 'После еды'
        WHEN random() > 0.6 THEN 'До еды'
        WHEN random() > 0.4 THEN 'Запивать большим количеством воды'
        WHEN random() > 0.2 THEN 'Не разжевывать'
        ELSE NULL 
    END AS notes
FROM medical_records mr
CROSS JOIN generate_series(1, 1 + floor(random() * 3)::int) -- 1-3 назначения на запись
LIMIT 10000; -- Ограничиваем общее количество назначений

-- Удаление временных функций
DROP FUNCTION IF EXISTS random_phone();
DROP FUNCTION IF EXISTS random_email(VARCHAR, INT);
DROP FUNCTION IF EXISTS mock_encrypt_diagnosis(TEXT);
DROP FUNCTION IF EXISTS generate_mock_iv();

-- Обновление статистики таблиц для оптимизатора
ANALYZE patients, doctors, appointments, medical_records, prescriptions;

-- Проверка уникальности email
DO $$
DECLARE
    patient_email_duplicates INT;
    doctor_email_duplicates INT;
BEGIN
    -- Проверяем дублирование email у пациентов
    SELECT COUNT(*) - COUNT(DISTINCT email) INTO patient_email_duplicates
    FROM patients WHERE email IS NOT NULL;
    
    -- Проверяем дублирование email у врачей
    SELECT COUNT(*) - COUNT(DISTINCT email) INTO doctor_email_duplicates
    FROM doctors WHERE email IS NOT NULL;
    
    IF patient_email_duplicates > 0 THEN
        RAISE WARNING 'Найдено % дублирующихся email у пациентов', patient_email_duplicates;
    END IF;
    
    IF doctor_email_duplicates > 0 THEN
        RAISE WARNING 'Найдено % дублирующихся email у врачей', doctor_email_duplicates;
    END IF;
    
    IF patient_email_duplicates = 0 AND doctor_email_duplicates = 0 THEN
        RAISE NOTICE 'Все email уникальны!';
    END IF;
END $$;

-- Статистика генерации
DO $$
DECLARE
    stats RECORD;
BEGIN
    SELECT 
        (SELECT COUNT(*) FROM patients) as patients,
        (SELECT COUNT(*) FROM doctors) as doctors,
        (SELECT COUNT(*) FROM appointments) as appointments,
        (SELECT COUNT(*) FROM medical_records) as records,
        (SELECT COUNT(*) FROM prescriptions) as prescriptions,
        (SELECT COUNT(*) FROM appointments WHERE status = 'completed') as completed_appointments,
        (SELECT COUNT(*) FROM appointments WHERE status = 'scheduled') as scheduled_appointments,
        (SELECT COUNT(*) FROM appointments WHERE status = 'cancelled') as cancelled_appointments
    INTO stats;
    
    RAISE NOTICE E'\n===== СТАТИСТИКА ГЕНЕРАЦИИ =====';
    RAISE NOTICE 'Пациентов: %', stats.patients;
    RAISE NOTICE 'Врачей: %', stats.doctors;
    RAISE NOTICE 'Приемов всего: %', stats.appointments;
    RAISE NOTICE '  - завершенных: %', stats.completed_appointments;
    RAISE NOTICE '  - запланированных: %', stats.scheduled_appointments;
    RAISE NOTICE '  - отмененных: %', stats.cancelled_appointments;
    RAISE NOTICE 'Медкарт: %', stats.records;
    RAISE NOTICE 'Назначений: %', stats.prescriptions;
    RAISE NOTICE E'================================\n';
END $$;