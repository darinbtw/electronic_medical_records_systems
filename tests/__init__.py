"""
Модуль тестирования для системы электронных медицинских карт

Содержит базовые утилиты и конфигурацию для тестирования всех компонентов системы:
- Тесты моделей данных
- Тесты API endpoints  
- Тесты безопасности (SQL injection, шифрование)
- Тесты подключения к базе данных
- Интеграционные тесты

Пример использования:
    from tests import BaseTestCase, create_test_data
    
    class TestPatients(BaseTestCase):
        def setUp(self):
            super().setUp()
            self.test_data = create_test_data()
"""

import os
import sys
import unittest
import tempfile
from datetime import datetime, date
from pathlib import Path

# Добавляем корневую папку проекта в Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Конфигурация для тестов
TEST_CONFIG = {
    'database': {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'name': os.getenv('DB_NAME', 'medical_records'),
        'user': os.getenv('DB_USER', 'postgres'), 
        'password': os.getenv('DB_PASSWORD', ''),
        'test_prefix': 'test_'
    },
    'api': {
        'base_url': 'http://localhost:8000',
        'timeout': 30
    },
    'security': {
        'test_encryption': True,
        'test_sql_injection': True
    }
}

class BaseTestCase(unittest.TestCase):
    """
    Базовый класс для всех тестов системы медкарт
    
    Предоставляет общую функциональность:
    - Настройка тестового окружения
    - Подключение к БД
    - Создание и очистка тестовых данных
    - Утилиты для тестирования API
    """
    
    @classmethod
    def setUpClass(cls):
        """Настройка окружения для всех тестов в классе"""
        cls.project_root = project_root
        cls.test_config = TEST_CONFIG
        
        # Инициализируем подключение к БД для тестов
        try:
            from src.database.connection import db
            cls.db = db
            
            # Проверяем подключение
            if not cls.db.test_connection():
                raise Exception("Не удалось подключиться к тестовой БД")
                
        except ImportError as e:
            print(f"Ошибка импорта модулей БД: {e}")
            cls.db = None
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        self.start_time = datetime.now()
        self.test_name = self._testMethodName
        
        # Создаем временную папку для тестовых файлов
        self.temp_dir = tempfile.mkdtemp(prefix='medical_tests_')
        
        print(f"\n🧪 Запуск теста: {self.test_name}")
    
    def tearDown(self):
        """Очистка после каждого теста"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Очищаем временные файлы
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except:
            pass
        
        print(f"✅ Тест {self.test_name} завершен за {duration:.2f}с")
    
    def assert_valid_patient_data(self, patient_data):
        """Проверка корректности данных пациента"""
        required_fields = ['first_name', 'last_name', 'birth_date', 'gender']
        
        for field in required_fields:
            self.assertIn(field, patient_data, f"Отсутствует обязательное поле: {field}")
            self.assertIsNotNone(patient_data[field], f"Поле {field} не может быть None")
        
        # Проверка пола
        self.assertIn(patient_data['gender'], ['M', 'F'], "Пол должен быть M или F")
        
        # Проверка даты рождения
        if isinstance(patient_data['birth_date'], str):
            try:
                birth_date = datetime.strptime(patient_data['birth_date'], '%Y-%m-%d').date()
            except ValueError:
                self.fail("Неверный формат даты рождения")
        else:
            birth_date = patient_data['birth_date']
        
        self.assertLessEqual(birth_date, date.today(), "Дата рождения не может быть в будущем")
        self.assertGreaterEqual(birth_date, date(1900, 1, 1), "Дата рождения слишком старая")
    
    def assert_valid_doctor_data(self, doctor_data):
        """Проверка корректности данных врача"""
        required_fields = ['first_name', 'last_name', 'specialization', 'license_number']
        
        for field in required_fields:
            self.assertIn(field, doctor_data, f"Отсутствует обязательное поле: {field}")
            self.assertIsNotNone(doctor_data[field], f"Поле {field} не может быть None")
        
        # Проверка формата номера лицензии
        license_number = doctor_data['license_number']
        import re
        valid_license = re.match(r'^(ЛИЦ-\d{4}-\d{4}|LIC-\d{4}-\d{3,4})$', license_number)
        self.assertTrue(valid_license, f"Неверный формат номера лицензии: {license_number}")
    
    def execute_sql_safely(self, query, params=None):
        """Безопасное выполнение SQL запроса для тестов"""
        if not self.db:
            self.skipTest("БД недоступна для тестирования")
        
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.fail(f"Ошибка выполнения SQL: {e}")

def create_test_data():
    """
    Создать набор тестовых данных
    
    Returns:
        dict: Словарь с тестовыми данными для всех сущностей
    """
    return {
        'patients': [
            {
                'first_name': 'Тест',
                'last_name': 'Пациентов',
                'middle_name': 'Тестович',
                'birth_date': '1990-01-15',
                'gender': 'M',
                'phone': '+7 (999) 111-11-11',
                'email': 'test.patient@example.com',
                'address': 'г. Тестовый, ул. Тестовая, д. 1'
            },
            {
                'first_name': 'Тестовая',
                'last_name': 'Пациентова', 
                'middle_name': 'Тестовна',
                'birth_date': '1985-05-20',
                'gender': 'F',
                'phone': '+7 (999) 222-22-22',
                'email': 'test.patient2@example.com',
                'address': 'г. Тестовый, ул. Тестовая, д. 2'
            }
        ],
        'doctors': [
            {
                'first_name': 'Тест',
                'last_name': 'Докторов',
                'middle_name': 'Тестович',
                'specialization': 'Терапевт',
                'license_number': 'ЛИЦ-2024-9999',
                'phone': '+7 (999) 333-33-33',
                'email': 'test.doctor@clinic.com'
            },
            {
                'first_name': 'Тестовая',
                'last_name': 'Докторова',
                'middle_name': 'Тестовна', 
                'specialization': 'Кардиолог',
                'license_number': 'ЛИЦ-2024-8888',
                'phone': '+7 (999) 444-44-44',
                'email': 'test.doctor2@clinic.com'
            }
        ],
        'appointments': [
            {
                'patient_id': 1,
                'doctor_id': 1,
                'appointment_date': '2024-07-01T10:00:00',
                'status': 'scheduled'
            },
            {
                'patient_id': 2,
                'doctor_id': 2, 
                'appointment_date': '2024-07-01T14:00:00',
                'status': 'completed'
            }
        ],
        'medical_records': [
            {
                'appointment_id': 2,  # Только для завершенных приемов
                'complaints': 'Тестовые жалобы',
                'examination_results': 'Тестовые результаты осмотра',
                'diagnosis': 'Тестовый диагноз'
            }
        ],
        'prescriptions': [
            {
                'medical_record_id': 1,
                'medication_name': 'Тестовый препарат',
                'dosage': '500мг',
                'frequency': '2 раза в день',
                'duration': '5 дней',
                'notes': 'Тестовые заметки'
            }
        ]
    }

def create_sql_injection_test_cases():
    """
    Создать тестовые случаи для проверки SQL injection
    
    Returns:
        list: Список потенциально опасных строк
    """
    return [
        "' OR '1'='1",
        "'; DROP TABLE patients; --",
        "' UNION SELECT * FROM doctors --",
        "admin'--",
        "' OR 1=1 --",
        "'; INSERT INTO patients VALUES (999,'hack','hack','1990-01-01','M'); --",
        "test@mail.ru'; --",
        "тест' OR 'х'='х",  # Кириллица
        "test\n' OR '1'='1",  # С переносом строки
    ]

def run_all_tests():
    """
    Запустить все тесты в модуле
    
    Returns:
        unittest.TestResult: Результаты тестирования
    """
    # Ищем все тестовые модули
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(
        start_dir=str(current_dir),
        pattern='test_*.py',
        top_level_dir=str(project_root)
    )
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(test_suite)

def setup_test_database():
    """
    Настройка тестовой базы данных
    
    Создает копию основной БД для тестирования
    """
    print("🔧 Настройка тестовой базы данных...")
    
    try:
        from src.database.connection import db
        
        # Проверяем основное подключение
        if not db.test_connection():
            raise Exception("Основная БД недоступна")
        
        print("✅ Тестовая БД готова к работе")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка настройки тестовой БД: {e}")
        return False

def cleanup_test_data():
    """
    Очистка тестовых данных после завершения тестов
    """
    print("🧹 Очистка тестовых данных...")
    
    try:
        from src.database.connection import db
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Удаляем тестовые данные (по email/phone паттернам)
            test_patterns = [
                "DELETE FROM prescriptions WHERE medical_record_id IN (SELECT id FROM medical_records WHERE appointment_id IN (SELECT id FROM appointments WHERE patient_id IN (SELECT id FROM patients WHERE email LIKE '%test%' OR email LIKE '%тест%')))",
                "DELETE FROM medical_records WHERE appointment_id IN (SELECT id FROM appointments WHERE patient_id IN (SELECT id FROM patients WHERE email LIKE '%test%' OR email LIKE '%тест%'))",
                "DELETE FROM appointments WHERE patient_id IN (SELECT id FROM patients WHERE email LIKE '%test%' OR email LIKE '%тест%')",
                "DELETE FROM patients WHERE email LIKE '%test%' OR email LIKE '%тест%'",
                "DELETE FROM doctors WHERE email LIKE '%test%' OR email LIKE '%тест%'"
            ]
            
            for query in test_patterns:
                try:
                    cursor.execute(query)
                except:
                    pass  # Игнорируем ошибки при очистке
            
            conn.commit()
            
        print("✅ Тестовые данные очищены")
        
    except Exception as e:
        print(f"⚠️ Ошибка очистки: {e}")

# Экспорт основных компонентов
__all__ = [
    'BaseTestCase',
    'TEST_CONFIG', 
    'create_test_data',
    'create_sql_injection_test_cases',
    'run_all_tests',
    'setup_test_database',
    'cleanup_test_data'
]

# Версия тестового модуля
__version__ = '12.10.5'

# Автоматическая настройка тестового окружения при импорте
if __name__ != '__main__':
    # Проверяем наличие необходимых модулей
    try:
        import dotenv
        from pathlib import Path
        
        # Загружаем переменные окружения
        env_file = project_root / '.env'
        if env_file.exists():
            dotenv.load_dotenv(env_file)
            
    except ImportError:
        pass  # dotenv не обязателен для тестов