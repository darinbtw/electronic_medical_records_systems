"""
Главный файл для запуска API системы медицинских карт
"""
from flask import Flask
from flask_cors import CORS
import sys
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

# Импортируем все routes
from src.api.full_routes import app

# Включаем CORS для работы с frontend
CORS(app)

if __name__ == '__main__':
    print("🏥 Starting Medical Records System API...")
    print("📍 URL: http://localhost:8000")
    print("📚 Full API documentation available")
    app.run(host='0.0.0.0', port=8000, debug=True)