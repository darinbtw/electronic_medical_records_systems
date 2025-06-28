"""
Главный файл для запуска API системы медицинских карт
"""
from flask import Flask
from flask_cors import CORS
import sys
from pathlib import Path

# Добавляем путь к корню проекта
sys.path.insert(0, str(Path(__file__).parent.parent))

# Импортируем русскую версию API
from src.api.russian_routes import app

# Включаем CORS для работы с frontend
CORS(app)

if __name__ == '__main__':
    print("Запуск системы медкарт с русской локализацией...")
    print("URL: http://localhost:8000")
    print("Веб-интерфейс с правильным форматированием дат")
    app.run(host='0.0.0.0', port=8000, debug=True)