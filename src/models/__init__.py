"""
Модели данных для системы электронных медицинских карт

Этот модуль содержит все модели данных (dataclasses) для представления
сущностей медицинской системы: пациентов, врачей, приемов и медицинских записей.

Пример использования:
    from src.models import Patient, Doctor, Appointment
    
    patient = Patient(
        first_name="Иван",
        last_name="Иванов", 
        birth_date=date(1990, 1, 15),
        gender="M"
    )
"""

# Импортируем все модели для удобного доступа
from .patient import Patient
from .doctor import Doctor
from .appointment import Appointment
from .medical_record import MedicalRecord, Prescription

# Список всех доступных моделей
__all__ = [
    'Patient',
    'Doctor', 
    'Appointment',
    'MedicalRecord',
    'Prescription'
]

# Версия модулей моделей
__version__ = '1.0.0'

# Метаданные моделей для валидации и документации
MODEL_METADATA = {
    'Patient': {
        'table': 'patients',
        'primary_key': 'id',
        'required_fields': ['first_name', 'last_name', 'birth_date', 'gender'],
        'encrypted_fields': [],  # Пока без TDE
        'description': 'Модель пациента медицинского учреждения'
    },
    'Doctor': {
        'table': 'doctors', 
        'primary_key': 'id',
        'required_fields': ['first_name', 'last_name', 'specialization', 'license_number'],
        'encrypted_fields': [],
        'description': 'Модель врача медицинского учреждения'
    },
    'Appointment': {
        'table': 'appointments',
        'primary_key': 'id', 
        'required_fields': ['patient_id', 'doctor_id', 'appointment_date'],
        'encrypted_fields': [],
        'description': 'Модель записи на прием'
    },
    'MedicalRecord': {
        'table': 'medical_records',
        'primary_key': 'id',
        'required_fields': ['appointment_id'],
        'encrypted_fields': ['diagnosis_encrypted'],  # Зашифрованные поля
        'description': 'Модель медицинской записи с зашифрованным диагнозом'
    },
    'Prescription': {
        'table': 'prescriptions', 
        'primary_key': 'id',
        'required_fields': ['medical_record_id', 'medication_name'],
        'encrypted_fields': [],
        'description': 'Модель назначения лекарственных препаратов'
    }
}

def get_model_info(model_name: str) -> dict:
    """
    Получить метаинформацию о модели
    
    Args:
        model_name: Название модели ('Patient', 'Doctor', etc.)
        
    Returns:
        dict: Словарь с метаданными модели
        
    Example:
        >>> get_model_info('Patient')
        {'table': 'patients', 'primary_key': 'id', ...}
    """
    return MODEL_METADATA.get(model_name, {})

def get_all_models():
    """
    Получить все доступные модели
    
    Returns:
        dict: Словарь {название: класс_модели}
        
    Example:
        >>> models = get_all_models()
        >>> patient_class = models['Patient']
    """
    import sys
    current_module = sys.modules[__name__]
    
    models = {}
    for model_name in __all__:
        models[model_name] = getattr(current_module, model_name)
    
    return models

def validate_required_fields(model_instance, model_name: str) -> list:
    """
    Проверить, что все обязательные поля заполнены
    
    Args:
        model_instance: Экземпляр модели
        model_name: Название модели
        
    Returns:
        list: Список отсутствующих обязательных полей
        
    Example:
        >>> patient = Patient(first_name="Иван")
        >>> errors = validate_required_fields(patient, 'Patient')
        >>> print(errors)  # ['last_name', 'birth_date', 'gender']
    """
    metadata = get_model_info(model_name)
    required_fields = metadata.get('required_fields', [])
    
    missing_fields = []
    for field in required_fields:
        value = getattr(model_instance, field, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)
    
    return missing_fields

# Константы для валидации
GENDER_CHOICES = ['M', 'F']
APPOINTMENT_STATUS_CHOICES = ['scheduled', 'completed', 'cancelled']

# Специализации врачей (для валидации)
DOCTOR_SPECIALIZATIONS = [
    'Терапевт',
    'Кардиолог', 
    'Невролог',
    'Хирург',
    'Педиатр',
    'Гинеколог',
    'Офтальмолог',
    'ЛОР',
    'Дерматолог',
    'Уролог',
    'Эндокринолог',
    'Гастроэнтеролог',
    'Онколог',
    'Психиатр',
    'Травматолог',
    'Стоматолог'
]

def create_sample_data():
    """
    Создать примеры данных для тестирования
    
    Returns:
        dict: Словарь с примерами всех моделей
    """
    from datetime import date, datetime
    
    # Пример пациента
    sample_patient = Patient(
        id=1,
        first_name="Иван",
        last_name="Иванов",
        middle_name="Иванович", 
        birth_date=date(1985, 3, 15),
        gender="M",
        phone="+7 (999) 123-45-67",
        email="ivanov@example.com",
        address="г. Москва, ул. Ленина, д. 1"
    )
    
    # Пример врача  
    sample_doctor = Doctor(
        id=1,
        first_name="Александр",
        last_name="Петров",
        middle_name="Сергеевич",
        specialization="Терапевт",
        license_number="ЛИЦ-2024-0001",
        phone="+7 (999) 765-43-21", 
        email="petrov@clinic.ru"
    )
    
    # Пример приема
    sample_appointment = Appointment(
        id=1,
        patient_id=1,
        doctor_id=1,
        appointment_date=datetime(2024, 6, 30, 10, 0),
        status="scheduled"
    )
    
    # Пример медицинской записи
    sample_medical_record = MedicalRecord(
        id=1,
        appointment_id=1,
        complaints="Головная боль, общая слабость",
        examination_results="Температура 36.8°C, давление 120/80"
    )
    
    # Пример назначения
    sample_prescription = Prescription(
        id=1,
        medical_record_id=1,
        medication_name="Парацетамол",
        dosage="500мг",
        frequency="2 раза в день",
        duration="5 дней"
    )
    
    return {
        'patient': sample_patient,
        'doctor': sample_doctor,
        'appointment': sample_appointment, 
        'medical_record': sample_medical_record,
        'prescription': sample_prescription
    }

# Экспорт утилит валидации
__all__.extend([
    'MODEL_METADATA',
    'get_model_info', 
    'get_all_models',
    'validate_required_fields',
    'GENDER_CHOICES',
    'APPOINTMENT_STATUS_CHOICES', 
    'DOCTOR_SPECIALIZATIONS',
    'create_sample_data'
])