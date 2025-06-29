# Создайте файл: quick_db_test.py

import os
import psycopg2
from dotenv import load_dotenv

def quick_test():
    """Быстрая проверка БД без проблем с кодировкой"""
    
    load_dotenv()
    
    print("Быстрая проверка базы данных...")
    print("=" * 40)
    
    try:
        # Подключение с явным указанием кодировки
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'medical_records'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            client_encoding='utf8'  # Явно указываем кодировку
        )
        
        cursor = conn.cursor()
        
        print("УСПЕХ: Подключение к БД работает!")
        
        # Проверяем таблицы
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"Найдено таблиц: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  - {table_name}: {count} записей")
            except Exception as e:
                print(f"  - {table_name}: ошибка ({str(e)[:50]})")
        
        cursor.close()
        conn.close()
        
        print("\nСтатус: ГОТОВО К ЗАПУСКУ!")
        return True
        
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        print(f"ОШИБКА подключения: {error_msg}")
        
        if "does not exist" in error_msg:
            print("\nРЕШЕНИЕ: База данных не существует!")
            print("Выполните команду:")
            print('psql -U postgres -c "CREATE DATABASE medical_records;"')
            
        elif "authentication failed" in error_msg:
            print("\nРЕШЕНИЕ: Неверный пароль!")
            print("Проверьте пароль в файле .env")
            
        elif "could not connect" in error_msg:
            print("\nРЕШЕНИЕ: PostgreSQL не запущен!")
            print("Запустите PostgreSQL сервер")
            
        return False
        
    except Exception as e:
        print(f"НЕОЖИДАННАЯ ОШИБКА: {e}")
        return False

def create_database_if_needed():
    """Создать БД medical_records если её нет"""
    
    load_dotenv()
    
    print("\nПопытка создать БД medical_records...")
    
    try:
        # Подключаемся к postgres (системная БД)
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database='postgres',  # Подключаемся к системной БД
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            client_encoding='utf8'
        )
        
        conn.autocommit = True  # Важно для CREATE DATABASE
        cursor = conn.cursor()
        
        # Проверяем, существует ли БД
        cursor.execute("""
            SELECT 1 FROM pg_database WHERE datname = 'medical_records'
        """)
        
        if cursor.fetchone():
            print("БД medical_records уже существует")
        else:
            # Создаем БД
            cursor.execute("CREATE DATABASE medical_records")
            print("СОЗДАНА база данных medical_records")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Не удалось создать БД: {e}")
        return False

def main():
    print("ПРОВЕРКА И СОЗДАНИЕ БД")
    print("=" * 30)
    
    # Сначала пробуем подключиться
    if quick_test():
        print("\nБД готова! Можно запускать систему:")
        print("python run.py")
        return
    
    # Если не получилось, пробуем создать БД
    print("\nПробуем создать БД...")
    if create_database_if_needed():
        # Создаем таблицы
        print("\nСоздаем таблицы...")
        import subprocess
        result = subprocess.run("python src/database/create_table.py", shell=True)
        
        if result.returncode == 0:
            print("Таблицы созданы!")
            
            # Загружаем данные
            print("Загружаем тестовые данные...")
            subprocess.run("python src/database/load_test_data.py", shell=True)
            
            print("\nПроверяем результат...")
            if quick_test():
                print("\nВСЕ ГОТОВО! Запускайте:")
                print("python run.py")
            else:
                print("Все еще есть проблемы...")
        else:
            print("Ошибка создания таблиц")
    else:
        print("\nРУЧНОЕ РЕШЕНИЕ:")
        print("1. Запустите PostgreSQL")
        print("2. Выполните:")
        print('   psql -U postgres -c "CREATE DATABASE medical_records;"')
        print("3. Запустите снова: python quick_db_test.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nОтменено пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
    
    input("\nНажмите Enter для выхода...")