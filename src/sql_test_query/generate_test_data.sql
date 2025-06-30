-- 1. УДАЛЯЕМ ВСЕ ОГРАНИЧЕНИЯ И ТРИГГЕРЫ
ALTER TABLE appointments DROP CONSTRAINT IF EXISTS chk_appointments_different_ids;
ALTER TABLE appointments DROP CONSTRAINT IF EXISTS unique_appointment;
DROP TRIGGER IF EXISTS trg_validate_appointment_date ON appointments;

ALTER TABLE prescriptions DROP CONSTRAINT IF EXISTS chk_prescriptions_duration_format;
ALTER TABLE prescriptions DROP CONSTRAINT IF EXISTS chk_prescriptions_frequency_format;
ALTER TABLE prescriptions DROP CONSTRAINT IF EXISTS chk_prescriptions_dosage_format;

-- 2. ОЧИЩАЕМ ТАБЛИЦЫ
TRUNCATE TABLE prescriptions, medical_records, appointments, doctors, patients
    RESTART IDENTITY CASCADE;

-- 3. ГЕНЕРИРУЕМ ДАННЫЕ

-- Пациенты (1000 штук)
INSERT INTO patients (first_name, last_name, middle_name, birth_date, gender, phone, email, address)
SELECT 
    (ARRAY['Иван','Пётр','Сергей','Александр','Андрей','Дмитрий','Максим','Алексей','Николай','Владимир',
           'Анна','Мария','Елена','Наталья','Ольга','Татьяна','Ирина','Светлана','Екатерина','Людмила'])
      [1 + floor(random() * 20)],
    (ARRAY['Иванов','Петров','Сидоров','Смирнов','Кузнецов','Попов','Васильев','Соколов','Лебедев','Козлов'])
      [1 + floor(random() * 10)],
    (ARRAY['Иванович','Петрович','Сергеевич','Александрович','Андреевич','Ивановна','Петровна','Сергеевна'])
      [1 + floor(random() * 8)],
    DATE '1950-01-01' + (random() * 20000)::int,
    (ARRAY['M','F'])[1 + floor(random() * 2)],
    '+7' || floor(9000000000 + random() * 999999999)::text,
    'patient' || generate_series || '@mail.ru',
    'г. Москва, ул. Ленина, д. ' || floor(random() * 100 + 1)::text
FROM generate_series(1, 1000);

-- Врачи (50 штук)
INSERT INTO doctors (first_name, last_name, middle_name, specialization, license_number, phone, email)
SELECT
    (ARRAY['Александр','Сергей','Виктор','Михаил','Андрей','Ольга','Наталья','Елена','Татьяна','Марина'])
      [1 + floor(random() * 10)],
    (ARRAY['Докторов','Медведев','Хирургов','Терапевтов','Кардиологов','Неврологов','Педиатров'])
      [1 + floor(random() * 7)],
    (ARRAY['Сергеевич','Петрович','Андреевич','Сергеевна','Владимировна','Петровна'])
      [1 + floor(random() * 6)],
    (ARRAY['Терапевт','Кардиолог','Хирург','Невролог','Педиатр','ЛОР','Дерматолог'])
      [1 + floor(random() * 7)],
    'ЛИЦ-2025-' || lpad(generate_series::text, 4, '0'),
    '+7' || floor(9000000000 + random() * 999999999)::text,
    'doctor' || generate_series || '@clinic.ru'
FROM generate_series(1, 50);

-- Приёмы (5000 штук)
INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
SELECT
    1 + floor(random() * 1000)::int,
    1 + floor(random() * 50)::int,
    CURRENT_DATE - (random() * 365)::int + (random() * 8 + 9 || ' hours')::interval,
    (ARRAY['completed','completed','completed','scheduled','cancelled'])
      [1 + floor(random() * 5)]
FROM generate_series(1, 5000)
ON CONFLICT DO NOTHING;

-- Медкарты для завершённых приёмов
INSERT INTO medical_records (appointment_id, diagnosis_encrypted, diagnosis_iv, complaints, examination_results)
SELECT 
    a.id,
    '\x4f5256494b'::bytea,
    '\x0123456789abcdef'::bytea,
    (ARRAY['Головная боль','Температура','Кашель','Усталость','Боль в горле'])
      [1 + floor(random() * 5)],
    'Температура ' || (36.0 + random() * 3)::numeric(3,1)
      || ', давление ' || (110 + floor(random() * 40))::text 
      || '/' || (70 + floor(random() * 20))::text
FROM appointments a
WHERE a.status = 'completed';

-- Назначения
INSERT INTO prescriptions (medical_record_id, medication_name, dosage, frequency, duration, notes)
SELECT
    mr.id,
    (ARRAY['Парацетамол','Ибупрофен','Амоксициллин','Цитрамон','АЦЦ'])
      [1 + floor(random() * 5)],
    (ARRAY['500мг','200мг','1000мг','250мг','600мг'])
      [1 + floor(random() * 5)],
    (ARRAY['1 раз в день','2 раза в день','3 раза в день'])
      [1 + floor(random() * 3)],
    (ARRAY['3 дня','5 дней','1 неделя','10 дней'])
      [1 + floor(random() * 4)],
    (ARRAY['После еды','До еды','Запивать водой',NULL])
      [1 + floor(random() * 4)]
FROM medical_records mr;

-- 4. СТАТИСТИКА
SELECT 'Пациентов'      AS entity, COUNT(*) FROM patients
UNION ALL
SELECT 'Врачей',          COUNT(*) FROM doctors
UNION ALL  
SELECT 'Приёмов',         COUNT(*) FROM appointments
UNION ALL
SELECT 'Медкарт',         COUNT(*) FROM medical_records
UNION ALL
SELECT 'Назначений',      COUNT(*) FROM prescriptions;
