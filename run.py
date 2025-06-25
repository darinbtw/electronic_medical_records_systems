"""
Главный файл для запуска системы
"""
import os
import sys
from pathlib import Path

# Добавляем корневую папку в path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import app
from src.database.connection import db
from src.config import config

def check_system():
    """Проверка готовности системы"""
    print("🔍 Проверка системы...")
    
    # Проверка БД
    if not db.test_connection():
        print("❌ База данных недоступна!")
        print("   Проверьте настройки в .env файле")
        return False
    
    # Проверка таблиц
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables_count = cursor.fetchone()['count']
            
            if tables_count == 0:
                print("❌ Таблицы не созданы!")
                print("   Запустите: python setup.py")
                return False
            
            # Проверка данных
            cursor.execute("SELECT COUNT(*) as count FROM patients")
            patients = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM doctors")
            doctors = cursor.fetchone()['count']
            
            print(f"✅ База данных готова: {patients} пациентов, {doctors} врачей")
    except Exception as e:
        print(f"❌ Ошибка при проверке БД: {e}")
        return False
    
    # Проверка ключа шифрования
    if not os.path.exists('.encryption_key'):
        print("⚠️  Создаю ключ шифрования...")
        import secrets
        with open('.encryption_key', 'wb') as f:
            f.write(secrets.token_bytes(32))
        print("✅ Ключ шифрования создан")
    
    print("✅ Система готова к работе!")
    return True

def main():
    """Запуск приложения"""
    print("🏥 СИСТЕМА ЭЛЕКТРОННЫХ МЕДКАРТ")
    print("=" * 50)
    
    if not check_system():
        input("\nНажмите Enter для выхода...")
        return
    
    print(f"\n🚀 Запуск сервера...")
    print(f"📍 URL: http://localhost:{config.API_PORT}")
    print(f"📚 API Endpoints:")
    print(f"   - GET  /              - Главная страница")
    print(f"   - GET  /health        - Проверка состояния")
    print(f"   - GET  /api/patients  - Список пациентов")
    print(f"   - GET  /api/search    - Поиск пациентов")
    print(f"   - POST /api/validate  - Валидация данных")
    print("\nНажмите Ctrl+C для остановки\n")
    
    try:
        # Используем порт 8000 как в main.py
        app.run(
            host=config.API_HOST,
            port=8000,  # Изменено на 8000
            debug=config.API_DEBUG
        )
    except KeyboardInterrupt:
        print("\n\n👋 Сервер остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")
        input("\nНажмите Enter для выхода...")

if __name__ == '__main__':
    main()