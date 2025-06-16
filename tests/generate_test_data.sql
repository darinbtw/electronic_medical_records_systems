-- Генерируем больше данных для тестирования
INSERT INTO patients (first_name, last_name, middle_name, birth_date, gender, phone, email)
SELECT 
    'Имя' || i,
    'Фамилия' || i,
    'Отчество' || i,
    DATE '1950-01-01' + (random() * 365 * 70)::int,
    CASE WHEN random() > 0.5 THEN 'M' ELSE 'F' END,
    '+7999' || (1000000 + i),
    'user' || i || '@example.com'
FROM generate_series(4, 10000) AS i;

-- Добавим еще 990,000 записей
INSERT INTO patients (first_name, last_name, birth_date, gender, email)
SELECT 
    'Имя' || i,
    'Фамилия' || i,
    DATE '1950-01-01' + (random() * 365 * 70)::int,
    CASE WHEN random() > 0.5 THEN 'M' ELSE 'F' END,
    'user' || i || '@test.com'
FROM generate_series(10001, 1000000) i;

DROP INDEX idx_patients_name;
DROP INDEX idx_patients_birth_date;

-- Теперь повторим тесты - разница будет огромной.

-- Без индекса на birth_date
EXPLAIN ANALYZE
SELECT * FROM patients 
WHERE birth_date BETWEEN '1990-01-01' AND '1990-12-31';

-- Запоминаем время выполнения

-- Если созданы индексы, то:
-- DROP INDEX idx_patients_name;
-- DROP INDEX idx_patients_birth_date;

-- Создаем индексы
CREATE INDEX idx_patients_name ON patients(last_name, first_name);
CREATE INDEX idx_patients_birth_date ON patients(birth_date);

-- Без индекса на birth_date
EXPLAIN ANALYZE
SELECT * FROM patients 
WHERE birth_date BETWEEN '1990-01-01' AND '1990-12-31';