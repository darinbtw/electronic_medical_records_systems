from flask import Flask, request, jsonify, send_file
from datetime import datetime
import os
import sys
import logging

# Добавляем путь к корню проекта
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from src.database.connection import db
from src.config import config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# Включаем CORS для работы с frontend
from flask_cors import CORS
CORS(app)

# Проверяем статус TDE
TDE_ENABLED = os.getenv('TDE_ENABLED', 'False').lower() == 'true'

if TDE_ENABLED:
    try:
        from src.security.tde import TDEManager
        tde_manager = TDEManager()
        logger.info("🔒 TDE включен и готов к работе")
    except Exception as e:
        logger.warning(f"⚠️ TDE не удалось инициализировать: {e}")
        logger.info("📖 Работаем без TDE")
        TDE_ENABLED = False
        tde_manager = None
else:
    logger.info("📖 TDE отключен в настройках")
    tde_manager = None

def safe_encrypt_field(table_name, field_name, value):
    """Безопасное шифрование поля с обработкой пустых значений"""
    if not TDE_ENABLED or not tde_manager:
        return None, None
    
    # Если значение пустое или None, не шифруем
    if not value or str(value).strip() == '':
        return None, None
    
    try:
        return tde_manager.encrypt_field(table_name, field_name, str(value))
    except Exception as e:
        logger.error(f"Ошибка шифрования {table_name}.{field_name}: {e}")
        # Возвращаем None вместо исключения, чтобы не сломать создание записи
        return None, None

def safe_decrypt_field(table_name, field_name, ciphertext, iv):
    """Безопасная расшифровка поля с обработкой ошибок"""
    if not TDE_ENABLED or not tde_manager or not ciphertext or not iv:
        return None
    
    try:
        return tde_manager.decrypt_field(table_name, field_name, ciphertext, iv)
    except Exception as e:
        logger.error(f"Ошибка расшифровки {table_name}.{field_name}: {e}")
        return f"[ОШИБКА РАСШИФРОВКИ]"

def format_patient_data(patient):
    """Форматирование данных пациента для русского интерфейса"""
    if not patient:
        return patient
    
    formatted = dict(patient)
    
    # Форматируем дату рождения
    if 'birth_date' in formatted and formatted['birth_date']:
        try:
            birth_date = formatted['birth_date']
            
            if isinstance(birth_date, str):
                try:
                    if '.' in birth_date:
                        pass  # Уже в русском формате
                    elif '-' in birth_date:
                        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                        formatted['birth_date'] = birth_date.strftime('%d.%m.%Y')
                    else:
                        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                        formatted['birth_date'] = birth_date.strftime('%d.%m.%Y')
                except ValueError:
                    logger.warning(f"Could not parse birth_date: {birth_date}")
                    pass
            elif hasattr(birth_date, 'strftime'):
                formatted['birth_date'] = birth_date.strftime('%d.%m.%Y')
        except Exception as e:
            logger.error(f"Error formatting birth_date: {e}")
            pass
    
    # Расшифровываем и форматируем телефон
    if TDE_ENABLED and 'phone_encrypted' in formatted and 'phone_iv' in formatted:
        decrypted_phone = safe_decrypt_field('patients', 'phone', 
                                           formatted.get('phone_encrypted'), 
                                           formatted.get('phone_iv'))
        if decrypted_phone and decrypted_phone != "[ОШИБКА РАСШИФРОВКИ]":
            formatted['phone'] = decrypted_phone
        else:
            formatted['phone'] = "не указан"
        
        # Удаляем зашифрованные поля из вывода
        formatted.pop('phone_encrypted', None)
        formatted.pop('phone_iv', None)
    
    # Форматируем телефон
    if 'phone' in formatted:
        phone = formatted['phone']
        if phone and phone != "не указан" and not phone.startswith("[ОШИБКА"):
            digits = ''.join(filter(str.isdigit, phone))
            if len(digits) == 11 and digits.startswith('7'):
                formatted['phone'] = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
            elif len(digits) == 11 and digits.startswith('8'):
                formatted['phone'] = f"8 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        else:
            formatted['phone'] = "не указан"
    
    # Расшифровываем и форматируем email
    if TDE_ENABLED and 'email_encrypted' in formatted and 'email_iv' in formatted:
        decrypted_email = safe_decrypt_field('patients', 'email', 
                                           formatted.get('email_encrypted'), 
                                           formatted.get('email_iv'))
        if decrypted_email and decrypted_email != "[ОШИБКА РАСШИФРОВКИ]":
            formatted['email'] = decrypted_email
        else:
            formatted['email'] = "не указан"
        
        # Удаляем зашифрованные поля из вывода
        formatted.pop('email_encrypted', None)
        formatted.pop('email_iv', None)
    
    # Форматируем email
    if 'email' in formatted:
        if not formatted['email'] or formatted['email'].startswith("[ОШИБКА"):
            formatted['email'] = "не указан"
    
    # Расшифровываем и форматируем адрес
    if TDE_ENABLED and 'address_encrypted' in formatted and 'address_iv' in formatted:
        decrypted_address = safe_decrypt_field('patients', 'address', 
                                             formatted.get('address_encrypted'), 
                                             formatted.get('address_iv'))
        if decrypted_address and decrypted_address != "[ОШИБКА РАСШИФРОВКИ]":
            formatted['address'] = decrypted_address
        else:
            formatted['address'] = "не указан"
        
        # Удаляем зашифрованные поля из вывода
        formatted.pop('address_encrypted', None)
        formatted.pop('address_iv', None)
    
    # Форматируем пол
    if 'gender' in formatted:
        gender_map = {'M': 'Мужской', 'F': 'Женский'}
        formatted['gender'] = gender_map.get(formatted['gender'], formatted['gender'] or 'не указан')
    
    return formatted

