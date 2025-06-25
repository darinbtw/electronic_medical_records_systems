#!/usr/bin/env python3
"""
Скрипт установки и настройки проекта
"""
import os
import sys
import subprocess
import platform

def run_command(cmd, description):
    """Выполнить команду с выводом"""
    print(f"\n🔄 {description}...")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Ошибка при: {description}")
        return False
    print(f"✅ {description} - готово!")
    return True

def check_psql():
    """Проверка доступности psql"""
    try:
        result = subprocess.run("psql --version", shell=True, capture_output=True)
        return result.returncode == 0
    except:
        return False

def main():
    print("🏥 УСТАНОВКА СИСТЕМЫ ЭЛЕКТРОННЫХ МЕДКАРТ")
    print("=" * 50)
    
    # Установка зависимостей
    if not run_command("pip install -r requirements.txt", "Установка зависимостей"):
        return False
    
    # Проверка подключения
    if not run_command("python tests/test_connection.py", "Проверка подключения к БД"):
        return False
    
    # Создание таблиц
    if not run_command("python src/database/create_table.py", "Создание таблиц"):
        return False
    
    # Загрузка данных
    if check_psql():
        # Если psql доступен, используем его
        if platform.system() == "Windows":
            cmd = 'psql -U postgres -d medical_records -f "src/sql_test_query/basic_test_data.sql"'
        else:
            cmd = "psql -U postgres -d medical_records -f src/sql_test_query/basic_test_data.sql"
        
        if not run_command(cmd, "Загрузка тестовых данных через psql"):
            print("⚠️  Попытка загрузить данные через Python...")
            if not run_command("python src/database/load_test_data.py", "Загрузка тестовых данных"):
                return False
    else:
        # psql недоступен, используем Python
        print("ℹ️  psql не найден, используем Python для загрузки данных")
        if not run_command("python src/database/load_test_data.py", "Загрузка тестовых данных"):
            return False
    
    print("\n✅ Установка завершена!")
    print("\n🚀 Для запуска системы:")
    print("   python run.py")
    
    # Создаем .encryption_key если его нет
    if not os.path.exists('.encryption_key'):
        print("\n🔐 Генерация ключа шифрования...")
        import secrets
        with open('.encryption_key', 'wb') as f:
            f.write(secrets.token_bytes(32))
        print("✅ Ключ шифрования создан")
    
    return True

if __name__ == "__main__":
    success = main()
    input("\nНажмите Enter для выхода...")
    sys.exit(0 if success else 1)