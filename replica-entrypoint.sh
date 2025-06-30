#!/bin/bash
set -e

echo "Waiting for primary to be ready..."
until pg_isready -h pg-primary -p 5432 -U postgres
do
    echo "Primary is unavailable - sleeping"
    sleep 2
done

echo "Primary is ready - starting replication"

# ������� data ����������
rm -rf ${PGDATA}/*

# ������ basebackup
until pg_basebackup -h pg-primary -D ${PGDATA} -U postgres -v -P -W -R
do
    echo "Basebackup failed, retrying in 5 seconds..."
    sleep 5
done

echo "Basebackup completed"

# ����������� recovery
cat >> ${PGDATA}/postgresql.auto.conf <<EOF
primary_conninfo = 'host=pg-primary port=5432 user=postgres password=postgres'
recovery_target_timeline = 'latest'
EOF

# ������� standby.signal
touch ${PGDATA}/standby.signal

# ��������� PostgreSQL
echo "Starting PostgreSQL in replica mode..."
postgres
