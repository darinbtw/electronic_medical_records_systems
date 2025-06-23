# Скрипт восстановления базы данных из резервной копии

# Проверка аргументов
if [ $# -eq 0 ]; then
    echo "Использование: $0 <путь_к_файлу_резервной_копии>"
    echo "Пример: $0 /backup/postgres/medical_records_20240115_120000.sql.gz"
    exit 1
fi

BACKUP_FILE=$1
DB_NAME="medical_records"
DB_USER="postgres"

# Проверка существования файла
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Файл не найден: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  ВНИМАНИЕ: Все текущие данные в БД $DB_NAME будут удалены!"
read -p "Продолжить? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Отменено."
    exit 1
fi

# Распаковка если файл сжат
if [[ $BACKUP_FILE == *.gz ]]; then
    echo "📦 Распаковка архива..."
    gunzip -c $BACKUP_FILE > /tmp/restore_temp.sql
    RESTORE_FILE="/tmp/restore_temp.sql"
else
    RESTORE_FILE=$BACKUP_FILE
fi

# Пересоздание базы данных
echo "🔄 Пересоздание базы данных..."
psql -U $DB_USER -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"

# Восстановление
echo "📥 Восстановление данных..."
psql -U $DB_USER -d $DB_NAME < $RESTORE_FILE

if [ $? -eq 0 ]; then
    echo "✅ База данных успешно восстановлена!"
else
    echo "❌ Ошибка при восстановлении!"
    exit 1
fi

# Очистка временных файлов
rm -f /tmp/restore_temp.sql