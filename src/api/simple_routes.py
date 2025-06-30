# Упрощенная версия API маршрутов без TDE
from flask import request, jsonify
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import db

def create_patient_simple():
    """Упрощенное создание пациента без TDE"""
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
                'created_at': result['created_at'].isoformat(),
                'message': 'Пациент успешно добавлен'
            }), 201
            
    except Exception as e:
        return jsonify({'error': f'Ошибка создания пациента: {str(e)}'}), 500

print("Упрощенные маршруты готовы к использованию")
