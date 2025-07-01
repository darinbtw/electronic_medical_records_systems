# Руководство администратора системы медицинских карт

## 1. Обзор системы

Система электронных медицинских карт предназначена для:
- Хранения данных о пациентах и врачах
- Ведения истории приёмов
- Безопасного хранения диагнозов (с шифрованием)
- Управления назначениями лекарств

### Архитектура
- БД: PostgreSQL 16
- Язык: Python 3.11
- Шифрование: AES-256-CBC
- API: Flask

## 2. Установка и настройка

### 2.1. Требования
- PostgreSQL 16
- Python 3.11
- Минимум 4 ГБ RAM
- 20 ГБ свободного места на диске

### 2.2. Установка
```bash
# Клонирование репозитория
git clone <repository_url>
cd medical_records_system

# Установка зависимостей
pip install -r requirements.txt

# Копирование примера конфигурации
cp .env.example .env

# Редактирование настроек
nano .env
```

### 2.3. Настройка базы данных
```bash
# Создание базы данных
createdb -U postgres medical_records

# Применение миграций
python src/database/create_table.py

# Загрузка тестовых данных (опционально)
python src/database/load_test_data.py
```

### 2.4. Настройка TDE (шифрование)
```bash
# Включение TDE в .env
TDE_ENABLED=True

# Генерация ключа шифрования (автоматически при первом запуске)
python -c "from src.security.tde import main_tde_setup; main_tde_setup()"
```

## 3. Запуск системы

### 3.1. Обычный запуск
```bash
# Запуск с автоматическим backup
python run.py
```

### 3.2. Проверка статуса
```bash
# Проверка здоровья системы
curl http://localhost:8000/health

# Просмотр API документации
curl http://localhost:8000/api
```

## 4. Управление пользователями

### 4.1. Роли в системе
1. **Администратор** - полный доступ
2. **Главврач** - доступ ко всем медданным
3. **Врач** - доступ к своим пациентам
4. **Медсестра** - ограниченный доступ
5. **Регистратор** - только запись на приём
6. **Пациент** - свои данные
7. **Аудитор** - только чтение

### 4.2. Создание пользователей
```sql
-- Подключение к БД
psql -U postgres -d medical_records

-- Создание врача
INSERT INTO doctors (first_name, last_name, specialization, license_number, phone, email)
VALUES ('Иван', 'Иванов', 'Терапевт', 'ЛИЦ-2024-0001', '+79001234567', 'ivanov@clinic.ru');
```

## 5. Резервное копирование

### 5.1. Автоматическое резервное копирование
Система автоматически создаёт backup:
- **Полный backup**: 02:00 и 14:00 ежедневно
- **Очистка старых backup**: 03:00 (старше 7 дней)

### 5.2. Ручное создание backup
```bash
# Python backup (рекомендуется)
python scripts/python_backup.py

# Альтернативный метод
python scripts/backup.py
```

### 5.3. Восстановление из backup
```bash
# Запуск скрипта восстановления
python scripts/restore.py

# Выбор файла backup из списка
# Подтверждение восстановления
```

## 6. Репликация

### 6.1. Настройка Master
```bash
# Запуск скрипта настройки репликации
bash scripts/setup_replication.sh

# Проверка статуса
psql -U postgres -c "SELECT * FROM pg_stat_replication;"
```

### 6.2. Настройка Slave
```bash
# На slave сервере
pg_basebackup -h <master_ip> -D /var/lib/postgresql/16/main -U replicator -W

# Создание standby.signal
touch /var/lib/postgresql/16/main/standby.signal

# Запуск PostgreSQL
systemctl start postgresql
```

### 6.3. Мониторинг репликации
```sql
-- На Master
SELECT client_addr, state, sync_state, replay_lag 
FROM pg_stat_replication;

-- На Slave
SELECT pg_is_in_recovery();
```

## 7. Мониторинг

### 7.1. Логи системы
```bash
# Логи приложения
tail -f logs/medical_system.log

# Логи аудита
tail -f logs/audit.log

# Логи PostgreSQL
tail -f /var/log/postgresql/postgresql-16-main.log
```

### 7.2. Проверка производительности
```sql
-- Топ медленных запросов
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Размер таблиц
SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::regclass)) 
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
```

