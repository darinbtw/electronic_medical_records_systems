# Замените содержимое файла: src/api/russian_routes.py

from flask import Flask, request, jsonify, send_file
from datetime import datetime
import os
import sys

# Добавляем путь к корню проекта
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from src.database.connection import db
from src.security.encryption import AESEncryption
from src.api.validators import Validators
from src.config import config

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
encryption = AESEncryption()

# Включаем CORS для работы с web_interface.html
from flask_cors import CORS
CORS(app)

def format_patient_data(patient):
    """Форматирование данных пациента для русского интерфейса"""
    if not patient:
        return patient
    
    # Создаем копию для безопасности
    formatted = dict(patient)
    
    # Форматируем дату рождения
    if 'birth_date' in formatted and formatted['birth_date']:
        try:
            if isinstance(formatted['birth_date'], str):
                # Если строка, парсим
                birth_date = datetime.strptime(formatted['birth_date'], '%Y-%m-%d').date()
            else:
                birth_date = formatted['birth_date']
            formatted['birth_date'] = birth_date.strftime('%d.%m.%Y')
        except:
            pass
    
    # Форматируем телефон
    if 'phone' in formatted:
        phone = formatted['phone']
        if phone:
            digits = ''.join(filter(str.isdigit, phone))
            if len(digits) == 11 and digits.startswith('7'):
                formatted['phone'] = f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
            elif len(digits) == 11 and digits.startswith('8'):
                formatted['phone'] = f"8 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
        else:
            formatted['phone'] = "не указан"
    
    # Форматируем email
    if 'email' in formatted:
        if not formatted['email']:
            formatted['email'] = "не указан"
    
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
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y %H:%M')
    except:
        return str(dt)

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
            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            'details': {
                'patients_count': patients_count,
                'doctors_count': doctors_count
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'ERROR',
            'database': 'ERROR',
            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            'details': {'error': str(e)}
        })

# === ПОИСК ПАЦИЕНТОВ ===

@app.route('/api/search')
def search():
    """Универсальный поиск с русским форматированием"""
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'patients')
    
    if search_type == 'doctors':
        try:
            with db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, first_name, last_name, middle_name, 
                           specialization, phone, email
                    FROM doctors
                    ORDER BY last_name, first_name
                """)
                doctors = cursor.fetchall()
                
                # Форматируем каждого врача
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
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Поиск пациентов
    if len(query) < 2:
        return jsonify({'error': 'Запрос слишком короткий', 'patients': []}), 200
    
    try:
        with db.get_cursor() as cursor:
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
            
            # Форматируем каждого пациента
            formatted_patients = [format_patient_data(patient) for patient in patients]
            
        return jsonify({
            'patients': formatted_patients,
            'count': len(formatted_patients),
            'query': query
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === ПАЦИЕНТЫ ===

@app.route('/api/patients', methods=['GET'])
def get_patients():
    """Получить список пациентов с русским форматированием"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    try:
        with db.get_cursor() as cursor:
            # Общее количество
            cursor.execute("SELECT COUNT(*) as total FROM patients")
            total = cursor.fetchone()['total']
            
            # Пациенты на странице
            cursor.execute("""
                SELECT id, first_name, last_name, middle_name, 
                       birth_date, gender, phone, email
                FROM patients
                ORDER BY last_name, first_name
                LIMIT %s OFFSET %s
            """, (per_page, offset))
            
            patients = cursor.fetchall()
            
            # Форматируем каждого пациента
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
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Получить данные пациента по ID с русским форматированием"""
    try:
        with db.get_cursor() as cursor:
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
            
            # Форматируем данные
            formatted_patient = format_patient_data(patient)
            
            # Форматируем дату последнего приема
            if formatted_patient['last_appointment']:
                formatted_patient['last_appointment'] = format_datetime_russian(
                    formatted_patient['last_appointment']
                )
            else:
                formatted_patient['last_appointment'] = "нет"
                
            return jsonify(formatted_patient)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === ПРИЕМЫ ===

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    """Получить список приемов с русским форматированием"""
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
                ORDER BY a.appointment_date DESC 
                LIMIT 100
            """)
            
            appointments = cursor.fetchall()
            
            # Форматируем каждый прием
            formatted_appointments = []
            for appointment in appointments:
                formatted = dict(appointment)
                
                # Форматируем дату и время приема
                formatted['appointment_date'] = format_datetime_russian(
                    formatted['appointment_date']
                )
                
                # Переводим статус
                status_map = {
                    'scheduled': 'запланирован',
                    'completed': 'завершен', 
                    'cancelled': 'отменен'
                }
                formatted['status'] = status_map.get(
                    formatted['status'], formatted['status']
                )
                
                formatted_appointments.append(formatted)
            
            return jsonify({'appointments': formatted_appointments})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === СТАТИСТИКА ===

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Получить статистику системы"""
    try:
        with db.get_cursor() as cursor:
            # Общая статистика
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM patients) as total_patients,
                    (SELECT COUNT(*) FROM doctors) as total_doctors,
                    (SELECT COUNT(*) FROM appointments) as total_appointments,
                    (SELECT COUNT(*) FROM appointments WHERE status = 'scheduled') as scheduled_appointments,
                    (SELECT COUNT(*) FROM medical_records) as total_records
            """)
            general_stats = cursor.fetchone()
            
            # Статистика по врачам
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
        return jsonify({'error': str(e)}), 500

