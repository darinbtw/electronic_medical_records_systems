-- =====================================================
-- Очистка базы данных перед новыми тестами
-- ВНИМАНИЕ: Удаляет все данные!
-- =====================================================

-- Удаляем таблицы в правильном порядке (из-за foreign keys)
DROP TABLE IF EXISTS prescriptions CASCADE;
DROP TABLE IF EXISTS medical_records CASCADE;
DROP TABLE IF EXISTS appointments CASCADE;
DROP TABLE IF EXISTS doctors CASCADE;
DROP TABLE IF EXISTS patients CASCADE;
DROP TABLE IF EXISTS patients_audit CASCADE;

-- Удаляем функции и триггеры
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Сообщение об успешной очистке
DO $$
BEGIN
    RAISE NOTICE 'База данных очищена!';
END $$;