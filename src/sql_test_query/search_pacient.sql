
-- ПОИСК ПАЦИЕНТОВ

-- Поиск по ФИО (с использованием индекса)
SELECT p.id, p.first_name, p.last_name, p.middle_name, p.birth_date, p.phone
FROM patients p
WHERE p.last_name ILIKE 'Иванов%' 
AND p.first_name ILIKE 'Иван%';

-- Поиск по части ФИО (полнотекстовый поиск)
SELECT p.id, p.first_name, p.last_name, p.middle_name, p.phone
FROM patients p
WHERE CONCAT(p.last_name, ' ', p.first_name, ' ', p.middle_name) ILIKE '%Петр%';

-- Поиск по номеру телефона
SELECT p.id, p.first_name, p.last_name, p.phone, p.email
FROM patients p
WHERE p.phone LIKE '%909%';

-- Поиск по возрасту
SELECT p.id, p.first_name, p.last_name, 
       DATE_PART('year', AGE(p.birth_date)) AS age
FROM patients p
WHERE DATE_PART('year', AGE(p.birth_date)) BETWEEN 25 AND 35
ORDER BY age;