# Остальные маршруты (создание пациентов, медкарт) остаются без изменений
# но можно добавить русские сообщения об ошибках

@app.route('/api/patients', methods=['POST'])
def create_patient():
    """Создать нового пациента"""
    data = request.get_json()
    
    required = ['first_name', 'last_name', 'birth_date', 'gender']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Отсутствует поле: {field}'}), 400
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO patients 
                (first_name, last_name, middle_name, birth_date, 
                 gender, phone, email, address)
                VALUES (%(first_name)s, %(last_name)s, %(middle_name)s, 
                        %(birth_date)s, %(gender)s, %(phone)s, %(email)s, %(address)s)
                RETURNING id, created_at
            """, data)
            
            result = cursor.fetchone()
            return jsonify({
                'id': result['id'],
                'created_at': format_datetime_russian(result['created_at']),
                'message': 'Пациент успешно добавлен'
            }), 201
            
    except Exception as e:
        return jsonify({'error': f'Ошибка создания пациента: {str(e)}'}), 500

@app.route('/api/appointments', methods=['GET'])
def get_appointments_paginated():
    """Получить список приемов с пагинацией и фильтрами"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    status_filter = request.args.get('status', '')
    offset = (page - 1) * per_page
    
    try:
        with db.get_cursor() as cursor:
            # Строим WHERE условие
            where_clause = ""
            params = []
            
            if status_filter:
                where_clause = "WHERE a.status = %s"
                params.append(status_filter)
            
            # Общее количество
            count_query = f"""
                SELECT COUNT(*) as total 
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                {where_clause}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Приемы на странице
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
            
            # Форматируем каждый прием
            formatted_appointments = []
            for appointment in appointments:
                formatted = dict(appointment)
                
                # Форматируем дату и время приема
                formatted['appointment_date'] = format_datetime_russian(
                    formatted['appointment_date']
                )
                
                # Переводим статус
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
                    'pages': (total + per_page - 1) // per_page
                }
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/medical-records', methods=['GET'])
def get_medical_records_paginated():
    """Получить список медицинских записей с пагинацией"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    offset = (page - 1) * per_page
    
    try:
        with db.get_cursor() as cursor:
            # Общее количество
            cursor.execute("SELECT COUNT(*) as total FROM medical_records")
            total = cursor.fetchone()['total']
            
            # Записи на странице
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
            
            # Форматируем записи (без расшифровки диагноза)
            formatted_records = []
            for record in records:
                formatted = dict(record)
                
                # Форматируем дату приема
                formatted['appointment_date'] = format_datetime_russian(
                    formatted['appointment_date']
                )
                
                # Удаляем зашифрованные данные из списка
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
                    'pages': (total + per_page - 1) // per_page
                }
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/medical-records/<int:record_id>', methods=['GET'])
def get_medical_record_with_decryption(record_id):
    """Получить медицинскую запись с расшифровкой диагноза"""
    try:
        with db.get_cursor() as cursor:
            # Получаем запись
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
            
            # Форматируем данные
            formatted_record = dict(record)
            
            # Расшифровываем диагноз
            if record['diagnosis_encrypted'] and record['diagnosis_iv']:
                try:
                    decrypted = encryption.decrypt(
                        bytes(record['diagnosis_encrypted']),
                        bytes(record['diagnosis_iv'])
                    )
                    formatted_record['diagnosis'] = decrypted
                except Exception as e:
                    formatted_record['diagnosis'] = f"Ошибка расшифровки: {e}"
            else:
                formatted_record['diagnosis'] = "Диагноз не зашифрован"
            
            # Удаляем зашифрованные данные
            del formatted_record['diagnosis_encrypted']
            del formatted_record['diagnosis_iv']
            
            # Форматируем дату
            formatted_record['appointment_date'] = format_datetime_russian(
                formatted_record['appointment_date']
            )
            
            # Получаем назначения
            cursor.execute("""
                SELECT * FROM prescriptions 
                WHERE medical_record_id = %s
                ORDER BY id
            """, (record_id,))
            
            formatted_record['prescriptions'] = cursor.fetchall()
            
            return jsonify(formatted_record)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    """Создать новый прием"""
    data = request.get_json()
    
    required = ['patient_id', 'doctor_id', 'appointment_date']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Отсутствует поле: {field}'}), 400
    
    try:
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
                'message': 'Прием успешно создан'
            }), 201
            
    except Exception as e:
        return jsonify({'error': f'Ошибка создания приема: {str(e)}'}), 500

