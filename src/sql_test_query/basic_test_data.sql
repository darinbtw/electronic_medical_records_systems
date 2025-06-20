-- Базовые тестовые данные

-- Вставка тестовых пациентов
INSERT INTO patients (first_name, last_name, middle_name, birth_date, gender, phone, email, address) VALUES
('Иван', 'Иванов', 'Иванович', '1985-03-15', 'M', '+79001234567', 'ivanov@mail.ru', 'г. Москва, ул. Ленина, д. 1'),
('Петр', 'Петров', 'Петрович', '1990-07-22', 'M', '+79001234568', 'petrov@mail.ru', 'г. Москва, ул. Пушкина, д. 2'),
('Мария', 'Сидорова', 'Ивановна', '1992-11-03', 'F', '+79001234569', 'sidorova@mail.ru', 'г. Москва, ул. Гагарина, д. 3'),
('Елена', 'Козлова', 'Сергеевна', '1988-05-17', 'F', '+79001234570', 'kozlova@mail.ru', 'г. Санкт-Петербург, пр. Невский, д. 10'),
('Алексей', 'Смирнов', 'Александрович', '1975-12-01', 'M', '+79001234571', 'smirnov@mail.ru', 'г. Москва, ул. Тверская, д. 5');

-- Вставка тестовых врачей
INSERT INTO doctors (first_name, last_name, middle_name, specialization, license_number, phone, email) VALUES
('Александр', 'Докторов', 'Сергеевич', 'Терапевт', 'ЛИЦ-2024-0001', '+79101234567', 'doktorov@clinic.ru'),
('Ольга', 'Медицина', 'Владимировна', 'Кардиолог', 'ЛИЦ-2024-0002', '+79101234568', 'medicina@clinic.ru'),
('Сергей', 'Хирургов', 'Петрович', 'Хирург', 'ЛИЦ-2024-0003', '+79101234569', 'hirurgov@clinic.ru'),
('Наталья', 'Неврологова', 'Андреевна', 'Невролог', 'ЛИЦ-2024-0004', '+79101234570', 'nevrologova@clinic.ru');

-- Вставка тестовых приемов
INSERT INTO appointments (patient_id, doctor_id, appointment_date, status) VALUES
(1, 1, '2024-01-15 10:00:00', 'completed'),
(1, 2, '2024-02-20 14:30:00', 'completed'),
(2, 1, '2024-01-16 11:00:00', 'completed'),
(3, 3, '2024-01-17 09:00:00', 'completed'),
(4, 4, '2024-01-18 15:00:00', 'completed'),
(5, 1, CURRENT_TIMESTAMP + INTERVAL '1 day', 'scheduled'),
(1, 3, CURRENT_TIMESTAMP + INTERVAL '3 days', 'scheduled');

-- Вставка тестовых медицинских записей (без шифрования для простоты тестирования)
INSERT INTO medical_records (appointment_id, complaints, examination_results) VALUES
(1, 'Головная боль, слабость', 'Температура 37.2, давление 130/80'),
(2, 'Боли в области сердца', 'ЭКГ в норме, рекомендована консультация'),
(3, 'Кашель, насморк', 'Признаки ОРВИ'),
(4, 'Острая боль в животе', 'Подозрение на аппендицит'),
(5, 'Головокружение, тошнота', 'Неврологические симптомы');

-- Вставка тестовых назначений
INSERT INTO prescriptions (medical_record_id, medication_name, dosage, frequency, duration, notes) VALUES
(1, 'Парацетамол', '500мг', '2 раза в день', '5 дней', 'После еды'),
(1, 'Витамин С', '1000мг', '1 раз в день', '10 дней', NULL),
(2, 'Конкор', '5мг', '1 раз в день', '30 дней', 'Утром'),
(3, 'АЦЦ', '600мг', '1 раз в день', '7 дней', 'Растворить в воде'),
(3, 'Називин', '2 капли', '3 раза в день', '5 дней', 'В каждую ноздрю');

-- Проверка вставленных данных
DO $$
DECLARE
    patient_count INTEGER;
    doctor_count INTEGER;
    appointment_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO patient_count FROM patients;
    SELECT COUNT(*) INTO doctor_count FROM doctors;
    SELECT COUNT(*) INTO appointment_count FROM appointments;
    
    RAISE NOTICE 'Вставлено: % пациентов, % врачей, % приемов', 
                 patient_count, doctor_count, appointment_count;
END $$;