def format_datetime_russian(dt):
    """Форматирование даты/времени в русском формате"""
    if not dt:
        return "не указано"
    
    try:
        if isinstance(dt, str):
            if '.' in dt and ':' in dt:
                return dt
            
            if 'T' in dt:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(dt)
        
        return dt.strftime('%d.%m.%Y %H:%M')
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return str(dt) if dt else "не указано"

# === ГЛАВНАЯ СТРАНИЦА ===
@app.route('/')
def index():
    """Главная страница - возвращает веб-интерфейс"""
    web_interface_path = os.path.join(project_root, 'web_interface.html')
    if os.path.exists(web_interface_path):
        return send_file(web_interface_path)
    else:
        return jsonify({
            'message': 'Система электронных медкарт API',
            'error': 'web_interface.html не найден',
            'path': web_interface_path
        })

@app.route('/api')
def api_info():
    """Документация API"""
    return jsonify({
        'title': '🏥 Система медкарт - API',
        'version': '12.10.5',
        'url': 'http://localhost:8000',
        'tde_enabled': TDE_ENABLED,
        'status': 'Готов к работе',
        
        'endpoints': {
            'GET /': 'Главная страница (веб-интерфейс)',
            'GET /api': 'Эта страница с документацией',
            'GET /health': 'Проверка работы системы',
            'GET /api/patients': 'Список пациентов',
            'POST /api/patients': 'Добавить пациента',
            'GET /api/search?q=Иванов': 'Поиск пациентов',
            'GET /api/appointments': 'Список приёмов',
            'POST /api/appointments': 'Создать приём',
            'GET /api/medical-records': 'Список медкарт',
            'POST /api/medical-records': 'Создать медкарту',
            'GET /api/statistics': 'Статистика системы'
        }
    })