@app.route('/api/medical-records', methods=['POST'])
def create_medical_record():
    """Создать медицинскую запись с шифрованным диагнозом"""
    data = request.get_json()
    
    required = ['appointment_id', 'diagnosis']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Отсутствует поле: {field}'}), 400
    
    try:
        # Шифруем диагноз
        encrypted_diagnosis, iv = encryption.encrypt(data['diagnosis'])
        
        with db.get_cursor() as cursor:
            # Проверяем, что прием существует и можно создать запись
            cursor.execute("""
                SELECT id, status FROM appointments 
                WHERE id = %s
            """, (data['appointment_id'],))
            
            appointment = cursor.fetchone()
            if not appointment:
                return jsonify({'error': 'Прием не найден'}), 400
            
            # Проверяем, что запись для этого приема еще не создана
            cursor.execute("""
                SELECT id FROM medical_records 
                WHERE appointment_id = %s
            """, (data['appointment_id'],))
            
            existing_record = cursor.fetchone()
            if existing_record:
                return jsonify({'error': 'Медицинская запись для этого приема уже существует'}), 400
            
            # Обновляем статус приема на "завершен"
            cursor.execute("""
                UPDATE appointments 
                SET status = 'completed' 
                WHERE id = %s
            """, (data['appointment_id'],))
            
            # Создаем запись
            cursor.execute("""
                INSERT INTO medical_records 
                (appointment_id, diagnosis_encrypted, diagnosis_iv, 
                 complaints, examination_results)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (
                data['appointment_id'],
                encrypted_diagnosis,
                iv,
                data.get('complaints'),
                data.get('examination_results')
            ))
            
            result = cursor.fetchone()
            record_id = result['id']
            
            # Добавляем назначения
            if 'prescriptions' in data and data['prescriptions']:
                for prescription in data['prescriptions']:
                    if prescription.get('medication_name'):  # Проверяем что название препарата не пустое
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
        return jsonify({'error': f'Ошибка создания медкарты: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)