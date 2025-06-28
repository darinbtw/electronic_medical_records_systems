import os
import sys
import subprocess
import secrets
from pathlib import Path

if sys.platform.startswith('win'):
    os.system('chcp 65001 > nul')  # UTF-8 кодировка

def step_message(step, message):
    """Красивый вывод"""
    print(f"\n{'='*60}")
    print(f"ШАГ {step}: {message}")
    print('='*60)

def run_command(cmd, description, ignore_errors=False):
    """Выполнить команду с проверкой"""
    print(f"Выполняется: {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0 or ignore_errors:
            print(f"УСПЕШНО: {description}")
            if result.stdout:
                print(f"   Результат: {result.stdout.strip()[:100]}")
            return True
        else:
            print(f"ОШИБКА в {description}: {result.stderr}")
            return False
    except Exception as e:
        print(f"ИСКЛЮЧЕНИЕ в {description}: {e}")
        return False

def main():
    print("ПОЛНАЯ УСТАНОВКА СИСТЕМЫ МЕДКАРТ")
    print("Этот скрипт настроит ВСЕ компоненты")
    
    # Шаг 1: Исправляем .env файл
    step_message(1, "ИСПРАВЛЕНИЕ КОНФИГУРАЦИИ")
    
    if os.path.exists('.env'):
        print("Файл .env найден, проверяем содержимое...")
        
        # Читаем текущий .env
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Исправляем название БД если нужно
        if 'DB_NAME=postgres' in env_content:
            print("ВНИМАНИЕ: Найдено DB_NAME=postgres")
            print("Система может работать с базой 'postgres', но лучше создать отдельную БД")
            
            choice = input("Создать отдельную БД 'medical_records'? (y/n): ").lower()
            if choice == 'y':
                # Создаем БД через psql
                create_db_cmd = 'psql -U postgres -c "CREATE DATABASE medical_records;"'
                print("Создаем базу данных medical_records...")
                result = run_command(create_db_cmd, "Создание БД medical_records", ignore_errors=True)
                
                if result:
                    # Обновляем .env
                    new_content = env_content.replace('DB_NAME=postgres', 'DB_NAME=medical_records')
                    with open('.env', 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print("ОБНОВЛЕН файл .env - теперь используется medical_records")
                else:
                    print("НЕ УДАЛОСЬ создать БД, продолжаем с 'postgres'")
            else:
                print("Продолжаем работу с БД 'postgres'")
    else:
        print("ОШИБКА: Файл .env не найден!")
        print("Создайте файл .env по образцу .env.example")
        return False
    
    # Шаг 2: Установка зависимостей
    step_message(2, "УСТАНОВКА ЗАВИСИМОСТЕЙ")
    
    if not run_command("pip install -r requirements.txt", "Установка Python пакетов"):
        print("Пробуем установить основные пакеты...")
        basic_packages = "flask flask-cors psycopg2-binary python-dotenv cryptography pyjwt"
        if not run_command(f"pip install {basic_packages}", "Установка основных пакетов"):
            return False
    
    # Шаг 3: Создание ключа шифрования
    step_message(3, "НАСТРОЙКА БЕЗОПАСНОСТИ")
    
    if not os.path.exists('.encryption_key'):
        print("Создаю ключ шифрования...")
        with open('.encryption_key', 'wb') as f:
            f.write(secrets.token_bytes(32))
        print("СОЗДАН ключ шифрования")
    else:
        print("Ключ шифрования уже существует")
    
    # Шаг 4: Простая проверка подключения к БД
    step_message(4, "ПРОВЕРКА БАЗЫ ДАННЫХ")
    
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Параметры подключения
        conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'postgres'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
        
        print(f"Подключение к: {conn_params['host']}:{conn_params['port']}")
        print(f"База данных: {conn_params['database']}")
        
        # Тестируем подключение
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"УСПЕШНО: PostgreSQL подключен")
        print(f"Версия: {version[:50]}...")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"ОШИБКА подключения к БД: {e}")
        print("Проверьте:")
        print("   - PostgreSQL запущен")
        print("   - Пароль в .env правильный")
        print("   - База данных существует")
        return False
    
    # Шаг 5: Создание таблиц
    step_message(5, "СОЗДАНИЕ ТАБЛИЦ")
    
    if not run_command("python src/database/create_table.py", "Создание таблиц"):
        print("ОШИБКА создания таблиц!")
        return False
    
    # Шаг 6: Загрузка тестовых данных
    step_message(6, "ЗАГРУЗКА ТЕСТОВЫХ ДАННЫХ")
    
    db_name = os.getenv('DB_NAME', 'postgres')
    psql_cmd = f'psql -U postgres -d {db_name} -f "src/sql_test_query/basic_test_data.sql"'
    
    psql_success = run_command(psql_cmd, "Загрузка данных через psql", ignore_errors=True)
    
    if not psql_success:
        print("psql недоступен, используем Python...")
        if not run_command("python src/database/load_test_data.py", "Загрузка данных через Python"):
            print("ВНИМАНИЕ: Не удалось загрузить тестовые данные")
    
    # Финальная проверка
    step_message(7, "ФИНАЛЬНАЯ ПРОВЕРКА")
    
    print("Проверяем ключевые файлы...")
    
    files_to_check = [
        ('.env', 'Конфигурация'),
        ('.encryption_key', 'Ключ шифрования'),
        ('src/main.py', 'Главный API'),
        ('run.py', 'Файл запуска'),
        ('web_interface.html', 'Веб-интерфейс')
    ]
    
    all_good = True
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"НАЙДЕН: {description} ({file_path})")
        else:
            print(f"НЕ НАЙДЕН: {description} ({file_path})")
            all_good = False
    
    if all_good:
        print("\nУСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!")
        print("Для запуска системы:")
        print("   python run.py")
        print("\nВеб-интерфейс будет доступен:")
        print("   http://localhost:8000")
        return True
    else:
        print("\nЕсть проблемы с файлами!")
        return False

if __name__ == "__main__":
    try:
        success = main()
        input(f"\nНажмите Enter для {'запуска' if success else 'выхода'}...")
        
        if success:
            print("Запускаю систему...")
            os.system("python run.py")
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        input("Нажмите Enter для выхода...")