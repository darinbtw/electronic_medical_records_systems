import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_environment():
    """Проверка переменных окружения"""
    print("=== Проверка переменных окружения ===")
    
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: НЕ НАЙДЕНА")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def test_database_connection():
    """Проверка подключения к БД"""
    print("\n=== Проверка подключения к БД ===")
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }
        
        print(f"Подключение: {connection_params['host']}:{connection_params['port']}")
        print(f"База: {connection_params['database']}")
        
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Подключение успешно!")
        print(f"✅ PostgreSQL: {version['version'][:50]}...")
        
        # Проверка таблиц
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        if tables:
            print(f"✅ Таблиц найдено: {len(tables)}")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table['table_name']}")
                count = cursor.fetchone()['count']
                print(f"   - {table['table_name']}: {count} записей")
        else:
            print("⚠️  Таблицы не найдены. Создайте их:")
            print("   python src/database/create_table.py")
        
        cursor.close()
        conn.close()
        return True
        
    except ImportError:
        print("❌ psycopg2 не установлен: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def main():
    """Главная функция"""
    print("🏥 ТЕСТИРОВАНИЕ СИСТЕМЫ МЕДИЦИНСКИХ КАРТ")
    print("=" * 50)
    
    checks = [
        ("Переменные окружения", test_environment),
        ("Подключение к БД", test_database_connection)
    ]
    
    results = []
    for name, func in checks:
        try:
            result = func()
            results.append(result)
        except Exception as e:
            print(f"❌ Ошибка в {name}: {e}")
            results.append(False)
    
    print(f"\n📊 Результат: {sum(results)}/{len(results)} тестов пройдено")
    
    if all(results):
        print("🎉 Система готова!")
        print("\n🚀 Следующие шаги:")
        print("1. python src/database/create_table.py  # создать таблицы")
        print("2. psql -d medical_records -f src/sql_test_query/basic_test_data.sql  # добавить данные")
        print("3. python src/main.py  # запустить API")
    else:
        print("⚠️  Исправьте ошибки")
    
    return all(results)

if __name__ == "__main__":
    success = main()
    input("\nНажмите Enter...")
    sys.exit(0 if success else 1)