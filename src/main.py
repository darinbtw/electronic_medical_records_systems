"""
Главный файл для запуска API системы медицинских карт
"""
from flask import Flask, jsonify, request
from src.database.connection import db
from src.models.patient import Patient
from src.models.doctor import Doctor
from src.api.validators import Validators
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    """Главная страница API"""
    return jsonify({
        "name": "Medical Records System API",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "patients": "/api/patients",
            "doctors": "/api/doctors",
            "search": "/api/search"
        }
    })

@app.route('/health')
def health_check():
    """Проверка состояния системы"""
    try:
        if db.test_connection():
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "message": "System is operational"
            })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    
    return jsonify({
        "status": "unhealthy",
        "database": "disconnected",
        "error": str(e)
    }), 500

@app.route('/api/patients', methods=['GET'])
def get_patients():
    """Получить список пациентов"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, first_name, last_name, middle_name, 
                       birth_date, gender, phone, email
                FROM patients
                ORDER BY last_name, first_name
                LIMIT 100
            """)
            patients = cursor.fetchall()
            return jsonify({"patients": patients, "count": len(patients)})
    except Exception as e:
        logger.error(f"Error fetching patients: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_patients():
    """Поиск пациентов по ФИО"""
    query = request.args.get('q', '')
    if len(query) < 3:
        return jsonify({"error": "Query too short (min 3 chars)"}), 400
    
    try:
        with db.get_cursor() as cursor:
            # Безопасный поиск с параметризованным запросом
            cursor.execute("""
                SELECT id, first_name, last_name, middle_name, phone
                FROM patients
                WHERE last_name ILIKE %s 
                   OR first_name ILIKE %s
                   OR middle_name ILIKE %s
                ORDER BY last_name, first_name
                LIMIT 50
            """, (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            results = cursor.fetchall()
            return jsonify({"results": results, "count": len(results)})
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_data():
    """Валидация данных"""
    data = request.json
    results = {}
    
    if 'email' in data:
        results['email'] = {
            'value': data['email'],
            'valid': Validators.validate_email(data['email'])
        }
    
    if 'phone' in data:
        results['phone'] = {
            'value': data['phone'],
            'valid': Validators.validate_phone(data['phone'])
        }
    
    return jsonify(results)

if __name__ == '__main__':
    print("🏥 Starting Medical Records System API...")
    print("📍 URL: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/")
    app.run(host='0.0.0.0', port=8000, debug=True)