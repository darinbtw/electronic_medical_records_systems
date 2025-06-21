-- Поиск по email
SELECT p.id, p.first_name, p.last_name, p.email, p.phone FROM patients p
WHERE p.email ILIKE '%gmail.com%';