### 7.3. Мониторинг TDE
```bash
# Проверка статуса шифрования
curl http://localhost:8000/api/debug/tde-status

# Проверка покрытия шифрованием
python -c "from src.security.tde import TDEAdmin; TDEAdmin().verify_encryption()"
```

## 8. Безопасность

### 8.1. Управление ключами
```bash
# Ротация ключа шифрования (каждые 90 дней)
python -c "from src.database.connection import db; db.rotate_tde_keys()"

# Backup ключей
cp .tde_master_key .tde_master_key.backup.$(date +%Y%m%d)
chmod 600 .tde_master_key.backup.*
```

### 8.2. Аудит
```sql
-- Просмотр последних изменений пациентов
SELECT * FROM patients_audit 
ORDER BY changed_at DESC 
LIMIT 20;

-- Поиск подозрительной активности
SELECT changed_by, COUNT(*) as changes 
FROM patients_audit 
WHERE changed_at > NOW() - INTERVAL '1 hour' 
GROUP BY changed_by 
HAVING COUNT(*) > 100;
```

### 8.3. Защита от атак
```bash
# Проверка на SQL-инъекции
python src/security/sql_injection_test.py

# Анализ логов на попытки взлома
grep -i "error\|failed\|denied" logs/medical_system.log | tail -50
```

## 9. Обслуживание

### 9.1. Очистка и оптимизация
```sql
-- Анализ таблиц
ANALYZE patients, doctors, appointments, medical_records;

-- Очистка старых логов аудита (старше года)
DELETE FROM patients_audit 
WHERE changed_at < NOW() - INTERVAL '1 year';

-- Перестроение индексов
REINDEX TABLE patients;
REINDEX TABLE appointments;
```

### 9.2. Обновление системы
```bash
# Backup перед обновлением
python scripts/python_backup.py

# Обновление зависимостей
pip install -r requirements.txt --upgrade

# Применение новых миграций
python src/database/migrations/apply_updates.py

# Перезапуск системы
systemctl restart medical_records
```

## 10. Устранение неполадок

### 10.1. Система не запускается
```bash
# Проверка подключения к БД
psql -U postgres -d medical_records -c "SELECT 1;"

# Проверка прав на файлы
ls -la .encryption_key .tde_master_key

# Проверка портов
netstat -an | grep 8000
```

### 10.2. Проблемы с шифрованием
```bash
# Сброс TDE (ВНИМАНИЕ: потеря зашифрованных данных!)
rm .tde_master_key
TDE_ENABLED=False python run.py

# Миграция существующих данных под TDE
python -c "from src.security.tde import TDEAdmin; TDEAdmin().migrate_existing_data()"
```

### 10.3. Проблемы с производительностью
```sql
-- Проверка блокировок
SELECT pid, usename, query_start, state, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY query_start;

-- Завершение зависшего запроса
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE pid = <problem_pid>;
```

## 11. Контакты поддержки

При возникновении критических проблем:
1. Проверьте логи системы
2. Создайте backup данных
3. Обратитесь к старшему администратору
4. Документируйте все действия

## 12. Чек-лист ежедневных задач

- [ ] Проверить статус системы через /health
- [ ] Проверить наличие свежих backup
- [ ] Просмотреть логи на ошибки
- [ ] Проверить свободное место на диске
- [ ] Проверить статус репликации
- [ ] Просмотреть аудит необычной активности

## 13. Аварийное восстановление

### 13.1. Полный отказ Master БД
```bash
# На Slave1
# Промоут в Master
sudo -u postgres pg_ctl promote

# Перенаправление трафика на новый Master
# Обновить connection string в .env
```

### 13.2. Потеря данных
```bash
# Найти последний backup
ls -la backups/

# Восстановить
python scripts/restore.py backups/python_backup_20240115_140000.sql.gz
```

### 13.3. Взлом системы
1. Немедленно отключить внешний доступ
2. Сохранить логи для анализа
3. Проверить целостность данных
4. Сменить все пароли и ключи
5. Восстановить из проверенного backup

---

**Версия документа**: 1.0  
**Последнее обновление**: Январь 2024  
**Автор**: Администратор системы