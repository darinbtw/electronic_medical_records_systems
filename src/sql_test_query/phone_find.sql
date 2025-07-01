-- Поиск по номеру телефона
SELECT p.id, p.first_name, p.last_name, p.phone, p.email
FROM patients p
WHERE p.phone LIKE '%909%';