@app.route('/health')
def health():
    """Проверка состояния системы"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as patients FROM patients")
            patients_count = cursor.fetchone()['patients']
            
            cursor.execute("SELECT COUNT(*) as doctors FROM doctors")
            doctors_count = cursor.fetchone()['doctors']
            
        return jsonify({
            'status': 'OK',
            'database': 'OK',
            'tde': 'Enabled' if TDE_ENABLED else 'Disabled',
            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            'details': {
                'patients_count': patients_count,
                'doctors_count': doctors_count
            }
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'ERROR',
            'database': 'ERROR',
            'tde': 'Unknown',
            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            'details': {'error': str(e)}
        }), 500

# === ПАЦИЕНТЫ ===
@app.route('/api/patients', methods=['GET'])
def get_patients():
    """Получить список пациентов"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM patients")
            total = cursor.fetchone()['total']
            
            # Выбираем все поля включая зашифрованные
            if TDE_ENABLED:
                cursor.execute("""
                    SELECT id, first_name, last_name, middle_name, 
                           birth_date, gender, phone, email, address,
                           phone_encrypted, phone_iv, 
                           email_encrypted, email_iv,
                           address_encrypted, address_iv
                    FROM patients
                    ORDER BY last_name, first_name
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
            else:
                cursor.execute("""
                    SELECT id, first_name, last_name, middle_name, 
                           birth_date, gender, phone, email, address
                    FROM patients
                    ORDER BY last_name, first_name
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
            
            patients = cursor.fetchall()
            formatted_patients = [format_patient_data(patient) for patient in patients]
            
            return jsonify({
                'patients': formatted_patients,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })
    except Exception as e:
        logger.error(f"Get patients error: {e}")
        return jsonify({'error': f'Ошибка получения пациентов: {str(e)}'}), 500

@app.route('/api/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Получить данные пациента по ID"""
    try:
        with db.get_cursor() as cursor:
            if TDE_ENABLED:
                cursor.execute("""
                    SELECT p.*, 
                           COUNT(DISTINCT a.id) as total_appointments,
                           MAX(a.appointment_date) as last_appointment
                    FROM patients p
                    LEFT JOIN appointments a ON p.id = a.patient_id
                    WHERE p.id = %s
                    GROUP BY p.id
                """, (patient_id,))
            else:
                cursor.execute("""
                    SELECT p.*, 
                           COUNT(DISTINCT a.id) as total_appointments,
                           MAX(a.appointment_date) as last_appointment
                    FROM patients p
                    LEFT JOIN appointments a ON p.id = a.patient_id
                    WHERE p.id = %s
                    GROUP BY p.id
                """, (patient_id,))
            
            patient = cursor.fetchone()
            
            if not patient:
                return jsonify({'error': 'Пациент не найден'}), 404
            
            formatted_patient = format_patient_data(patient)
            
            if formatted_patient['last_appointment']:
                formatted_patient['last_appointment'] = format_datetime_russian(
                    formatted_patient['last_appointment']
                )
            else:
                formatted_patient['last_appointment'] = "нет"
                
            return jsonify(formatted_patient)
    except Exception as e:
        logger.error(f"Get patient error: {e}")
        return jsonify({'error': f'Ошибка получения пациента: {str(e)}'}), 500

@app.route('/api/patients', methods=['POST'])
def create_patient():
    """Создать нового пациента с поддержкой TDE"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные'}), 400
        
        required = ['first_name', 'last_name', 'birth_date', 'gender']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'error': f'Отсутствует обязательное поле: {field}'}), 400
        
        clean_data = {}
        for key, value in data.items():
            if value is not None and str(value).strip():
                clean_data[key] = str(value).strip()
        
        if 'phone' in clean_data and clean_data['phone']:
            phone = clean_data['phone']
            digits = ''.join(filter(str.isdigit, phone))
            if len(digits) < 10:
                return jsonify({'error': 'Неверный формат телефона'}), 400
            
            if len(digits) == 11 and digits.startswith('8'):
                digits = '7' + digits[1:]
            if len(digits) == 10:
                digits = '7' + digits
                
            clean_data['phone'] = f"+{digits}"
        
        logger.info(f"Creating patient with data: {clean_data}")
        
        with db.get_cursor() as cursor:
            # Подготавливаем данные для вставки
            insert_data = {
                'first_name': clean_data.get('first_name'),
                'last_name': clean_data.get('last_name'),
                'middle_name': clean_data.get('middle_name'),
                'birth_date': clean_data.get('birth_date'),
                'gender': clean_data.get('gender')
            }
            
            # Обрабатываем поля с TDE шифрованием
            if TDE_ENABLED:
                # Шифруем телефон
                if clean_data.get('phone'):
                    phone_encrypted, phone_iv = safe_encrypt_field('patients', 'phone', clean_data['phone'])
                    insert_data['phone_encrypted'] = phone_encrypted
                    insert_data['phone_iv'] = phone_iv
                    # НЕ сохраняем открытый телефон если TDE включен
                else:
                    insert_data['phone_encrypted'] = None
                    insert_data['phone_iv'] = None
                
                # Шифруем email
                if clean_data.get('email'):
                    email_encrypted, email_iv = safe_encrypt_field('patients', 'email', clean_data['email'])
                    insert_data['email_encrypted'] = email_encrypted
                    insert_data['email_iv'] = email_iv
                else:
                    insert_data['email_encrypted'] = None
                    insert_data['email_iv'] = None
                
                # Шифруем адрес
                if clean_data.get('address'):
                    address_encrypted, address_iv = safe_encrypt_field('patients', 'address', clean_data['address'])
                    insert_data['address_encrypted'] = address_encrypted
                    insert_data['address_iv'] = address_iv
                else:
                    insert_data['address_encrypted'] = None
                    insert_data['address_iv'] = None
                
                # SQL для вставки с TDE полями
                cursor.execute("""
                    INSERT INTO patients 
                    (first_name, last_name, middle_name, birth_date, gender, 
                     phone_encrypted, phone_iv, email_encrypted, email_iv, 
                     address_encrypted, address_iv)
                    VALUES (%(first_name)s, %(last_name)s, %(middle_name)s, 
                            %(birth_date)s, %(gender)s, %(phone_encrypted)s, %(phone_iv)s,
                            %(email_encrypted)s, %(email_iv)s, %(address_encrypted)s, %(address_iv)s)
                    RETURNING id, created_at
                """, insert_data)
            else:
                # Без TDE - обычная вставка
                insert_data.update({
                    'phone': clean_data.get('phone'),
                    'email': clean_data.get('email'),
                    'address': clean_data.get('address')
                })
                
                cursor.execute("""
                    INSERT INTO patients 
                    (first_name, last_name, middle_name, birth_date, 
                     gender, phone, email, address)
                    VALUES (%(first_name)s, %(last_name)s, %(middle_name)s, 
                            %(birth_date)s, %(gender)s, %(phone)s, %(email)s, %(address)s)
                    RETURNING id, created_at
                """, insert_data)
            
            result = cursor.fetchone()
            
            logger.info(f"Patient created successfully with ID: {result['id']}")
            
            return jsonify({
                'id': result['id'],
                'created_at': format_datetime_russian(result['created_at']),
                'message': 'Пациент успешно добавлен'
            }), 201
            
    except Exception as e:
        logger.error(f"Create patient error: {e}", exc_info=True)
        return jsonify({'error': f'Ошибка создания пациента: {str(e)}'}), 500

# === ПОИСК ===
@app.route('/api/search')
def search():
    """Универсальный поиск с поддержкой TDE"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'patients')
    
    try:
        if search_type == 'doctors':
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, first_name, last_name, middle_name, 
                           specialization, phone, email
                    FROM doctors
                    ORDER BY last_name, first_name
                """)
                doctors = cursor.fetchall()
                
                formatted_doctors = []
                for doctor in doctors:
                    formatted = dict(doctor)
                    if formatted['phone']:
                        digits = ''.join(filter(str.isdigit, formatted['phone']))
                        if len(digits) == 11:
                            formatted['phone'] = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
                    else:
                        formatted['phone'] = "не указан"
                    
                    if not formatted['email']:
                        formatted['email'] = "не указан"
                    
                    formatted_doctors.append(formatted)
                
                return jsonify({'doctors': formatted_doctors})
        
        if len(query) < 2:
            return jsonify({'error': 'Запрос слишком короткий', 'patients': []}), 200
        
        with db.get_cursor() as cursor:
            if TDE_ENABLED:
                # При TDE поиск только по незашифрованным полям
                cursor.execute("""
                    SELECT id, first_name, last_name, middle_name, 
                           birth_date, gender, phone, email, address,
                           phone_encrypted, phone_iv, 
                           email_encrypted, email_iv,
                           address_encrypted, address_iv
                    FROM patients
                    WHERE last_name ILIKE %s 
                       OR first_name ILIKE %s 
                       OR middle_name ILIKE %s
                    ORDER BY last_name, first_name
                    LIMIT 50
                """, (f'%{query}%', f'%{query}%', f'%{query}%'))
            else:
                cursor.execute("""
                    SELECT id, first_name, last_name, middle_name, 
                           birth_date, gender, phone, email
                    FROM patients
                    WHERE last_name ILIKE %s 
                       OR first_name ILIKE %s 
                       OR middle_name ILIKE %s
                       OR phone LIKE %s
                    ORDER BY last_name, first_name
                    LIMIT 50
                """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
            
            patients = cursor.fetchall()
            formatted_patients = [format_patient_data(patient) for patient in patients]
            
        return jsonify({
            'patients': formatted_patients,
            'count': len(formatted_patients),
            'query': query
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': f'Ошибка поиска: {str(e)}'}), 500

# === ПРИЁМЫ ===
@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    """Получить список приёмов"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    status_filter = request.args.get('status', '')
    offset = (page - 1) * per_page
    
    try:
        with db.get_cursor() as cursor:
            where_clause = ""
            params = []
            
            if status_filter:
                where_clause = "WHERE a.status = %s"
                params.append(status_filter)
            
            count_query = f"""
                SELECT COUNT(*) as total 
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                {where_clause}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            main_query = f"""
                SELECT a.*, 
                       p.first_name || ' ' || p.last_name as patient_name,
                       d.first_name || ' ' || d.last_name as doctor_name,
                       d.specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                {where_clause}
                ORDER BY a.appointment_date DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(main_query, params + [per_page, offset])
            appointments = cursor.fetchall()
            
            formatted_appointments = []
            for appointment in appointments:
                formatted = dict(appointment)
                
                formatted['appointment_date'] = format_datetime_russian(
                    formatted['appointment_date']
                )
                
                status_map = {
                    'scheduled': 'запланирован',
                    'completed': 'завершен', 
                    'cancelled': 'отменен'
                }
                formatted['status'] = status_map.get(
                    formatted['status'], formatted['status']
                )
                
                formatted_appointments.append(formatted)
            
            return jsonify({
                'appointments': formatted_appointments,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page if total > 0 else 1
                }
            })
            
    except Exception as e:
        logger.error(f"Get appointments error: {e}")
        return jsonify({'error': f'Ошибка получения приёмов: {str(e)}'}), 500

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    """Создать новый приём"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные'}), 400
        
        required = ['patient_id', 'doctor_id', 'appointment_date']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Отсутствует поле: {field}'}), 400
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO appointments 
                (patient_id, doctor_id, appointment_date, status)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
            """, (
                data['patient_id'],
                data['doctor_id'],
                data['appointment_date'],
                data.get('status', 'scheduled')
            ))
            
            result = cursor.fetchone()
            
            return jsonify({
                'id': result['id'],
                'created_at': format_datetime_russian(result['created_at']),
                'message': 'Приём успешно создан'
            }), 201
            
    except Exception as e:
        logger.error(f"Create appointment error: {e}")
        return jsonify({'error': f'Ошибка создания приёма: {str(e)}'}), 500

