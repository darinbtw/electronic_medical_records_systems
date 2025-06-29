"""
Главный файл для запуска системы с встроенным автоматическим backup
"""
import os
import sys
import threading
import time
from pathlib import Path

# Добавляем корневую папку в path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import app
from src.database.connection import db
from src.config import config

# Устанавливаем schedule если его нет
try:
    import schedule
except ImportError:
    print("📦 Установка schedule для автоматического backup...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "schedule"], check=True)
    import schedule

def create_backup():
    """Создание backup"""
    from datetime import datetime
    import subprocess
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Автоматический backup...")
    
    try:
        result = subprocess.run([sys.executable, "scripts/backup.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Backup завершен")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Ошибка backup")
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Backup ошибка: {e}")

def cleanup_old_backups():
    """Удаление старых backup"""
    import glob
    import os
    from datetime import datetime
    
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        return
    
    # Удаляем файлы старше 7 дней
    import time
    now = time.time()
    week_ago = now - (7 * 24 * 60 * 60)
    
    count = 0
    for backup_file in glob.glob(f"{backup_dir}/backup_*.sql.gz"):
        if os.path.getmtime(backup_file) < week_ago:
            try:
                os.remove(backup_file)
                count += 1
            except:
                pass
    
    if count > 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🗑️ Удалено старых backup: {count}")

def backup_scheduler():
    """Планировщик backup в отдельном потоке"""
    # Настройка расписания
    schedule.every().day.at("07:45").do(create_backup)
    schedule.every().day.at("14:00").do(create_backup)
    schedule.every().day.at("03:00").do(cleanup_old_backups)
    
    print("📅 Автоматический backup настроен:")
    print("   - Каждый день в 02:00 и 14:00")
    print("   - Очистка старых файлов в 03:00")
    
    # Создаем первый backup
    create_backup()
    
    # Запускаем планировщик
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Проверяем каждую минуту
        except Exception as e:
            print(f"Ошибка планировщика: {e}")
            time.sleep(300)  # При ошибке ждем 5 минут

def start_backup_scheduler():
    """Запуск планировщика в отдельном потоке"""
    backup_thread = threading.Thread(target=backup_scheduler, daemon=True)
    backup_thread.start()
    return backup_thread

def check_system():
    """Проверка готовности системы"""
    print("🔍 Проверка системы...")
    
    if not db.test_connection():
        print("❌ База данных недоступна!")
        return False
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM patients")
            patients = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM doctors")
            doctors = cursor.fetchone()['count']
            
            print(f"✅ База данных готова: {patients} пациентов, {doctors} врачей")
    except Exception as e:
        print(f"❌ Ошибка при проверке БД: {e}")
        return False
    
    # Проверяем ключ шифрования
    if not os.path.exists('.encryption_key'):
        print("⚠️  Создаю ключ шифрования...")
        import secrets
        with open('.encryption_key', 'wb') as f:
            f.write(secrets.token_bytes(32))
        print("✅ Ключ шифрования создан")
    
    print("✅ Система готова к работе!")
    return True

def main():
    """Главная функция с встроенным автоматическим backup"""
    print("🏥 СИСТЕМА ЭЛЕКТРОННЫХ МЕДКАРТ")
    print("=" * 50)
    
    if not check_system():
        input("\nНажмите Enter для выхода...")
        return
    
    # Запускаем автоматический backup в фоне
    print("\n🕐 Запуск автоматического планировщика backup...")
    backup_thread = start_backup_scheduler()
    
    print(f"\n🚀 Запуск сервера на http://localhost:8000")
    print("📱 Веб-интерфейс доступен в браузере")
    print("📖 API документация: http://localhost:8000/api")
    print("💾 Автоматический backup работает в фоне")
    print("\nНажмите Ctrl+C для остановки\n")
    
    try:
        app.run(
            host=config.API_HOST,
            port=8000,
            debug=config.API_DEBUG
        )
    except KeyboardInterrupt:
        print("\n\n👋 Система и планировщик backup остановлены")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()