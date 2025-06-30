#!/bin/bash
set -e

# ��������� ���� ��� ����������
echo "host replication all 0.0.0.0/0 trust" >> "$PGDATA/pg_hba.conf"

# ������� ������������ ��� ����������
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER replicator WITH REPLICATION LOGIN PASSWORD 'replicator';
    SELECT pg_reload_conf();
EOSQL
