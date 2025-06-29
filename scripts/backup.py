"""
Универсальный backup (Python + pg_dump)
"""
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def try_pg_dump_backup():
    """Пытаемся использовать pg_dump"""
    print("🔄 Попытка pg_dump backup...")
    
    # Возможные команды pg_dump
    pg_dump_commands = [
        "pg_dump",
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        "scripts/pg_dump_wrapper.py"
    ]
    
    for cmd in pg_dump_commands:
        try:
            if cmd.endswith('.py'):
                test_result = subprocess.run([sys.executable, cmd, '--version'], 
                                           capture_output=True, text=True, timeout=10)
            else:
                test_result = subprocess.run([cmd, '--version'], 
                                           capture_output=True, text=True, timeout=10)
            
            if test_result.returncode == 0:
                print(f"✅ Найден: {cmd}")
                return True
        except:
            continue
    
    print("❌ pg_dump недоступен")
    return False

def python_backup():
    """Резервный Python backup"""
    print("🐍 Используем Python backup...")
    
    try:
        result = subprocess.run([sys.executable, "scripts/python_backup.py"], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Python backup успешен")
            return True
        else:
            print(f"❌ Ошибка Python backup: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    """Главная функция - пробуем pg_dump, потом Python"""
    print("💾 УНИВЕРСАЛЬНЫЙ BACKUP")
    print("=" * 25)
    
    # Сначала пробуем pg_dump
    if try_pg_dump_backup():
        print("Используем pg_dump (быстрее)")
    
    # Если pg_dump не работает, используем Python
    if python_backup():
        print("✅ Backup завершен успешно")
    else:
        print("❌ Все методы backup не сработали")

if __name__ == "__main__":
    main()