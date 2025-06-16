-- Добавляем несколько пациентов
INSERT INTO patients (first_name, last_name, middle_name, birth_date, gender, phone, email, address)
VALUES 
    ('Иван', 'Иванов', 'Иванович', '1990-05-15', 'M', '+79991234567', 'ivanov@mail.ru', 'г. Москва, ул. Ленина, д. 1'),
    ('Мария', 'Петрова', 'Сергеевна', '1985-03-20', 'F', '+79991234568', 'petrova@mail.ru', 'г. Москва, ул. Пушкина, д. 2'),
    ('Петр', 'Сидоров', 'Петрович', '1975-11-10', 'M', '+79991234569', 'sidorov@mail.ru', 'г. Москва, ул. Гагарина, д. 3');

-- Добавляем врачей
INSERT INTO doctors (first_name, last_name, middle_name, specialization, license_number, phone, email)
VALUES 
    ('Александр', 'Смирнов', 'Александрович', 'Терапевт', 'LIC-2024-001', '+79997654321', 'smirnov@clinic.ru'),
    ('Елена', 'Козлова', 'Владимировна', 'Кардиолог', 'LIC-2024-002', '+79997654322', 'kozlova@clinic.ru');

-- Проверяем, что данные добавились
SELECT * FROM patients;
SELECT * FROM doctors;