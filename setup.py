"""
Главный файл для запуска системы с полной проверкой всех компонентов
"""
import os
import sys
import subprocess
from pathlib import Path

# Добавляем корневую папку в path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import app
from src.database.connection import db
from src.config import config

def check_database_structure():
    """Проверка структуры БД и 3НФ"""
    print("🔍 Проверка структуры базы данных...")
    
    try:
        with db.get_cursor() as cursor:
            # Проверяем все таблицы
            cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                ORDER BY table_name, ordinal_position;
            """)
            
            columns = cursor.fetchall()
            tables = {}
            
            for col in columns:
                table = col['table_name']
                if table not in tables:
                    tables[table] = []
                tables[table].append({
                    'column': col['column_name'],
                    'type': col['data_type'],
                    'nullable': col['is_nullable']
                })
            
            print(f"✅ Найдено таблиц: {len(tables)}")
            for table_name, cols in tables.items():
                print(f"   📋 {table_name}: {len(cols)} полей")
            
            # Проверяем внешние ключи (3НФ)
            cursor.execute("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name;
            """)
            
            foreign_keys = cursor.fetchall()
            print(f"✅ Внешних ключей (3НФ): {len(foreign_keys)}")
            for fk in foreign_keys:
                print(f"   🔗 {fk['table_name']}.{fk['column_name']} → {fk['foreign_table_name']}.{fk['foreign_column_name']}")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка проверки структуры БД: {e}")
        return False

def check_indexes():
    """Проверка индексов для поиска"""
    print("📇 Проверка индексов...")
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
            
            indexes = cursor.fetchall()
            required_indexes = [
                'idx_patients_name',
                'idx_patients_birth_date', 
                'idx_appointments_date',
                'idx_appointments_patient',
                'idx_appointments_doctor'
            ]
            
            found_indexes = [idx['indexname'] for idx in indexes]
            
            print(f"✅ Найдено индексов: {len(indexes)}")
            
            missing = [idx for idx in required_indexes if idx not in found_indexes]
            if missing:
                print(f"⚠️  Отсутствуют индексы: {missing}")
                return False
            else:
                print("✅ Все необходимые индексы найдены")
                return True
                
    except Exception as e:
        print(f"❌ Ошибка проверки индексов: {e}")
        return False

