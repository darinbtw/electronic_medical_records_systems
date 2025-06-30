-- Включаем репликацию
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET max_replication_slots = 10;
ALTER SYSTEM SET wal_keep_size = '1GB';

-- Права для репликации
ALTER USER postgres REPLICATION;

-- Создаем слоты репликации
SELECT * FROM pg_create_physical_replication_slot('slave1_slot');
SELECT * FROM pg_create_physical_replication_slot('slave2_slot');
