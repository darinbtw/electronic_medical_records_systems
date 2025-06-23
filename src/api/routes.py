from flask import Flask, request, jsonify
from functools import wraps
import jwt
from datetime import datetime, timedelta
import os
from src.database.connection import db
from src.security.encryption import AESEncryption
from src.api.validators import Validators
from src.config import config

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# Инициализация шифрования
encryption = AESEncryption()

def require_auth(f):
    """Декоратор для проверки JWT токена"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        try:
            # Убираем "Bearer " из токена
            if token.startswith('Bearer '):
                token = token[7:]
                
            payload = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            request.user_id = payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

@app.route('/api/login', methods=['POST'])
def login():
    """Простая аутентификация для тестирования"""
    data = request.get_json()
    
    # В реальном проекте здесь должна быть проверка логина/пароля
    if data.get('username') == 'admin' and data.get('password') == 'admin':
        # Создаем JWT токен
        payload = {
            'user_id': 1,
            'username': 'admin',
            'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'token': token,
            'message': 'Login successful'
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/patients', methods=['POST'])
@require_auth
def create_patient():
    """Создание нового пациента"""
    data = request.get_json()
    
    # Валидация
    required_fields = ['first_name', 'last_name', 'birth_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    # Валидация email и телефона
    if 'email' in data and data['email']:
        if not Validators.validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
    
    if 'phone' in data and data['phone']:
        if not Validators.validate_phone(data['phone']):
            return jsonify({'error': 'Invalid phone format'}), 400
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO patients 
                (first_name, last_name, middle_name, birth_date, gender, phone, email, address)
                VALUES (%(first_name)s, %(last_name)s, %(middle_name)s, %(birth_date)s, 
                        %(gender)s, %(phone)s, %(email)s, %(address)s)
                RETURNING id, created_at
            """, {
                'first_name': Validators.sanitize_string(data.get('first_name')),
                'last_name': Validators.sanitize_string(data.get('last_name')),
                'middle_name': Validators.sanitize_string(data.get('middle_name', '')),
                'birth_date': data.get('birth_date'),
                'gender': data.get('gender'),
                'phone': data.get('phone'),
                'email': data.get('email'),
                'address': Validators.sanitize_string(data.get('address', ''))
            })
            
            result = cursor.fetchone()
            
        return jsonify({
            'id': result['id'],
            'message': 'Patient created successfully',
            'created_at': result['created_at'].isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/patients/search', methods=['GET'])
@require_auth
def search_patients():
    """Поиск пациентов"""
    search_term = request.args.get('q', '').strip()
    
    if len(search_term) < 2:
        return jsonify({'error': 'Search term too short'}), 400
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, first_name, last_name, middle_name, birth_date, phone, email
                FROM patients
                WHERE last_name ILIKE %s OR first_name ILIKE %s OR middle_name ILIKE %s
                ORDER BY last_name, first_name
                LIMIT 50
            """, (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            
            patients = cursor.fetchall()
            
        return jsonify({
            'results': patients,
            'count': len(patients)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/medical-records', methods=['POST'])
@require_auth
def create_medical_record():
    """Создание медицинской записи с шифрованием диагноза"""
    data = request.get_json()
    
    required_fields = ['appointment_id', 'diagnosis']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    try:
        # Шифруем диагноз
        encrypted_diagnosis, iv = encryption.encrypt(data['diagnosis'])
        
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO medical_records 
                (appointment_id, diagnosis_encrypted, diagnosis_iv, complaints, examination_results)
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
            
        return jsonify({
            'id': record_id,
            'message': 'Medical record created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    from src.main import app as main_app
    # Используем основное приложение из main.py