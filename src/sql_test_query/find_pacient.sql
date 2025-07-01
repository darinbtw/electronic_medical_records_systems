
-- ПОИСК ПАЦИЕНТОВ

-- Поиск по ФИО (с использованием индекса)
SELECT p.id, p.first_name, p.last_name, p.middle_name, p.birth_date, p.phone
FROM patients p
WHERE p.last_name ILIKE 'Иванов%' 
AND p.first_name ILIKE 'Иван%';