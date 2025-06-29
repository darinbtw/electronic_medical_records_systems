"""
Backup скрипт для системы медкарт
"""
import os
import subprocess
import datetime
import gzip
import shutil

def create_backup():
    db_name = "medical_records"
    db_user = "postgres"
    backup_dir = "backups"
    
    # Создаем директорию
    os.makedirs(backup_dir, exist_ok=True)
    
    # Генерируем имя файла
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/backup_{timestamp}.sql"
    
    print("Создание backup...")
    
    try:
        # Выполняем pg_dump
        cmd = ["pg_dump", "-U", db_user, "-d", db_name]
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"Backup создан: {backup_file}")
            
            # Сжимаем файл
            with open(backup_file, 'rb') as f_in:
                with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            os.remove(backup_file)  # Удаляем несжатый файл
            print(f"Backup сжат: {backup_file}.gz")
            
        else:
            print(f"Ошибка создания backup: {result.stderr}")
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    create_backup()
    input("Нажмите Enter для выхода...")