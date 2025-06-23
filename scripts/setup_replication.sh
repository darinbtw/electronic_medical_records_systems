# Настройка репликации PostgreSQL (Master)

echo "🔧 Настройка Master-сервера для репликации"

# Путь к конфигурации PostgreSQL (может отличаться)
PG_CONFIG="/etc/postgresql/14/main/postgresql.conf"
PG_HBA="/etc/postgresql/14/main/pg_hba.conf"

# Резервные копии конфигов
cp $PG_CONFIG ${PG_CONFIG}.backup
cp $PG_HBA ${PG_HBA}.backup

# Настройка postgresql.conf
echo "📝 Настройка postgresql.conf..."
cat >> $PG_CONFIG << EOF

# Replication settings
wal_level = replica
max_wal_senders = 3
wal_keep_segments = 64
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/14/main/archive/%f'
EOF

# Настройка pg_hba.conf
echo "📝 Настройка pg_hba.conf..."
echo "host    replication     replicator      192.168.1.0/24          md5" >> $PG_HBA

# Создание пользователя для репликации
echo "👤 Создание пользователя replicator..."
sudo -u postgres psql -c "CREATE USER replicator WITH REPLICATION PASSWORD 'repl_password';"

# Создание директории для архивов
mkdir -p /var/lib/postgresql/14/main/archive
chown postgres:postgres /var/lib/postgresql/14/main/archive

# Перезапуск PostgreSQL
echo "🔄 Перезапуск PostgreSQL..."
systemctl restart postgresql

echo "✅ Master-сервер настроен!"
echo ""
echo "📋 Для настройки Slave-серверов:"
echo "1. Остановите PostgreSQL на slave"
echo "2. Выполните pg_basebackup:"
echo "   pg_basebackup -h <master_ip> -D /var/lib/postgresql/14/main -U replicator -W"
echo "3. Создайте recovery.conf"
echo "4. Запустите PostgreSQL на slave"