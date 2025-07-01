#!/usr/bin/env python3
"""
Скрипт для исправления проблемы с TDE при создании пациентов
"""
import os
import sys
from pathlib import Path

# Добавляем корневую папку в path
current_dir = Path(__file__).parent
project_root = current_dir.parent if 'scripts' in str(current_dir) else current_dir
sys.path.insert(0, str(project_root))

def check_tde_status():
    """Проверка статуса TDE"""
    print("🔍 Проверка статуса TDE...")
    
    tde_enabled = os.getenv('TDE_ENABLED', 'False').lower() == 'true'
    print(f"TDE_ENABLED в переменных окружения: {tde_enabled}")
    
    # Проверяем наличие ключа шифрования
    key_file = os.getenv('ENCRYPTION_KEY_FILE', '.encryption_key')
    key_exists = os.path.exists(key_file)
    print(f"Файл ключа шифрования ({key_file}): {'существует' if key_exists else 'отсутствует'}")
    
    return tde_enabled, key_exists

def check_database_structure():
    """Проверка структуры БД для TDE"""
    print("\n🔍 Проверка структуры БД...")
    
    try:
        from src.database.connection import db
        
        with db.get_cursor() as cursor:
            # Проверяем наличие TDE полей в таблице patients
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'patients' 
                AND column_name LIKE '%_encrypted'
                ORDER BY column_name
            """)
            
            encrypted_columns = [row['column_name'] for row in cursor.fetchall()]
            
            print(f"Зашифрованные поля в таблице patients: {encrypted_columns}")
            
            expected_columns = ['address_encrypted', 'email_encrypted', 'phone_encrypted']
            missing_columns = [col for col in expected_columns if col not in encrypted_columns]
            
            if missing_columns:
                print(f"❌ Отсутствуют поля: {missing_columns}")
                return False
            else:
                print("✅ Все необходимые TDE поля присутствуют")
                return True
                
    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")
        return False

def run_migration():
    """Запуск миграции для добавления TDE полей"""
    print("\n🔄 Запуск миграции TDE...")
    
    try:
        from src.database.connection import db
        
        # Читаем SQL скрипт миграции
        migration_sql = """
        -- Добавляем TDE поля для таблицы patients
        DO $$
        BEGIN
            -- Добавляем поля для шифрования телефона
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'patients' AND column_name = 'phone_encrypted'
            ) THEN
                ALTER TABLE patients ADD COLUMN phone_encrypted BYTEA;
                RAISE NOTICE 'Добавлен столбец phone_encrypted';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'patients' AND column_name = 'phone_iv'
            ) THEN
                ALTER TABLE patients ADD COLUMN phone_iv BYTEA;
                RAISE NOTICE 'Добавлен столбец phone_iv';
            END IF;

            -- Добавляем поля для шифрования email
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'patients' AND column_name = 'email_encrypted'
            ) THEN
                ALTER TABLE patients ADD COLUMN email_encrypted BYTEA;
                RAISE NOTICE 'Добавлен столбец email_encrypted';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'patients' AND column_name = 'email_iv'
            ) THEN
                ALTER TABLE patients ADD COLUMN email_iv BYTEA;
                RAISE NOTICE 'Добавлен столбец email_iv';
            END IF;

            -- Добавляем поля для шифрования адреса
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'patients' AND column_name = 'address_encrypted'
            ) THEN
                ALTER TABLE patients ADD COLUMN address_encrypted BYTEA;
                RAISE NOTICE 'Добавлен столбец address_encrypted';
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'patients' AND column_name = 'address_iv'
            ) THEN
                ALTER TABLE patients ADD COLUMN address_iv BYTEA;
                RAISE NOTICE 'Добавлен столбец address_iv';
            END IF;
        END $$;
        """
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(migration_sql)
            conn.commit()
            
        print("✅ Миграция TDE выполнена успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False

def test_patient_creation():
    """Тест создания пациента с TDE"""
    print("\n🧪 Тест создания пациента с TDE...")
    
    try:
        from src.database.connection import db
        
        # Тестовые данные пациента
        test_patient = {
            'first_name': 'Тест',
            'last_name': 'Тестович',
            'middle_name': 'Тестовый',
            'birth_date': '1990-01-01',
            'gender': 'M',
            'phone': '+7 (999) 123-45-67',
            'email': 'test@example.com',
            'address': 'г. Тестовый, ул. Тестовая, д. 1'
        }
        
        # Проверяем, включен ли TDE
        tde_enabled = os.getenv('TDE_ENABLED', 'False').lower() == 'true'
        
        if tde_enabled:
            try:
                from src.security.tde import TDEManager
                tde_manager = TDEManager()
                
                # Шифруем данные
                phone_encrypted, phone_iv = tde_manager.encrypt_field('patients', 'phone', test_patient['phone'])
                email_encrypted, email_iv = tde_manager.encrypt_field('patients', 'email', test_patient['email'])
                address_encrypted, address_iv = tde_manager.encrypt_field('patients', 'address', test_patient['address'])
                
                print("✅ Шифрование полей работает корректно")
                
                # Проверяем расшифровку
                decrypted_phone = tde_manager.decrypt_field('patients', 'phone', phone_encrypted, phone_iv)
                decrypted_email = tde_manager.decrypt_field('patients', 'email', email_encrypted, email_iv)
                decrypted_address = tde_manager.decrypt_field('patients', 'address', address_encrypted, address_iv)
                
                if (decrypted_phone == test_patient['phone'] and 
                    decrypted_email == test_patient['email'] and 
                    decrypted_address == test_patient['address']):
                    print("✅ Расшифровка работает корректно")
                else:
                    print("❌ Ошибка расшифровки данных")
                    return False
                
                # Тестируем вставку в БД
                with db.get_cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO patients 
                        (first_name, last_name, middle_name, birth_date, gender, 
                         phone_encrypted, phone_iv, email_encrypted, email_iv, 
                         address_encrypted, address_iv)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        test_patient['first_name'],
                        test_patient['last_name'], 
                        test_patient['middle_name'],
                        test_patient['birth_date'],
                        test_patient['gender'],
                        phone_encrypted,
                        phone_iv,
                        email_encrypted,
                        email_iv,
                        address_encrypted,
                        address_iv
                    ))
                    
                    result = cursor.fetchone()
                    test_patient_id = result['id']
                    
                    print(f"✅ Тестовый пациент создан с ID: {test_patient_id}")
                    
                    # Удаляем тестового пациента
                    cursor.execute("DELETE FROM patients WHERE id = %s", (test_patient_id,))
                    print("🗑️ Тестовый пациент удален")
                    
                return True
                
            except ImportError:
                print("❌ Модуль TDE не найден")
                return False
        else:
            print("ℹ️ TDE отключен, тестируем обычную вставку...")
            
            with db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO patients 
                    (first_name, last_name, middle_name, birth_date, gender, phone, email, address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    test_patient['first_name'],
                    test_patient['last_name'], 
                    test_patient['middle_name'],
                    test_patient['birth_date'],
                    test_patient['gender'],
                    test_patient['phone'],
                    test_patient['email'],
                    test_patient['address']
                ))
                
                result = cursor.fetchone()
                test_patient_id = result['id']
                
                print(f"✅ Тестовый пациент создан с ID: {test_patient_id}")
                
                # Удаляем тестового пациента
                cursor.execute("DELETE FROM patients WHERE id = %s", (test_patient_id,))
                print("🗑️ Тестовый пациент удален")
                
            return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_env_file():
    """Исправление .env файла для TDE"""
    print("\n🔧 Проверка и исправление .env файла...")
    
    env_file = project_root / '.env'
    
    if not env_file.exists():
        print("❌ Файл .env не найден")
        return False
    
    # Читаем текущий .env
    with open(env_file, 'r', encoding='utf-8') as f:
        env_content = f.read()
    
    # Проверяем наличие TDE_ENABLED
    if 'TDE_ENABLED' not in env_content:
        print("➕ Добавляем TDE_ENABLED в .env")
        with open(env_file, 'a', encoding='utf-8') as f:
            f.write('\n# TDE Configuration\n')
            f.write('TDE_ENABLED=false\n')
            f.write('ENCRYPTION_KEY_FILE=.encryption_key\n')
        print("✅ TDE настройки добавлены в .env")
    else:
        print("✅ TDE настройки уже есть в .env")
    
    return True

def main():
    """Главная функция диагностики и исправления TDE"""
    print("🔒 ДИАГНОСТИКА И ИСПРАВЛЕНИЕ ПРОБЛЕМ TDE")
    print("=" * 60)
    
    # Шаг 1: Проверка статуса TDE
    tde_enabled, key_exists = check_tde_status()
    
    # Шаг 2: Исправление .env файла
    fix_env_file()
    
    # Шаг 3: Проверка структуры БД
    db_ready = check_database_structure()
    
    # Шаг 4: Запуск миграции если нужно
    if not db_ready:
        print("\n🔄 Структура БД не готова для TDE, запускаем миграцию...")
        if run_migration():
            db_ready = check_database_structure()
    
    # Шаг 5: Тестирование создания пациента
    if db_ready:
        test_success = test_patient_creation()
    else:
        test_success = False
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    
    print(f"TDE включен: {'✅' if tde_enabled else '❌'}")
    print(f"Ключ шифрования: {'✅' if key_exists else '❌'}")
    print(f"Структура БД: {'✅' if db_ready else '❌'}")
    print(f"Тест создания пациента: {'✅' if test_success else '❌'}")
    
    if tde_enabled and db_ready and test_success:
        print("\n🎉 ВСЕ ПРОБЛЕМЫ ИСПРАВЛЕНЫ!")
        print("Система готова к работе с TDE")
    elif not tde_enabled and test_success:
        print("\n✅ Система работает БЕЗ TDE")
        print("Для включения TDE установите в .env: TDE_ENABLED=true")
    else:
        print("\n⚠️ ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНОЕ ИСПРАВЛЕНИЕ")
        
        if not db_ready:
            print("1. Запустите миграцию БД: python scripts/tde_migration.sql")
        
        if tde_enabled and not key_exists:
            print("2. Создайте ключ шифрования: будет создан автоматически при первом запуске")
        
        if not test_success:
            print("3. Проверьте логи ошибок выше")
    
    print("\n📚 Дополнительная информация:")
    print("- Для включения TDE: установите TDE_ENABLED=true в .env")
    print("- Для отключения TDE: установите TDE_ENABLED=false в .env")
    print("- Миграция БД: python -c \"from scripts.fix_tde_issue import run_migration; run_migration()\"")
    print("- Тест системы: python scripts/fix_tde_issue.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Диагностика прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nНажмите Enter для выхода...")