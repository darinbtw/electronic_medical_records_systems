-- Поиск по email
SELECT d.id, d.first_name, d.last_name, d.email, d.phone FROM doctors d
WHERE d.email ILIKE '%clinic.ru%';