@app.route('/api/appointments-without-records', methods=['GET'])
def get_appointments_without_records():
    """Получить завершённые приёмы без медицинских записей"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT a.*, 
                       p.first_name || ' ' || p.last_name as patient_name,
                       d.first_name || ' ' || d.last_name as doctor_name,
                       d.specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                LEFT JOIN medical_records mr ON a.id = mr.appointment_id
                WHERE a.status = 'completed' 
                AND mr.id IS NULL
                ORDER BY a.appointment_date DESC
                LIMIT 100
            """)
            
            appointments = cursor.fetchall()
            
            formatted_appointments = []
            for appointment in appointments:
                formatted = dict(appointment)
                formatted['appointment_date'] = format_datetime_russian(
                    formatted['appointment_date']
                )
                formatted_appointments.append(formatted)
            
            return jsonify({
                'appointments': formatted_appointments,
                'count': len(formatted_appointments)
            })
            
    except Exception as e:
        logger.error(f"Get appointments without records error: {e}")
        return jsonify({'error': f'Ошибка получения приёмов: {str(e)}'}), 500

# === МЕДИЦИНСКИЕ ЗАПИСИ ===
@app.route('/api/medical-records', methods=['GET'])
def get_medical_records():
    """Получить список медицинских записей"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as total FROM medical_records")
            total = cursor.fetchone()['total']
            
            cursor.execute("""
                SELECT mr.*, 
                       a.appointment_date,
                       p.first_name || ' ' || p.last_name as patient_name,
                       d.first_name || ' ' || d.last_name as doctor_name
                FROM medical_records mr
                JOIN appointments a ON mr.appointment_id = a.id
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                ORDER BY mr.created_at DESC
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            
            records = cursor.fetchall()
            
            formatted_records = []
            for record in records:
                formatted = dict(record)
                
                formatted['appointment_date'] = format_datetime_russian(
                    formatted['appointment_date']
                )
                
                # Расшифровываем диагноз если он зашифрован
                if TDE_ENABLED and formatted.get('diagnosis_encrypted') and formatted.get('diagnosis_iv'):
                    decrypted_diagnosis = safe_decrypt_field('medical_records', 'diagnosis', 
                                                          formatted['diagnosis_encrypted'], 
                                                          formatted['diagnosis_iv'])
                    if decrypted_diagnosis and decrypted_diagnosis != "[ОШИБКА РАСШИФРОВКИ]":
                        formatted['diagnosis'] = decrypted_diagnosis
                    else:
                        formatted['diagnosis'] = "Ошибка расшифровки диагноза"
                
                # Удаляем зашифрованные поля из вывода
                if 'diagnosis_encrypted' in formatted:
                    del formatted['diagnosis_encrypted']
                if 'diagnosis_iv' in formatted:
                    del formatted['diagnosis_iv']
                
                formatted_records.append(formatted)
            
            return jsonify({
                'records': formatted_records,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page if total > 0 else 1
                }
            })
            
    except Exception as e:
        logger.error(f"Get medical records error: {e}")
        return jsonify({'error': f'Ошибка получения медкарт: {str(e)}'}), 500

