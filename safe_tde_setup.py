"""
Безопасная настройка TDE с проверкой ошибок
"""

import os
import sys
import json
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_tde_setup():
    """Безопасная настройка TDE"""
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
            env_content += """

# TDE Settings (восстановлены)
TDE_ENABLED=True
TDE_MASTER_KEY_FILE=.tde_master_key
TDE_KEY_ROTATION_DAYS=90
TDE_BACKUP_KEYS=True
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ TDE включен в .env")
    
    # Пробуем инициализировать TDE
    try:
        print("\n🔄 Инициализация TDE...")
        
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
        print(f"\n📊 Информация TDE:")
        print(f"   Алгоритм: {info['algorithm']}")
        print(f"   Главный ключ: {'✅' if info['master_key_exists'] else '❌'}")
        print(f"   Таблиц для шифрования: {len(info['encrypted_tables'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации TDE: {e}")
        print("\n🔧 Решение: запустите систему БЕЗ TDE")
        print("   TDE_ENABLED=False в .env")
        return False

if __name__ == "__main__":
    safe_tde_setup()
