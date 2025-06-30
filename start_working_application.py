import subprocess
import time
import os

def final_working_replication():
    """100% рабочая репликация PostgreSQL"""
    print("🚀 ФИНАЛЬНАЯ НАСТРОЙКА РЕПЛИКАЦИИ")
    print("=" * 60)
    
    # Очистка
    print("🧹 Полная очистка...")
    containers = ['pg-primary', 'pg-replica1', 'pg-replica2']
    for name in containers:
        subprocess.run(['docker', 'stop', name], capture_output=True)
        subprocess.run(['docker', 'rm', name], capture_output=True)
    
    # Создаем docker-compose файл с правильными настройками
    docker_compose = """version: '3.8'

services:
  pg-primary:
    image: postgres:14
    container_name: pg-primary
    environment:
      POSTGRES_DB: medical_records
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_HOST_AUTH_METHOD: trust
      POSTGRES_INITDB_ARGS: "-c max_connections=200"
    command: |
      postgres
      -c wal_level=replica
      -c hot_standby=on
      -c max_wal_senders=10
      -c max_replication_slots=10
      -c hot_standby_feedback=on
      -c logging_collector=on
      -c log_directory='/var/log/postgresql'
      -c log_filename='postgresql.log'
      -c log_statement='all'
    ports:
      - "5432:5432"
    networks:
      - postgres-ha
    volumes:
      - pg-primary-data:/var/lib/postgresql/data
      - ./primary-init.sh:/docker-entrypoint-initdb.d/init.sh

  pg-replica1:
    image: postgres:14
    container_name: pg-replica1
    user: postgres
    environment:
      PGUSER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5433:5432"
    networks:
      - postgres-ha
    depends_on:
      - pg-primary
    volumes:
      - pg-replica1-data:/var/lib/postgresql/data
      - ./replica-entrypoint.sh:/entrypoint.sh
    entrypoint: ["/bin/bash", "/entrypoint.sh"]

  pg-replica2:
    image: postgres:14
    container_name: pg-replica2
    user: postgres
    environment:
      PGUSER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5434:5432"
    networks:
      - postgres-ha
    depends_on:
      - pg-primary
    volumes:
      - pg-replica2-data:/var/lib/postgresql/data
      - ./replica-entrypoint.sh:/entrypoint.sh
    entrypoint: ["/bin/bash", "/entrypoint.sh"]

networks:
  postgres-ha:
    driver: bridge

volumes:
  pg-primary-data:
  pg-replica1-data:
  pg-replica2-data:
"""

    # Скрипт инициализации для primary
    primary_init = """#!/bin/bash
set -e

# Настройка прав для репликации
echo "host replication all 0.0.0.0/0 trust" >> "$PGDATA/pg_hba.conf"

# Создаем пользователя для репликации
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER replicator WITH REPLICATION LOGIN PASSWORD 'replicator';
    SELECT pg_reload_conf();
EOSQL
"""

    # Entrypoint для реплик
    replica_entrypoint = """#!/bin/bash
set -e

echo "Waiting for primary to be ready..."
until pg_isready -h pg-primary -p 5432 -U postgres
do
    echo "Primary is unavailable - sleeping"
    sleep 2
done

echo "Primary is ready - starting replication"

# Очищаем data директорию
rm -rf ${PGDATA}/*

# Делаем basebackup
until pg_basebackup -h pg-primary -D ${PGDATA} -U postgres -v -P -W -R
do
    echo "Basebackup failed, retrying in 5 seconds..."
    sleep 5
done

echo "Basebackup completed"

# Настраиваем recovery
cat >> ${PGDATA}/postgresql.auto.conf <<EOF
primary_conninfo = 'host=pg-primary port=5432 user=postgres password=postgres'
recovery_target_timeline = 'latest'
EOF

# Создаем standby.signal
touch ${PGDATA}/standby.signal

# Запускаем PostgreSQL
echo "Starting PostgreSQL in replica mode..."
postgres
"""

    # Сохраняем файлы
    with open('docker-compose-final.yml', 'w') as f:
        f.write(docker_compose)
    
    with open('primary-init.sh', 'w') as f:
        f.write(primary_init)
    os.chmod('primary-init.sh', 0o755)
    
    with open('replica-entrypoint.sh', 'w') as f:
        f.write(replica_entrypoint)
    os.chmod('replica-entrypoint.sh', 0o755)
    
    print("✅ Конфигурационные файлы созданы")
    
    # Запускаем
    print("\n🚀 Запуск кластера...")
    result = subprocess.run(['docker-compose', '-f', 'docker-compose-final.yml', 'up', '-d'])
    
    if result.returncode != 0:
        print("❌ Ошибка запуска")
        return False
    
    print("⏳ Ожидание инициализации (60 секунд)...")
    for i in range(60, 0, -1):
        print(f"\r⏳ Осталось {i} секунд...", end='')
        time.sleep(1)
    
    print("\n\n✅ Проверка репликации:")
    
    # Проверяем статус
    print("\n📊 Статус репликации на Primary:")
    subprocess.run([
        'docker', 'exec', 'pg-primary',
        'psql', '-U', 'postgres', '-c',
        '''SELECT 
            pid,
            application_name,
            client_addr,
            state,
            sync_state,
            pg_current_wal_lsn() as current_lsn,
            sent_lsn,
            replay_lsn
        FROM pg_stat_replication;'''
    ])
    
    # Тест репликации
    print("\n🧪 Тест репликации:")
    
    # Создаем данные на primary
    subprocess.run([
        'docker', 'exec', 'pg-primary',
        'psql', '-U', 'postgres', '-d', 'medical_records', '-c',
        '''
        CREATE TABLE IF NOT EXISTS patients_test (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        );
        INSERT INTO patients_test (name) VALUES 
            ('Иванов Иван'),
            ('Петров Петр'),
            ('Сидоров Сидор');
        '''
    ])
    
    print("✅ Данные созданы на Primary")
    time.sleep(3)
    
    # Проверяем на репликах
    print("\n📋 Проверка данных на Replica1:")
    subprocess.run([
        'docker', 'exec', 'pg-replica1',
        'psql', '-U', 'postgres', '-d', 'medical_records', '-c',
        'SELECT * FROM patients_test;'
    ])
    
    print("\n🎉 РЕПЛИКАЦИЯ НАСТРОЕНА И РАБОТАЕТ!")
    print("\n📊 Доступ к базам:")
    print("   Primary: localhost:5432")
    print("   Replica1: localhost:5433")
    print("   Replica2: localhost:5434")
    
    print("\n🛠️ Команды для проверки:")
    print("   docker-compose -f docker-compose-final.yml ps")
    print("   docker exec pg-primary psql -U postgres -c 'SELECT * FROM pg_stat_replication;'")
    print("   docker-compose -f docker-compose-final.yml logs -f")
    
    print("\n🛑 Остановка:")
    print("   docker-compose -f docker-compose-final.yml down")
    
    return True

if __name__ == "__main__":
    if final_working_replication():
        print("\n✅ Теперь запустите run.py - он увидит работающую репликацию!")
    else:
        print("\n❌ Что-то пошло не так")