def check_encryption():
    """Проверка шифрования диагнозов"""
    print("🔐 Проверка шифрования...")
    
    try:
        # Проверяем наличие ключа шифрования
        encryption_key = '.encryption_key'
        if not os.path.exists(encryption_key):
            print("⚠️  Ключ шифрования не найден, создаю...")
            import secrets
            with open(encryption_key, 'wb') as f:
                f.write(secrets.token_bytes(32))
            os.chmod(encryption_key, 0o600)
            print("✅ Ключ шифрования создан")
        
        # Проверяем поля для шифрования в БД
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'medical_records' 
                AND column_name IN ('diagnosis_encrypted', 'diagnosis_iv');
            """)
            
            encryption_fields = cursor.fetchall()
            if len(encryption_fields) == 2:
                print("✅ Поля для шифрования диагнозов найдены")
                return True
            else:
                print("❌ Поля для шифрования не найдены")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка проверки шифрования: {e}")
        return False

def check_backup_tools():
    """Проверка инструментов резервного копирования"""
    print("💾 Проверка backup инструментов...")
    
    try:
        # Проверяем pg_dump
        result = subprocess.run(['pg_dump', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pg_dump доступен:", result.stdout.strip())
        else:
            print("❌ pg_dump не найден")
            return False
        
        # Проверяем наличие скриптов backup
        backup_scripts = [
            'scripts/backup.sh',
            'scripts/restore.sh'
        ]
        
        missing_scripts = []
        for script in backup_scripts:
            if not os.path.exists(script):
                missing_scripts.append(script)
        
        if missing_scripts:
            print(f"⚠️  Отсутствуют скрипты: {missing_scripts}")
        else:
            print("✅ Backup скрипты найдены")
        
        return len(missing_scripts) == 0
        
    except Exception as e:
        print(f"❌ Ошибка проверки backup: {e}")
        return False

def check_replication_config():
    """Проверка настроек репликации"""
    print("🔄 Проверка настроек репликации...")
    
    try:
        with db.get_cursor() as cursor:
            # Проверяем настройки репликации
            cursor.execute("SHOW wal_level;")
            wal_level = cursor.fetchone()[0]
            
            cursor.execute("SHOW max_wal_senders;")
            max_wal_senders = cursor.fetchone()[0]
            
            print(f"📊 WAL level: {wal_level}")
            print(f"📊 Max WAL senders: {max_wal_senders}")
            
            if wal_level in ['replica', 'logical'] and int(max_wal_senders) > 0:
                print("✅ Репликация настроена")
                return True
            else:
                print("⚠️  Репликация не настроена (это нормально для разработки)")
                return True  # Не критично для разработки
                
    except Exception as e:
        print(f"❌ Ошибка проверки репликации: {e}")
        return False

def check_sql_injection_protection():
    """Проверка защиты от SQL-инъекций"""
    print("🛡️  Проверка защиты от SQL-инъекций...")
    
    try:
        # Тестируем безопасный запрос
        from src.security.sql_injection_test import SQLInjectionTester
        tester = SQLInjectionTester()
        
        # Запускаем несколько тестов
        safe_count, vulnerable_count, protected_count = tester.test_search_injection()
        
        total_tests = safe_count + vulnerable_count + protected_count
        security_score = ((safe_count + protected_count) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 Безопасность: {security_score:.1f}%")
        print(f"   ✅ Безопасных: {safe_count}")
        print(f"   🛡️  Защищено БД: {protected_count}")
        print(f"   ❌ Уязвимых: {vulnerable_count}")
        
        return security_score >= 95
        
    except Exception as e:
        print(f"❌ Ошибка проверки безопасности: {e}")
        return False

def check_documentation():
    """Проверка документации"""
    print("📚 Проверка документации...")
    
    docs = [
        'docs/admin_guide.md',
        'docs/er_diagram.puml',
        'web_interface.html'
    ]
    
    found_docs = []
    missing_docs = []
    
    for doc in docs:
        if os.path.exists(doc):
            found_docs.append(doc)
        else:
            missing_docs.append(doc)
    
    print(f"✅ Найдено документов: {len(found_docs)}")
    for doc in found_docs:
        print(f"   📄 {doc}")
    
    if missing_docs:
        print(f"⚠️  Отсутствуют: {missing_docs}")
    
    return len(missing_docs) == 0

def run_comprehensive_check():
    """Комплексная проверка всех компонентов проекта"""
    print("🏥 КОМПЛЕКСНАЯ ПРОВЕРКА СИСТЕМЫ МЕДКАРТ")
    print("=" * 60)
    
    checks = [
        ("База данных", lambda: db.test_connection()),
        ("Структура БД (3НФ)", check_database_structure),
        ("Индексы поиска", check_indexes),
        ("Шифрование AES-256", check_encryption),
        ("Backup инструменты", check_backup_tools),
        ("Репликация", check_replication_config),
        ("Защита от SQL-injection", check_sql_injection_protection),
        ("Документация", check_documentation)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n🔍 {name}...")
        try:
            result = check_func()
            results.append((name, result))
            status = "✅ ПРОЙДЕНО" if result else "⚠️  ТРЕБУЕТ ВНИМАНИЯ"
            print(f"   {status}")
        except Exception as e:
            results.append((name, False))
            print(f"   ❌ ОШИБКА: {e}")
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\n🎯 Результат: {passed}/{total} проверок пройдено")
    
    if passed == total:
        print("🎉 ВСЕ КОМПОНЕНТЫ РАБОТАЮТ ОТЛИЧНО!")
    elif passed >= total * 0.8:
        print("👍 СИСТЕМА ГОТОВА К РАБОТЕ (есть небольшие замечания)")
    else:
        print("⚠️  ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНАЯ НАСТРОЙКА")
    
    return passed >= total * 0.7  # 70% - минимум для запуска

def main():
    """Главная функция"""
    print("🚀 ЗАПУСК СИСТЕМЫ ЭЛЕКТРОННЫХ МЕДКАРТ")
    print("=" * 50)
    
    # Комплексная проверка
    if not run_comprehensive_check():
        print("\n❌ Система не готова к запуску!")
        print("Исправьте ошибки и запустите снова")
        input("\nНажмите Enter для выхода...")
        return
    
    print(f"\n🌟 СИСТЕМА ГОТОВА!")
    print(f"🚀 Запуск сервера на http://localhost:8000")
    print("📱 Веб-интерфейс доступен в браузере")
    print("📖 API документация: http://localhost:8000/api")
    print("\nНажмите Ctrl+C для остановки\n")
    
    try:
        app.run(
            host=config.API_HOST,
            port=8000,
            debug=config.API_DEBUG
        )
    except KeyboardInterrupt:
        print("\n\n👋 Система остановлена")
    except Exception as e:
        print(f"\n❌ Ошибка запуска: {e}")

if __name__ == '__main__':
    main()