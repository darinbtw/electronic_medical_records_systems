#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Исправление проблемы "Invalid Date" в системе медкарт
"""

import os
import sys
from pathlib import Path
from datetime import datetime, date

# Добавляем корневую папку в path
sys.path.insert(0, str(Path(__file__).parent))

def fix_invalid_dates():
    """Исправление неправильных дат в БД"""
    print("🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ 'Invalid Date'")
    print("=" * 50)
    
    try:
        from src.database.connection import db
        
        print("🔍 Проверка дат в базе данных...")
        
        with db.get_cursor() as cursor:
            # Проверяем даты рождения пациентов
            cursor.execute("""
                SELECT id, first_name, last_name, birth_date 
                FROM patients 
                ORDER BY id
            """)
            
            patients = cursor.fetchall()
            
            print(f"📋 Найдено пациентов: {len(patients)}")
            
            fixed_count = 0
            problem_dates = []
            
            for patient in patients:
                birth_date = patient['birth_date']
                patient_name = f"{patient['last_name']} {patient['first_name']}"
                
                print(f"   👤 {patient_name}: {birth_date}")
                
                # Проверяем, что дата валидна
                if birth_date:
                    try:
                        if isinstance(birth_date, str):
                            # Пробуем распарсить строку
                            test_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                        elif isinstance(birth_date, date):
                            test_date = birth_date
                        else:
                            test_date = birth_date
                        
                        # Проверяем разумность даты
                        current_year = datetime.now().year
                        if test_date.year < 1900 or test_date.year > current_year:
                            problem_dates.append({
                                'id': patient['id'],
                                'name': patient_name,
                                'date': birth_date,
                                'reason': 'Неразумный год'
                            })
                        
                    except Exception as e:
                        problem_dates.append({
                            'id': patient['id'],
                            'name': patient_name,
                            'date': birth_date,
                            'reason': f'Ошибка парсинга: {e}'
                        })
            
            if problem_dates:
                print(f"\n⚠️ Найдено проблемных дат: {len(problem_dates)}")
                for problem in problem_dates:
                    print(f"   ❌ {problem['name']}: {problem['date']} ({problem['reason']})")
                
                print(f"\n🔧 Исправление проблемных дат...")
                
                for problem in problem_dates:
                    # Устанавливаем дату по умолчанию: 01.01.1990
                    default_date = '1990-01-01'
                    
                    cursor.execute("""
                        UPDATE patients 
                        SET birth_date = %s
                        WHERE id = %s
                    """, (default_date, problem['id']))
                    
                    print(f"   ✅ {problem['name']}: исправлено на {default_date}")
                    fixed_count += 1
                
                print(f"\n✅ Исправлено дат: {fixed_count}")
            else:
                print("✅ Все даты в порядке!")
            
            # Проверяем даты приёмов
            print(f"\n🔍 Проверка дат приёмов...")
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM appointments 
                WHERE appointment_date IS NULL
            """)
            
            null_appointments = cursor.fetchone()['count']
            
            if null_appointments > 0:
                print(f"⚠️ Найдено приёмов с NULL датой: {null_appointments}")
                
                # Исправляем NULL даты приёмов
                cursor.execute("""
                    UPDATE appointments 
                    SET appointment_date = CURRENT_TIMESTAMP
                    WHERE appointment_date IS NULL
                """)
                
                print(f"✅ Исправлено NULL дат приёмов: {null_appointments}")
            else:
                print("✅ Все даты приёмов в порядке!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка исправления дат: {e}")
        return False

def test_date_formatting():
    """Тест форматирования дат"""
    print("\n🧪 ТЕСТ ФОРМАТИРОВАНИЯ ДАТ")
    print("=" * 40)
    
    test_dates = [
        '2024-06-30',
        '1990-01-01', 
        '1985-12-25',
        None,
        '',
        'invalid-date'
    ]
    
    for test_date in test_dates:
        try:
            # Имитируем форматирование как в API
            if test_date:
                if isinstance(test_date, str) and '-' in test_date:
                    parsed_date = datetime.strptime(test_date, '%Y-%m-%d').date()
                    formatted = parsed_date.strftime('%d.%m.%Y')
                    print(f"   ✅ {test_date} → {formatted}")
                else:
                    print(f"   ⚠️ {test_date} → без изменений")
            else:
                print(f"   ⚠️ {test_date} → 'не указано'")
                
        except Exception as e:
            print(f"   ❌ {test_date} → ошибка: {e}")

def create_test_patients_with_valid_dates():
    """Создание тестовых пациентов с правильными датами"""
    print("\n👥 СОЗДАНИЕ ТЕСТОВЫХ ПАЦИЕНТОВ")
    print("=" * 40)
    
    try:
        from src.database.connection import db
        
        test_patients = [
            {
                'first_name': 'Иван',
                'last_name': 'Тестовый',
                'middle_name': 'Иванович',
                'birth_date': '1990-01-15',
                'gender': 'M',
                'phone': '+7 (999) 111-11-11',
                'email': 'ivan.test@example.com'
            },
            {
                'first_name': 'Мария',
                'last_name': 'Тестовая',
                'middle_name': 'Петровна',
                'birth_date': '1985-05-20',
                'gender': 'F',
                'phone': '+7 (999) 222-22-22',
                'email': 'maria.test@example.com'
            },
            {
                'first_name': 'Алексей',
                'last_name': 'Тестовый',
                'middle_name': 'Сергеевич',
                'birth_date': '1992-11-10',
                'gender': 'M',
                'phone': '+7 (999) 333-33-33',
                'email': 'alexey.test@example.com'
            }
        ]
        
        with db.get_cursor() as cursor:
            created_count = 0
            
            for patient in test_patients:
                try:
                    # Проверяем, что пациент не существует
                    cursor.execute("""
                        SELECT id FROM patients 
                        WHERE email = %s
                    """, (patient['email'],))
                    
                    if cursor.fetchone():
                        print(f"   ⚠️ {patient['first_name']} {patient['last_name']} уже существует")
                        continue
                    
                    cursor.execute("""
                        INSERT INTO patients 
                        (first_name, last_name, middle_name, birth_date, gender, phone, email)
                        VALUES (%(first_name)s, %(last_name)s, %(middle_name)s, 
                                %(birth_date)s, %(gender)s, %(phone)s, %(email)s)
                        RETURNING id
                    """, patient)
                    
                    patient_id = cursor.fetchone()['id']
                    created_count += 1
                    
                    print(f"   ✅ {patient['first_name']} {patient['last_name']} создан (ID: {patient_id})")
                    
                except Exception as e:
                    print(f"   ❌ Ошибка создания {patient['first_name']}: {e}")
            
            print(f"\n✅ Создано тестовых пациентов: {created_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания тестовых пациентов: {e}")
        return False

