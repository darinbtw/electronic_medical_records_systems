# Настройки
DB_NAME="medical_records"
DB_USER="postgres"
BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql"

# Создаём директорию если её нет
mkdir -p $BACKUP_DIR

# Выполняем дамп
echo "🔄 Начинаем резервное копирование БД $DB_NAME..."
pg_dump -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# Проверяем успешность
if [ $? -eq 0 ]; then
    echo "✅ Резервная копия создана: $BACKUP_FILE"
    
    # Сжимаем файл
    gzip $BACKUP_FILE
    echo "📦 Файл сжат: ${BACKUP_FILE}.gz"
    
    # Удаляем старые бэкапы (старше 30 дней)
    find $BACKUP_DIR -name "${DB_NAME}_*.sql.gz" -mtime +30 -delete
    echo "🗑️  Старые резервные копии удалены"
else
    echo "❌ Ошибка при создании резервной копии!"
    exit 1
fi