"""
Restore скрипт для системы медкарт
"""
import os
import subprocess
import sys
import gzip

def restore_backup(backup_file):
    if not os.path.exists(backup_file):
        print(f"Файл не найден: {backup_file}")
        return False
    
    db_name = "medical_records"
    db_user = "postgres"
    
    print(f"Восстановление из: {backup_file}")
    
    # Подтверждение
    confirm = input("Все данные в БД будут заменены! Продолжить? (y/n): ")
    if confirm.lower() != 'y':
        print("Отменено")
        return False
    
    try:
        # Если файл сжат, распаковываем
        if backup_file.endswith('.gz'):
            temp_file = backup_file[:-3]  # убираем .gz
            print("Распаковка архива...")
            with gzip.open(backup_file, 'rb') as f_in:
                with open(temp_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            backup_file = temp_file
        
        # Восстанавливаем
        print("Восстановление данных...")
        cmd = ["psql", "-U", db_user, "-d", db_name, "-f", backup_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Восстановление завершено успешно!")
            return True
        else:
            print(f"Ошибка восстановления: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    finally:
        # Удаляем временный файл
        if backup_file.endswith('.sql') and os.path.exists(backup_file):
            try:
                os.remove(backup_file)
            except:
                pass

def main():
    print("ВОССТАНОВЛЕНИЕ БАЗЫ ДАННЫХ")
    print("=" * 30)
    
    if len(sys.argv) == 2:
        backup_file = sys.argv[1]
    else:
        # Ищем backup файлы
        backup_dir = "backups"
        if os.path.exists(backup_dir):
            files = [f for f in os.listdir(backup_dir) if f.endswith(('.sql', '.sql.gz'))]
            if files:
                print("Доступные backup файлы:")
                for i, f in enumerate(files, 1):
                    print(f"{i}. {f}")
                
                try:
                    choice = int(input("Выберите номер файла: ")) - 1
                    backup_file = os.path.join(backup_dir, files[choice])
                except:
                    print("Неверный выбор")
                    return
            else:
                print("Backup файлы не найдены")
                return
        else:
            print("Папка backups не найдена")
            return
    
    restore_backup(backup_file)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОтменено пользователем")
    
    input("Нажмите Enter для выхода...")