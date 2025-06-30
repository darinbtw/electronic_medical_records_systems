#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление поврежденного ключа TDE
Удаляет поврежденный файл ключа и позволяет системе создать новый
"""

import os
import sys
from pathlib import Path

def fix_tde_key():
    """Исправление поврежденного TDE ключа"""
    print("🔧 ИСПРАВЛЕНИЕ TDE КЛЮЧА")
    print("=" * 40)
    
    # Файлы ключей TDE
    tde_files = [
        '.tde_master_key',
        '.encryption_key',
        '.tde_master_key.backup.*'
    ]
    
    print("🔍 Проверка TDE файлов...")
    
    for tde_file in tde_files[:2]:  # Только основные файлы
        if os.path.exists(tde_file):
            try:
                # Проверяем размер файла
                file_size = os.path.getsize(tde_file)
                print(f"📄 Найден {tde_file}: {file_size} байт")
                
                if file_size == 0:
                    print(f"⚠️ Файл {tde_file} пустой!")
                    
                    # Удаляем пустой файл
                    os.remove(tde_file)
                    print(f"🗑️ Удален пустой файл {tde_file}")
                    
                elif tde_file == '.tde_master_key':
                    # Проверяем JSON формат
                    try:
                        with open(tde_file, 'r') as f:
                            content = f.read().strip()
                            
                        if not content:
                            print(f"⚠️ Файл {tde_file} пустой!")
                            os.remove(tde_file)
                            print(f"🗑️ Удален пустой файл {tde_file}")
                        elif not content.startswith('{'):
                            print(f"⚠️ Файл {tde_file} не содержит JSON!")
                            
                            # Создаем backup поврежденного файла
                            backup_name = f"{tde_file}.corrupted.backup"
                            os.rename(tde_file, backup_name)
                            print(f"💾 Поврежденный файл сохранен как {backup_name}")
                        else:
                            import json
                            try:
                                with open(tde_file, 'r') as f:
                                    json.load(f)
                                print(f"✅ Файл {tde_file} корректен")
                            except json.JSONDecodeError as e:
                                print(f"❌ JSON ошибка в {tde_file}: {e}")
                                
                                # Создаем backup и удаляем
                                backup_name = f"{tde_file}.corrupted.backup"
                                os.rename(tde_file, backup_name)
                                print(f"💾 Поврежденный файл сохранен как {backup_name}")
                                
                    except Exception as e:
                        print(f"❌ Ошибка проверки {tde_file}: {e}")
                        
                        # Создаем backup и удаляем
                        backup_name = f"{tde_file}.corrupted.backup"
                        try:
                            os.rename(tde_file, backup_name)
                            print(f"💾 Поврежденный файл сохранен как {backup_name}")
                        except:
                            os.remove(tde_file)
                            print(f"🗑️ Удален поврежденный файл {tde_file}")
                
            except Exception as e:
                print(f"❌ Ошибка обработки {tde_file}: {e}")
        else:
            print(f"📄 Файл {tde_file} не найден (это нормально)")
    
    print("\n🔧 ОТКЛЮЧЕНИЕ TDE ДЛЯ ИСПРАВЛЕНИЯ")
    print("=" * 40)
    
    # Временно отключаем TDE в .env
    env_file = '.env'
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                env_content = f.read()
            
            # Комментируем или изменяем TDE_ENABLED
            lines = env_content.split('\n')
            new_lines = []
            tde_found = False
            
            for line in lines:
                if line.strip().startswith('TDE_ENABLED'):
                    new_lines.append('TDE_ENABLED=False  # Временно отключено для исправления')
                    tde_found = True
                    print("🔧 TDE_ENABLED установлен в False")
                else:
                    new_lines.append(line)
            
            if not tde_found:
                new_lines.append('')
                new_lines.append('# TDE Settings')
                new_lines.append('TDE_ENABLED=False  # Временно отключено для исправления')
                print("🔧 Добавлен TDE_ENABLED=False")
            
            # Сохраняем обновленный .env
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))
            
            print("✅ Файл .env обновлен")
            
        except Exception as e:
            print(f"❌ Ошибка обновления .env: {e}")
    else:
        print("❌ Файл .env не найден!")
        
        # Создаем минимальный .env
        env_content = """# Минимальные настройки
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medical_records
DB_USER=postgres
DB_PASSWORD=

# TDE отключен для исправления
TDE_ENABLED=False

# API
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ Создан новый файл .env")

def create_fixed_tde_setup():
    """Создание исправленного setup для TDE"""
    print("\n🛠️ СОЗДАНИЕ ИСПРАВЛЕННОГО TDE SETUP")
    print("=" * 40)
    
    setup_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Безопасная настройка TDE с проверкой ошибок
