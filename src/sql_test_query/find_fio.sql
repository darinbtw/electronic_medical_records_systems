-- Поиск по части ФИО (полнотекстовый поиск)
SELECT p.id, p.first_name, p.last_name, p.middle_name, p.phone
FROM patients p
WHERE CONCAT(p.last_name, ' ', p.first_name, ' ', p.middle_name) ILIKE '%Петр%';