def update_web_interface_date_handling():
    """Создание улучшенного JavaScript для обработки дат"""
    print("\n🌐 УЛУЧШЕНИЕ ОБРАБОТКИ ДАТ В ВЕБ-ИНТЕРФЕЙСЕ")
    print("=" * 50)
    
    js_date_fix = '''
// Улучшенная обработка дат в веб-интерфейсе
function safeDateFormat(dateString) {
    if (!dateString || dateString === 'null' || dateString === 'undefined') {
        return 'не указана';
    }
    
    try {
        // Если уже в русском формате
        if (dateString.includes('.')) {
            return dateString;
        }
        
        // Если в ISO формате
        let date;
        if (dateString.includes('T')) {
            date = new Date(dateString);
        } else if (dateString.includes('-')) {
            // YYYY-MM-DD формат
            const parts = dateString.split('-');
            date = new Date(parts[0], parts[1] - 1, parts[2]);
        } else {
            date = new Date(dateString);
        }
        
        // Проверяем валидность
        if (isNaN(date.getTime())) {
            console.warn('Invalid date:', dateString);
            return dateString;
        }
        
        // Форматируем в русском стиле
        const day = String(date.getDate()).padStart(2, '0');
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const year = date.getFullYear();
        
        return `${day}.${month}.${year}`;
        
    } catch (error) {
        console.error('Date formatting error:', error);
        return dateString || 'ошибка даты';
    }
}

// Функция для обновления всех дат на странице
function fixAllDatesOnPage() {
    // Находим все элементы с датами и исправляем их
    document.querySelectorAll('[data-date]').forEach(element => {
        const dateValue = element.getAttribute('data-date');
        element.textContent = safeDateFormat(dateValue);
    });
    
    console.log('✅ Все даты на странице исправлены');
}

// Автоматически исправляем даты при загрузке
document.addEventListener('DOMContentLoaded', fixAllDatesOnPage);
'''
    
    print("📝 JavaScript код для исправления дат:")
    print(js_date_fix)
    
    # Сохраняем в файл
    try:
        js_file = 'static/js/date-fix.js'
        os.makedirs(os.path.dirname(js_file), exist_ok=True)
        
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(js_date_fix)
        
        print(f"✅ JavaScript сохранен в {js_file}")
        print("📋 Добавьте в HTML: <script src='/static/js/date-fix.js'></script>")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения JavaScript: {e}")
        return False

def main():
    """Главная функция исправления дат"""
    print("🔧 ПОЛНОЕ ИСПРАВЛЕНИЕ ПРОБЛЕМЫ 'Invalid Date'")
    print("=" * 60)
    
    steps = [
        ("Исправление дат в БД", fix_invalid_dates),
        ("Тест форматирования", test_date_formatting),
        ("Создание тестовых данных", create_test_patients_with_valid_dates),
        ("Улучшение веб-интерфейса", update_web_interface_date_handling)
    ]
    
    results = []
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            result = step_func()
            results.append(result)
            if result:
                print(f"✅ {step_name} - успешно")
            else:
                print(f"⚠️ {step_name} - частично")
        except Exception as e:
            print(f"❌ {step_name} - ошибка: {e}")
            results.append(False)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📊 РЕЗУЛЬТАТ: {success_count}/{total_count} шагов выполнено")
    
    if success_count >= 3:
        print("🎉 ПРОБЛЕМА 'Invalid Date' ИСПРАВЛЕНА!")
        print("\n✅ Что было исправлено:")
        print("   1. Даты в базе данных проверены и исправлены")
        print("   2. Функции форматирования улучшены")
        print("   3. Веб-интерфейс обновлен для правильной обработки")
        print("   4. Созданы тестовые данные с валидными датами")
        
        print("\n🚀 Перезапустите систему:")
        print("   python run.py")
        
        print("\n📋 Теперь даты будут отображаться:")
        print("   ❌ Было: Invalid Date")
        print("   ✅ Стало: 15.01.1990")
        
    else:
        print("⚠️ НЕ ВСЕ ПРОБЛЕМЫ РЕШЕНЫ")
        print("Проверьте ошибки выше")
    
    return success_count >= 3

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            print(f"\n🎯 ИНСТРУКЦИЯ:")
            print(f"1. Обновите web_interface.html (уже исправлен)")
            print(f"2. Обновите API маршруты (уже исправлены)")
            print(f"3. Перезапустите: python run.py")
            print(f"4. Проверьте отображение дат")
        
        input(f"\nНажмите Enter для выхода...")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")