\"\"\"

import os
import sys
import json
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_tde_setup():
    \"\"\"Безопасная настройка TDE\"\"\"
    print("🔒 БЕЗОПАСНАЯ НАСТРОЙКА TDE")
    print("=" * 40)
    
    # Проверяем, что старые файлы удалены
    tde_files = ['.tde_master_key', '.encryption_key']
    for tde_file in tde_files:
        if os.path.exists(tde_file):
            print(f"⚠️ Найден старый файл {tde_file}")
            choice = input(f"Удалить {tde_file}? (y/n): ").lower()
            if choice == 'y':
                os.remove(tde_file)
                print(f"🗑️ Файл {tde_file} удален")
            else:
                print(f"⚠️ Файл {tde_file} оставлен. Может возникнуть ошибка!")
    
    # Включаем TDE в .env
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()
        
        # Заменяем TDE_ENABLED на True
        env_content = env_content.replace('TDE_ENABLED=False', 'TDE_ENABLED=True')
        
        # Добавляем TDE настройки если их нет
        if 'TDE_MASTER_KEY_FILE' not in env_content:
            env_content += \"\"\"

# TDE Settings (восстановлены)
TDE_ENABLED=True
TDE_MASTER_KEY_FILE=.tde_master_key
TDE_KEY_ROTATION_DAYS=90
TDE_BACKUP_KEYS=True
\"\"\"
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ TDE включен в .env")
    
    # Пробуем инициализировать TDE
    try:
        print("\\n🔄 Инициализация TDE...")
        
        # Устанавливаем переменную окружения
        os.environ['TDE_ENABLED'] = 'True'
        
        # Импортируем TDE модуль
        sys.path.insert(0, '.')
        from src.security.tde import TDEManager
        
        # Создаем TDE менеджер (должен создать новые ключи)
        tde = TDEManager()
        print("✅ TDE менеджер создан успешно")
        
        # Проверяем информацию
        info = tde.get_encryption_info()
        print(f"\\n📊 Информация TDE:")
        print(f"   Алгоритм: {info['algorithm']}")
        print(f"   Главный ключ: {'✅' if info['master_key_exists'] else '❌'}")
        print(f"   Таблиц для шифрования: {len(info['encrypted_tables'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации TDE: {e}")
        print("\\n🔧 Решение: запустите систему БЕЗ TDE")
        print("   TDE_ENABLED=False в .env")
        return False

if __name__ == "__main__":
    safe_tde_setup()
"""
    
    with open('safe_tde_setup.py', 'w', encoding='utf-8') as f:
        f.write(setup_script)
    
    print("✅ Создан скрипт safe_tde_setup.py")

def main():
    """Главная функция исправления"""
    print("🚨 ОБНАРУЖЕНА ПРОБЛЕМА С TDE КЛЮЧОМ")
    print("=" * 50)
    print("Ошибка: файл .tde_master_key поврежден или пуст")
    print("Это происходит когда:")
    print("  1. Файл был создан некорректно")
    print("  2. Система была прервана во время создания ключа")
    print("  3. Файл был поврежден")
    print("")
    
    choice = input("Исправить проблему автоматически? (y/n): ").lower()
    
    if choice != 'y':
        print("🛑 Исправление отменено")
        print("\\nДля ручного исправления:")
        print("1. Удалите файл .tde_master_key")
        print("2. Установите TDE_ENABLED=False в .env")
        print("3. Перезапустите систему")
        return
    
    print("\\n🔄 Начинаем исправление...")
    
    # Исправляем ключ TDE
    fix_tde_key()
    
    # Создаем скрипт для безопасной настройки
    create_fixed_tde_setup()
    
    print("\\n✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 40)
    print("🚀 Следующие шаги:")
    print("\\n1. Запустите систему БЕЗ TDE:")
    print("   python run.py")
    print("\\n2. Если хотите включить TDE:")
    print("   python safe_tde_setup.py")
    print("\\n3. Или используйте систему без шифрования")
    print("   (данные будут храниться в открытом виде)")
    
    print("\\n📝 Что было исправлено:")
    print("  ✅ Удалены поврежденные файлы ключей")
    print("  ✅ TDE отключен в .env")
    print("  ✅ Система может запуститься")
    print("  ✅ Создан скрипт безопасной настройки TDE")
    print("\\n🔒 Безопасность:")
    print("  - TDE отключен временно")
    print("  - Данные в БД не зашифрованы")
    print("  - Поврежденные файлы сохранены как backup")

if __name__ == "__main__":
    main()