@app.route('/api/medical-records/<int:record_id>', methods=['GET'])
def get_medical_record_with_decryption(record_id):
    """Получить медицинскую запись с расшифровкой диагноза"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT mr.*, a.appointment_date,
                       p.first_name || ' ' || p.last_name as patient_name,
                       d.first_name || ' ' || d.last_name as doctor_name
                FROM medical_records mr
                JOIN appointments a ON mr.appointment_id = a.id
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE mr.id = %s
            """, (record_id,))
            
            record = cursor.fetchone()
            
            if not record:
                return jsonify({'error': 'Медицинская запись не найдена'}), 404
            
            formatted_record = dict(record)
            
            # Расшифровываем диагноз
            if record['diagnosis_encrypted'] and record['diagnosis_iv']:
                try:
                    decrypted = safe_decrypt_field('medical_records', 'diagnosis',
                                                 bytes(record['diagnosis_encrypted']),
                                                 bytes(record['diagnosis_iv']))
                    formatted_record['diagnosis'] = decrypted or "Ошибка расшифровки"
                except Exception as e:
                    logger.error(f"Decryption error: {e}")
                    formatted_record['diagnosis'] = f"Ошибка расшифровки: {e}"
            else:
                formatted_record['diagnosis'] = "Диагноз не зашифрован"
            
            if 'diagnosis_encrypted' in formatted_record:
                del formatted_record['diagnosis_encrypted']
            if 'diagnosis_iv' in formatted_record:
                del formatted_record['diagnosis_iv']
            
            formatted_record['appointment_date'] = format_datetime_russian(
                formatted_record['appointment_date']
            )
            
            cursor.execute("""
                SELECT * FROM prescriptions 
                WHERE medical_record_id = %s
                ORDER BY id
            """, (record_id,))
            
            formatted_record['prescriptions'] = cursor.fetchall()
            
            return jsonify(formatted_record)
            
    except Exception as e:
        logger.error(f"Get medical record error: {e}")
        return jsonify({'error': f'Ошибка получения медкарты: {str(e)}'}), 500

