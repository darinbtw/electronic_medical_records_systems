-- Возрастной анализ пациентов
SELECT 
    CASE 
        WHEN age < 18 THEN 'До 18'
        WHEN age BETWEEN 18 AND 30 THEN '18-30'
        WHEN age BETWEEN 31 AND 50 THEN '31-50'
        WHEN age BETWEEN 51 AND 65 THEN '51-65'
        ELSE 'Старше 65'
    END as age_group,
    COUNT(*) as patients_count
FROM (
    SELECT DATE_PART('year', AGE(birth_date)) as age
    FROM patients
) age_data
GROUP BY age_group
ORDER BY 
    CASE age_group
        WHEN 'До 18' THEN 1
        WHEN '18-30' THEN 2
        WHEN '31-50' THEN 3
        WHEN '51-65' THEN 4
        ELSE 5
    END;