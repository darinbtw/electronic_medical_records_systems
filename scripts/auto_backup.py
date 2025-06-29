"""
Автоматический планировщик backup
"""
import time
import schedule
import subprocess
import sys
import os
from datetime import datetime

def create_backup():
    """Создание backup"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Создание автоматического backup...")
    
    try:
        # Запускаем backup скрипт
        result = subprocess.run([sys.executable, "backup.py"], 
                              cwd="scripts",
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ Backup создан успешно")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Ошибка backup: {result.stderr}")
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ❌ Исключение: {e}")

def cleanup_old_backups():
    """Удаление старых backup (старше 7 дней)"""
    import glob
    import time
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        return
    
    now = time.time()
    week_ago = now - (7 * 24 * 60 * 60)  # 7 дней в секундах
    
    for backup_file in glob.glob(f"{backup_dir}/backup_*.sql.gz"):
        if os.path.getmtime(backup_file) < week_ago:
            try:
                os.remove(backup_file)
                print(f"Удален старый backup: {backup_file}")
            except Exception as e:
                print(f"Ошибка удаления {backup_file}: {e}")

def main():
    """Главная функция планировщика"""
    print("🕐 АВТОМАТИЧЕСКИЙ ПЛАНИРОВЩИК BACKUP")
    print("=" * 40)
    
    # Настройка расписания
    schedule.every().day.at("07:45").do(create_backup)      # Каждый день в 7:45
    schedule.every().day.at("14:00").do(create_backup)      # Каждый день в 14:00
    schedule.every().day.at("03:00").do(cleanup_old_backups) # Очистка в 3:00
    
    print("📅 Расписание backup:")
    print("  - Каждый день в 02:00")
    print("  - Каждый день в 14:00") 
    print("  - Очистка старых файлов в 03:00")
    print("\nДля остановки нажмите Ctrl+C")
    
    # Создаем первый backup сразу
    print("\n🔄 Создание начального backup...")
    create_backup()
    
    # Запускаем планировщик
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Проверяем каждую минуту
            
    except KeyboardInterrupt:
        print("\n\n👋 Планировщик остановлен")

if __name__ == "__main__":
    # Устанавливаем schedule если его нет
    try:
        import schedule
    except ImportError:
        print("Установка schedule...")
        subprocess.run([sys.executable, "-m", "pip", "install", "schedule"])
        import schedule
    
    main()