@app.route('/api/medical-records', methods=['POST'])
def create_medical_record():
    """Создать медицинскую запись с шифрованным диагнозом"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Отсутствуют данные'}), 400
        
        required = ['appointment_id', 'diagnosis']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Отсутствует поле: {field}'}), 400
        
        diagnosis_encrypted = None
        diagnosis_iv = None
        
        if TDE_ENABLED and tde_manager:
            try:
                diagnosis_encrypted, diagnosis_iv = safe_encrypt_field('medical_records', 'diagnosis', data['diagnosis'])
                logger.info("Диагноз зашифрован с TDE")
            except Exception as e:
                logger.error(f"Ошибка шифрования диагноза: {e}")
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, status FROM appointments 
                WHERE id = %s
            """, (data['appointment_id'],))
            
            appointment = cursor.fetchone()
            if not appointment:
                return jsonify({'error': 'Приём не найден'}), 400
            
            cursor.execute("""
                SELECT id FROM medical_records 
                WHERE appointment_id = %s
            """, (data['appointment_id'],))
            
            existing_record = cursor.fetchone()
            if existing_record:
                return jsonify({'error': 'Медицинская запись для этого приёма уже существует'}), 400
            
            cursor.execute("""
                UPDATE appointments 
                SET status = 'completed' 
                WHERE id = %s
            """, (data['appointment_id'],))
            
            if TDE_ENABLED:
                # Вставка с зашифрованным диагнозом
                cursor.execute("""
                    INSERT INTO medical_records 
                    (appointment_id, diagnosis_encrypted, diagnosis_iv, 
                     complaints, examination_results)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, created_at
                """, (
                    data['appointment_id'],
                    diagnosis_encrypted,
                    diagnosis_iv,
                    data.get('complaints'),
                    data.get('examination_results')
                ))
            else:
                # Вставка без шифрования
                cursor.execute("""
                    INSERT INTO medical_records 
                    (appointment_id, complaints, examination_results)
                    VALUES (%s, %s, %s)
                    RETURNING id, created_at
                """, (
                    data['appointment_id'],
                    data.get('complaints'),
                    data.get('examination_results')
                ))
            
            result = cursor.fetchone()
            record_id = result['id']
            
            if 'prescriptions' in data and data['prescriptions']:
                for prescription in data['prescriptions']:
                    if prescription.get('medication_name'):
                        cursor.execute("""
                            INSERT INTO prescriptions 
                            (medical_record_id, medication_name, dosage, 
                             frequency, duration, notes)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            record_id,
                            prescription['medication_name'],
                            prescription.get('dosage'),
                            prescription.get('frequency'),
                            prescription.get('duration'),
                            prescription.get('notes')
                        ))
            
            return jsonify({
                'id': record_id,
                'created_at': format_datetime_russian(result['created_at']),
                'message': 'Медицинская запись успешно создана'
            }), 201
            
    except Exception as e:
        logger.error(f"Create medical record error: {e}")
        return jsonify({'error': f'Ошибка создания медкарты: {str(e)}'}), 500

# === СТАТИСТИКА ===
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Получить статистику системы"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM patients) as total_patients,
                    (SELECT COUNT(*) FROM doctors) as total_doctors,
                    (SELECT COUNT(*) FROM appointments) as total_appointments,
                    (SELECT COUNT(*) FROM appointments WHERE status = 'scheduled') as scheduled_appointments,
                    (SELECT COUNT(*) FROM medical_records) as total_records
            """)
            general_stats = cursor.fetchone()
            
            cursor.execute("""
                SELECT d.id, d.first_name, d.last_name, d.specialization,
                       COUNT(a.id) as appointment_count
                FROM doctors d
                LEFT JOIN appointments a ON d.id = a.doctor_id
                GROUP BY d.id, d.first_name, d.last_name, d.specialization
                ORDER BY appointment_count DESC
            """)
            doctors_stats = cursor.fetchall()
            
            return jsonify({
                'general': dict(general_stats),
                'doctors': [dict(doc) for doc in doctors_stats]
            })
            
    except Exception as e:
        logger.error(f"Get statistics error: {e}")
        return jsonify({'error': f'Ошибка получения статистики: {str(e)}'}), 500

# === ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ===

def clear_quick_search():
    """Очистка быстрого поиска"""
    return jsonify({'message': 'Поиск очищен'})

def clear_patient_search():
    """Очистка поиска пациентов"""
    return jsonify({'message': 'Поиск пациентов очищен'})

def load_dashboard_data():
    """Загрузка данных для дашборда"""
    try:
        stats = get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Load dashboard data error: {e}")
        return jsonify({'error': f'Ошибка загрузки данных: {str(e)}'}), 500

# === ВСПОМОГАТЕЛЬНЫЕ МАРШРУТЫ ===

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    """Получить список врачей"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, first_name, last_name, middle_name, 
                       specialization, license_number, phone, email,
                       created_at
                FROM doctors
                ORDER BY last_name, first_name
            """)
            doctors = cursor.fetchall()
            
            formatted_doctors = []
            for doctor in doctors:
                formatted = dict(doctor)
                
                # Форматируем телефон
                if formatted['phone']:
                    digits = ''.join(filter(str.isdigit, formatted['phone']))
                    if len(digits) == 11:
                        formatted['phone'] = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
                else:
                    formatted['phone'] = "не указан"
                
                # Форматируем email
                if not formatted['email']:
                    formatted['email'] = "не указан"
                
                formatted_doctors.append(formatted)
            
            return jsonify({'doctors': formatted_doctors})
            
    except Exception as e:
        logger.error(f"Get doctors error: {e}")
        return jsonify({'error': f'Ошибка получения врачей: {str(e)}'}), 500

