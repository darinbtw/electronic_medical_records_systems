import os
import sys
from pathlib import Path

# Добавляем корневую папку в path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_sql_file(filepath):
    """Загрузка и выполнение SQL файла"""
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Разбиваем на отдельные команды
    # Удаляем комментарии и пустые строки
    commands = []
    current_command = []
    
    for line in sql_content.split('\n'):
        # Пропускаем комментарии
        if line.strip().startswith('--') or not line.strip():
            continue
            
        current_command.append(line)
        
        # Если строка заканчивается на ;, это конец команды
        if line.strip().endswith(';'):
            commands.append('\n'.join(current_command))
            current_command = []
    
    return commands

def load_test_data():
    """Загрузка тестовых данных"""
    sql_file = 'src/sql_test_query/basic_test_data.sql'
    
    if not os.path.exists(sql_file):
        logger.error(f"Файл {sql_file} не найден!")
        return False
    
    try:
        logger.info("Загрузка тестовых данных...")
        
        # Читаем SQL файл
        commands = load_sql_file(sql_file)
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            executed = 0
            for command in commands:
                if command.strip():
                    try:
                        cursor.execute(command)
                        executed += 1
                    except Exception as e:
                        # Игнорируем ошибки дубликатов
                        if "duplicate key" not in str(e):
                            logger.warning(f"Ошибка выполнения: {e}")
            
            conn.commit()
            logger.info(f"Выполнено {executed} команд")
        
        # Проверяем результат
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM patients")
            patient_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM doctors")
            doctor_count = cursor.fetchone()['count']
            
            logger.info(f"✅ Загружено: {patient_count} пациентов, {doctor_count} врачей")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        return False

if __name__ == "__main__":
    success = load_test_data()
    sys.exit(0 if success else 1)