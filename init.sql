
-- ��������� ����������
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 10;
ALTER SYSTEM SET max_replication_slots = 10;

-- ������� ����� ����������
SELECT pg_create_physical_replication_slot('slave1');
SELECT pg_create_physical_replication_slot('slave2');

-- ���� ����� �� ����������
ALTER USER postgres REPLICATION;