@app.route('/api/doctors/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    """Получить данные врача по ID"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT d.*, 
                       COUNT(DISTINCT a.id) as total_appointments
                FROM doctors d
                LEFT JOIN appointments a ON d.id = a.doctor_id
                WHERE d.id = %s
                GROUP BY d.id
            """, (doctor_id,))
            
            doctor = cursor.fetchone()
            
            if not doctor:
                return jsonify({'error': 'Врач не найден'}), 404
            
            formatted_doctor = dict(doctor)
            
            # Форматируем телефон
            if formatted_doctor['phone']:
                digits = ''.join(filter(str.isdigit, formatted_doctor['phone']))
                if len(digits) == 11:
                    formatted_doctor['phone'] = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
            else:
                formatted_doctor['phone'] = "не указан"
            
            # Форматируем email
            if not formatted_doctor['email']:
                formatted_doctor['email'] = "не указан"
                
            return jsonify(formatted_doctor)
            
    except Exception as e:
        logger.error(f"Get doctor error: {e}")
        return jsonify({'error': f'Ошибка получения врача: {str(e)}'}), 500

# === ДОПОЛНИТЕЛЬНЫЕ API МАРШРУТЫ ===

@app.route('/api/patients/list', methods=['GET'])
def get_patients_list():
    """Получить упрощенный список пациентов для выпадающих списков"""
    try:
        with db.get_cursor() as cursor:
            if TDE_ENABLED:
                cursor.execute("""
                    SELECT id, first_name, last_name, middle_name,
                           phone_encrypted, phone_iv,
                           email_encrypted, email_iv
                    FROM patients
                    ORDER BY last_name, first_name
                    LIMIT 1000
                """)
            else:
                cursor.execute("""
                    SELECT id, first_name, last_name, middle_name, phone, email
                    FROM patients
                    ORDER BY last_name, first_name
                    LIMIT 1000
                """)
            
            patients = cursor.fetchall()
            
            formatted_patients = []
            for patient in patients:
                formatted = {
                    'id': patient['id'],
                    'first_name': patient['first_name'],
                    'last_name': patient['last_name'],
                    'middle_name': patient['middle_name']
                }
                
                # Расшифровываем контактные данные если нужно
                if TDE_ENABLED and patient.get('phone_encrypted'):
                    decrypted_phone = safe_decrypt_field('patients', 'phone', 
                                                       patient['phone_encrypted'], 
                                                       patient['phone_iv'])
                    formatted['phone'] = decrypted_phone if decrypted_phone else "не указан"
                else:
                    formatted['phone'] = patient.get('phone', "не указан")
                
                if TDE_ENABLED and patient.get('email_encrypted'):
                    decrypted_email = safe_decrypt_field('patients', 'email', 
                                                       patient['email_encrypted'], 
                                                       patient['email_iv'])
                    formatted['email'] = decrypted_email if decrypted_email else "не указан"
                else:
                    formatted['email'] = patient.get('email', "не указан")
                
                formatted_patients.append(formatted)
            
            return jsonify({
                'patients': formatted_patients,
                'count': len(formatted_patients)
            })
            
    except Exception as e:
        logger.error(f"Get patients list error: {e}")
        return jsonify({'error': f'Ошибка получения списка пациентов: {str(e)}'}), 500

@app.route('/api/doctors/list', methods=['GET'])
def get_doctors_list():
    """Получить упрощенный список врачей для выпадающих списков"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, first_name, last_name, middle_name, specialization
                FROM doctors
                ORDER BY specialization, last_name, first_name
            """)
            
            doctors = cursor.fetchall()
            
            formatted_doctors = []
            for doctor in doctors:
                formatted_doctors.append({
                    'id': doctor['id'],
                    'first_name': doctor['first_name'],
                    'last_name': doctor['last_name'],
                    'middle_name': doctor['middle_name'],
                    'specialization': doctor['specialization']
                })
            
            return jsonify({
                'doctors': formatted_doctors,
                'count': len(formatted_doctors)
            })
            
    except Exception as e:
        logger.error(f"Get doctors list error: {e}")
        return jsonify({'error': f'Ошибка получения списка врачей: {str(e)}'}), 500

@app.route('/api/appointments/completed-without-records', methods=['GET'])
def get_completed_appointments_without_records():
    """Получить завершённые приёмы без медицинских записей для создания медкарт"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT a.id, a.appointment_date,
                       p.first_name || ' ' || p.last_name || 
                       COALESCE(' ' || p.middle_name, '') as patient_name,
                       d.first_name || ' ' || d.last_name || 
                       COALESCE(' ' || d.middle_name, '') as doctor_name,
                       d.specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                LEFT JOIN medical_records mr ON a.id = mr.appointment_id
                WHERE a.status = 'completed' 
                AND mr.id IS NULL
                ORDER BY a.appointment_date DESC
                LIMIT 200
            """)
            
            appointments = cursor.fetchall()
            
            formatted_appointments = []
            for appointment in appointments:
                formatted_appointments.append({
                    'id': appointment['id'],
                    'patient_name': appointment['patient_name'].strip(),
                    'doctor_name': appointment['doctor_name'].strip(),
                    'specialization': appointment['specialization'],
                    'appointment_date': format_datetime_russian(appointment['appointment_date'])
                })
            
            return jsonify({
                'appointments': formatted_appointments,
                'count': len(formatted_appointments)
            })
            
    except Exception as e:
        logger.error(f"Get completed appointments without records error: {e}")
        return jsonify({'error': f'Ошибка получения приёмов: {str(e)}'}), 500

# === ОБРАБОТЧИКИ ОШИБОК ===

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint не найден'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Неверный запрос'}), 400

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Метод не разрешен'}), 405

# === ДОПОЛНИТЕЛЬНЫЕ УТИЛИТЫ ===

def validate_patient_data(data):
    """Валидация данных пациента"""
    errors = []
    
    if not data.get('first_name'):
        errors.append('Имя обязательно')
    if not data.get('last_name'):
        errors.append('Фамилия обязательна')
    if not data.get('birth_date'):
        errors.append('Дата рождения обязательна')
    if not data.get('gender') or data['gender'] not in ['M', 'F']:
        errors.append('Пол должен быть M или F')
    
    if data.get('email') and '@' not in data['email']:
        errors.append('Неверный формат email')
    
    if data.get('phone'):
        digits = ''.join(filter(str.isdigit, data['phone']))
        if len(digits) < 10:
            errors.append('Неверный формат телефона')
    
    return errors

def format_validation_errors(errors):
    """Форматирование ошибок валидации"""
    if not errors:
        return None
    
    return {
        'error': 'Ошибки валидации',
        'details': errors,
        'count': len(errors)
    }

# === УТИЛИТЫ ДЛЯ ОТЛАДКИ ===

@app.route('/api/debug/tde-status', methods=['GET'])
def debug_tde_status():
    """Отладочная информация о статусе TDE"""
    if not TDE_ENABLED:
        return jsonify({
            'tde_enabled': False,
            'message': 'TDE отключен'
        })
    
    try:
        info = {
            'tde_enabled': TDE_ENABLED,
            'tde_manager_initialized': tde_manager is not None,
            'encryption_key_exists': os.path.exists(os.getenv('ENCRYPTION_KEY_FILE', '.encryption_key'))
        }
        
        if tde_manager:
            info['encryption_info'] = tde_manager.get_encryption_info()
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({
            'tde_enabled': TDE_ENABLED,
            'error': str(e)
        })

@app.route('/api/debug/database-structure', methods=['GET'])
def debug_database_structure():
    """Отладочная информация о структуре БД"""
    try:
        with db.get_cursor() as cursor:
            # Проверяем TDE поля в таблице patients
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'patients' 
                AND (column_name LIKE '%_encrypted' OR column_name LIKE '%_iv')
                ORDER BY column_name
            """)
            
            tde_columns = cursor.fetchall()
            
            # Проверяем обычные поля
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'patients' 
                AND column_name NOT LIKE '%_encrypted' 
                AND column_name NOT LIKE '%_iv'
                ORDER BY ordinal_position
            """)
            
            regular_columns = cursor.fetchall()
            
            return jsonify({
                'table': 'patients',
                'tde_columns': [dict(col) for col in tde_columns],
                'regular_columns': [dict(col) for col in regular_columns],
                'tde_columns_count': len(tde_columns),
                'regular_columns_count': len(regular_columns)
            })
            
    except Exception as e:
        logger.error(f"Debug database structure error: {e}")
        return jsonify({'error': f'Ошибка проверки структуры БД: {str(e)}'}), 500

# === ЗАПУСК ПРИЛОЖЕНИЯ ===

if __name__ == '__main__':
    logger.info("🏥 Запуск системы медкарт...")
    logger.info(f"🔒 TDE: {'Включен' if TDE_ENABLED else 'Отключен'}")
    
    # Проверяем готовность системы
    try:
        if db.test_connection():
            logger.info("✅ База данных подключена")
        else:
            logger.error("❌ Проблемы с подключением к БД")
    except Exception as e:
        logger.error(f"❌ Ошибка проверки БД: {e}")
    
    # Проверяем TDE если включен
    if TDE_ENABLED and tde_manager:
        try:
            info = tde_manager.get_encryption_info()
            logger.info(f"🔐 TDE инициализирован: {info['algorithm']}")
        except Exception as e:
            logger.error(f"⚠️ Проблемы с TDE: {e}")
    
    logger.info("🚀 Сервер запускается на http://localhost:8000")
    logger.info("📖 API документация: http://localhost:8000/api")
    
    app.run(host='0.0.0.0', port=8000, debug=True)