from flask import Flask, request, jsonify
from datetime import datetime
import jwt
from functools import wraps
from src.database.connection import db
from src.security.encryption import AESEncryption
from src.api.validators import Validators
from src.config import config

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
encryption = AESEncryption()

# === ПАЦИЕНТЫ ===

@app.route('/api/patients', methods=['GET'])
def get_patients():
    """Получить список пациентов с пагинацией"""
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
            
            return jsonify({
                'patients': patients,
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
    """Получить данные пациента по ID"""
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
                return jsonify({'error': 'Patient not found'}), 404
                
            return jsonify(patient)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients', methods=['POST'])
def create_patient():
    """Создать нового пациента"""
    data = request.get_json()
    
    # Валидация
    required = ['first_name', 'last_name', 'birth_date', 'gender']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO patients 
                (first_name, last_name, middle_name, birth_date, 
                 gender, phone, email, address)
                VALUES (%(first_name)s, %(last_name)s, %(middle_name)s, 
                        %(birth_date)s, %(gender)s, %(phone)s, %(email)s, %(address)s)
                RETURNING id, created_at
            """, {
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'middle_name': data.get('middle_name'),
                'birth_date': data['birth_date'],
                'gender': data['gender'],
                'phone': data.get('phone'),
                'email': data.get('email'),
                'address': data.get('address')
            })
            
            result = cursor.fetchone()
            return jsonify({
                'id': result['id'],
                'created_at': result['created_at'].isoformat(),
                'message': 'Patient created successfully'
            }), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """Обновить данные пациента"""
    data = request.get_json()
    
    try:
        with db.get_cursor() as cursor:
            # Проверяем существование
            cursor.execute("SELECT id FROM patients WHERE id = %s", (patient_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Patient not found'}), 404
            
            # Обновляем
            cursor.execute("""
                UPDATE patients 
                SET first_name = %(first_name)s,
                    last_name = %(last_name)s,
                    middle_name = %(middle_name)s,
                    phone = %(phone)s,
                    email = %(email)s,
                    address = %(address)s
                WHERE id = %(id)s
                RETURNING updated_at
            """, {
                'id': patient_id,
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'middle_name': data.get('middle_name'),
                'phone': data.get('phone'),
                'email': data.get('email'),
                'address': data.get('address')
            })
            
            updated_at = cursor.fetchone()['updated_at']
            return jsonify({
                'message': 'Patient updated successfully',
                'updated_at': updated_at.isoformat()
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === ПРИЕМЫ ===

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    """Получить список приемов"""
    patient_id = request.args.get('patient_id')
    doctor_id = request.args.get('doctor_id')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    try:
        with db.get_cursor() as cursor:
            query = """
                SELECT a.*, 
                       p.first_name || ' ' || p.last_name as patient_name,
                       d.first_name || ' ' || d.last_name as doctor_name,
                       d.specialization
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE 1=1
            """
            params = []
            
            if patient_id:
                query += " AND a.patient_id = %s"
                params.append(patient_id)
            
            if doctor_id:
                query += " AND a.doctor_id = %s"
                params.append(doctor_id)
                
            if date_from:
                query += " AND a.appointment_date >= %s"
                params.append(date_from)
                
            if date_to:
                query += " AND a.appointment_date <= %s"
                params.append(date_to)
            
            query += " ORDER BY a.appointment_date DESC LIMIT 100"
            
            cursor.execute(query, params)
            appointments = cursor.fetchall()
            
            return jsonify({'appointments': appointments})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/appointments', methods=['POST'])
def create_appointment():
    """Создать новый прием"""
    data = request.get_json()
    
    required = ['patient_id', 'doctor_id', 'appointment_date']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO appointments 
                (patient_id, doctor_id, appointment_date, status)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
                data['patient_id'],
                data['doctor_id'],
                data['appointment_date'],
                data.get('status', 'scheduled')
            ))
            
            appointment_id = cursor.fetchone()['id']
            
            return jsonify({
                'id': appointment_id,
                'message': 'Appointment created successfully'
            }), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === МЕДИЦИНСКИЕ ЗАПИСИ ===

@app.route('/api/medical-records', methods=['POST'])
def create_medical_record():
    """Создать медицинскую запись с шифрованным диагнозом"""
    data = request.get_json()
    
    required = ['appointment_id', 'diagnosis']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    try:
        # Шифруем диагноз
        encrypted_diagnosis, iv = encryption.encrypt(data['diagnosis'])
        
        with db.get_cursor() as cursor:
            # Проверяем, что прием существует и завершен
            cursor.execute("""
                UPDATE appointments 
                SET status = 'completed' 
                WHERE id = %s AND status = 'scheduled'
                RETURNING id
            """, (data['appointment_id'],))
            
            if not cursor.fetchone():
                return jsonify({'error': 'Appointment not found or already completed'}), 400
            
            # Создаем запись
            cursor.execute("""
                INSERT INTO medical_records 
                (appointment_id, diagnosis_encrypted, diagnosis_iv, 
                 complaints, examination_results)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data['appointment_id'],
                encrypted_diagnosis,
                iv,
                data.get('complaints'),
                data.get('examination_results')
            ))
            
            record_id = cursor.fetchone()['id']
            
            # Добавляем назначения
            if 'prescriptions' in data:
                for prescription in data['prescriptions']:
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
                'message': 'Medical record created successfully'
            }), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/medical-records/<int:record_id>', methods=['GET'])
def get_medical_record(record_id):
    """Получить медицинскую запись с расшифровкой"""
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
                return jsonify({'error': 'Medical record not found'}), 404
            
            # Расшифровываем диагноз
            if record['diagnosis_encrypted']:
                decrypted = encryption.decrypt(
                    bytes(record['diagnosis_encrypted']),
                    bytes(record['diagnosis_iv'])
                )
                record['diagnosis'] = decrypted
                del record['diagnosis_encrypted']
                del record['diagnosis_iv']
            
            # Получаем назначения
            cursor.execute("""
                SELECT * FROM prescriptions 
                WHERE medical_record_id = %s
            """, (record_id,))
            
            record['prescriptions'] = cursor.fetchall()
            
            return jsonify(record)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === СТАТИСТИКА ===

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Получить статистику системы"""
    try:
        with db.get_cursor() as cursor:
            stats = {}
            
            # Общая статистика
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM patients) as total_patients,
                    (SELECT COUNT(*) FROM doctors) as total_doctors,
                    (SELECT COUNT(*) FROM appointments) as total_appointments,
                    (SELECT COUNT(*) FROM appointments WHERE status = 'scheduled') as scheduled_appointments,
                    (SELECT COUNT(*) FROM medical_records) as total_records
            """)
            stats['general'] = cursor.fetchone()
            
            # Статистика по врачам
            cursor.execute("""
                SELECT d.id, d.first_name, d.last_name, d.specialization,
                       COUNT(a.id) as appointment_count
                FROM doctors d
                LEFT JOIN appointments a ON d.id = a.doctor_id
                GROUP BY d.id
                ORDER BY appointment_count DESC
            """)
            stats['doctors'] = cursor.fetchall()
            
            # Статистика по диагнозам (топ-10)
            cursor.execute("""
                SELECT 
                    DATE_TRUNC('month', a.appointment_date) as month,
                    COUNT(*) as appointment_count
                FROM appointments a
                WHERE a.appointment_date >= CURRENT_DATE - INTERVAL '12 months'
                GROUP BY month
                ORDER BY month
            """)
            stats['monthly_appointments'] = cursor.fetchall()
            
            return jsonify(stats)
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)