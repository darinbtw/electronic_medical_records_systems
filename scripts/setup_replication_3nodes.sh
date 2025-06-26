#!/bin/bash
# Полная настройка репликации PostgreSQL для 3 нод

# Конфигурация
MASTER_IP="192.168.1.10"
SLAVE1_IP="192.168.1.11"
SLAVE2_IP="192.168.1.12"
REPL_USER="replicator"
REPL_PASS="repl_password"

echo "🔧 Настройка репликации PostgreSQL на 3 ноды"

# === НАСТРОЙКА MASTER ===
if [[ $(hostname -I) == *"$MASTER_IP"* ]]; then
    echo "📍 Настройка MASTER узла..."
    
    # Конфигурация postgresql.conf
    cat >> /etc/postgresql/14/main/postgresql.conf << EOF

# Replication Master Settings
wal_level = replica
max_wal_senders = 5
wal_keep_segments = 64
archive_mode = on
archive_command = 'test ! -f /var/lib/postgresql/14/archive/%f && cp %p /var/lib/postgresql/14/archive/%f'
synchronous_commit = on
synchronous_standby_names = 'slave1,slave2'
EOF

    # Конфигурация pg_hba.conf
    cat >> /etc/postgresql/14/main/pg_hba.conf << EOF
# Replication connections
host    replication     $REPL_USER      $SLAVE1_IP/32          md5
host    replication     $REPL_USER      $SLAVE2_IP/32          md5
EOF

    # Создание пользователя репликации
    sudo -u postgres psql -c "CREATE USER $REPL_USER WITH REPLICATION PASSWORD '$REPL_PASS';"
    
    # Создание директории архивов
    mkdir -p /var/lib/postgresql/16/archive
    chown postgres:postgres /var/lib/postgresql/14/archive
    
    systemctl restart postgresql
    echo "✅ Master настроен!"
fi

# === НАСТРОЙКА SLAVE УЗЛОВ ===
if [[ $(hostname -I) == *"$SLAVE1_IP"* ]] || [[ $(hostname -I) == *"$SLAVE2_IP"* ]]; then
    echo "📍 Настройка SLAVE узла..."
    
    # Определяем имя узла
    if [[ $(hostname -I) == *"$SLAVE1_IP"* ]]; then
        NODE_NAME="slave1"
    else
        NODE_NAME="slave2"
    fi
    
    # Останавливаем PostgreSQL
    systemctl stop postgresql
    
    # Очищаем старые данные
    rm -rf /var/lib/postgresql/16/main/*
    
    # Делаем базовый backup с master
    PGPASSWORD=$REPL_PASS pg_basebackup \
        -h $MASTER_IP \
        -D /var/lib/postgresql/16/main \
        -U $REPL_USER \
        -v -P -W \
        -R -X stream \
        -C -S $NODE_NAME
    
    # Настройка recovery
    cat > /var/lib/postgresql/16/main/postgresql.auto.conf << EOF
primary_conninfo = 'host=$MASTER_IP port=5432 user=$REPL_USER password=$REPL_PASS application_name=$NODE_NAME'
restore_command = 'cp /var/lib/postgresql/14/archive/%f %p'
recovery_target_timeline = 'latest'
EOF

    # Создаем standby.signal
    touch /var/lib/postgresql/16/main/standby.signal
    
    # Права доступа
    chown -R postgres:postgres /var/lib/postgresql/16/main
    
    # Запускаем PostgreSQL
    systemctl start postgresql
    echo "✅ $NODE_NAME настроен!"
fi

# === ПРОВЕРКА РЕПЛИКАЦИИ ===
echo "🔍 Проверка статуса репликации..."
sleep 5

if [[ $(hostname -I) == *"$MASTER_IP"* ]]; then
    sudo -u postgres psql -c "SELECT client_addr, state, sync_state FROM pg_stat_replication;"
else
    sudo -u postgres psql -c "SELECT pg_is_in_recovery();"
fi