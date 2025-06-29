@echo off
REM Backup скрипт для системы медкарт (Windows)

set DB_NAME=medical_records
set DB_USER=postgres
set BACKUP_DIR=backups
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%

if not exist %BACKUP_DIR% mkdir %BACKUP_DIR%

echo Создание backup...
pg_dump -U %DB_USER% -d %DB_NAME% > "%BACKUP_DIR%/backup_%TIMESTAMP%.sql"

if %errorlevel% equ 0 (
    echo Backup создан: backup_%TIMESTAMP%.sql
) else (
    echo Ошибка создания backup
)

pause