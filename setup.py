#!/usr/bin/env python3
"""
Скрипт установки и настройки проекта
"""
import os
import sys
import subprocess

def run_command(cmd, description):
    """Выполнить команду с выводом"""
    print(f"\n🔄 {description}...")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Ошибка при: {description}")
        return False
    print(f"✅ {description} - готово!")
    return True

def main():
    print("🏥 УСТАНОВКА СИСТЕМЫ ЭЛЕКТРОННЫХ МЕДКАРТ")
    print("=" * 50)
    
    steps = [
        ("pip install -r requirements.txt", "Установка зависимостей"),
        ("python tests/test_connection.py", "Проверка подключения к БД"),
        ("python src/database/create_table.py", "Создание таблиц"),
        ("psql -U postgres -d medical_records -f src/sql_test_query/basic_test_data.sql", "Загрузка тестовых данных"),
    ]
    
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            print("\n⚠️  Установка прервана. Исправьте ошибки и запустите снова.")
            return False
    
    print("\n✅ Установка завершена!")
    print("\n🚀 Для запуска системы:")
    print("   python run.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)