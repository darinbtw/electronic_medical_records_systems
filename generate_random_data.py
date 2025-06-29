# Создайте файл: generate_random_data.py

import random
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем корневую папку в path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.connection import db
from src.security.encryption import AESEncryption

class RussianDataGenerator:
    def __init__(self):
        # Мужские имена
        self.male_names = [
            'Александр', 'Андрей', 'Алексей', 'Антон', 'Артем', 'Владимир', 'Виктор',
            'Дмитрий', 'Денис', 'Евгений', 'Иван', 'Игорь', 'Кирилл', 'Максим',
            'Михаил', 'Николай', 'Олег', 'Павел', 'Петр', 'Роман', 'Сергей',
            'Станислав', 'Федор', 'Юрий', 'Ярослав'
        ]
        
        # Женские имена
        self.female_names = [
            'Анна', 'Анастасия', 'Алина', 'Александра', 'Валентина', 'Виктория',
            'Галина', 'Дарья', 'Елена', 'Екатерина', 'Жанна', 'Ирина', 'Кристина',
            'Людмила', 'Мария', 'Наталья', 'Ольга', 'Полина', 'Светлана', 'Татьяна',
            'Ульяна', 'Фаина', 'Юлия', 'Яна'
        ]
        
        # Фамилии
        self.surnames = [
            'Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Попов', 'Васильев',
            'Соколов', 'Лебедев', 'Козлов', 'Новиков', 'Морозов', 'Волков', 'Зайцев',
            'Павлов', 'Семенов', 'Голубев', 'Виноградов', 'Богданов', 'Воробьев',
            'Федоров', 'Михайлов', 'Беляев', 'Тарасов', 'Белов', 'Комаров', 'Орлов',
            'Киселев', 'Макаров', 'Андреев', 'Ковалев', 'Ильин', 'Гусев', 'Титов',
            'Кузьмин', 'Кудрявцев', 'Баранов', 'Куликов', 'Алексеев', 'Степанов'
        ]
        
        # Мужские отчества
        self.male_patronymics = [
            'Александрович', 'Андреевич', 'Алексеевич', 'Антонович', 'Артемович',
            'Владимирович', 'Викторович', 'Дмитриевич', 'Денисович', 'Евгеньевич',
            'Иванович', 'Игоревич', 'Кириллович', 'Максимович', 'Михайлович',
            'Николаевич', 'Олегович', 'Павлович', 'Петрович', 'Романович',
            'Сергеевич', 'Станиславович', 'Федорович', 'Юрьевич', 'Ярославович'
        ]
        
        # Женские отчества
        self.female_patronymics = [
            'Александровна', 'Андреевна', 'Алексеевна', 'Антоновна', 'Артемовна',
            'Владимировна', 'Викторовна', 'Дмитриевна', 'Денисовна', 'Евгеньевна',
            'Ивановна', 'Игоревна', 'Кирилловна', 'Максимовна', 'Михайловна',
            'Николаевна', 'Олеговна', 'Павловна', 'Петровна', 'Романовна',
            'Сергеевна', 'Станиславовна', 'Федоровна', 'Юрьевна', 'Ярославовна'
        ]
        
        # Специализации врачей
        self.specializations = [
            'Терапевт', 'Кардиолог', 'Невролог', 'Хирург', 'Педиатр', 'Гинеколог',
            'Офтальмолог', 'ЛОР', 'Дерматолог', 'Уролог', 'Эндокринолог',
            'Гастроэнтеролог', 'Онколог', 'Психиатр', 'Травматолог', 'Стоматолог'
        ]
        
        # Города
        self.cities = [
            'Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань',
            'Нижний Новгород', 'Челябинск', 'Самара', 'Омск', 'Ростов-на-Дону',
            'Уфа', 'Красноярск', 'Воронеж', 'Пермь', 'Волгоград'
        ]
        
        # Улицы
        self.streets = [
            'ул. Ленина', 'ул. Пушкина', 'ул. Гагарина', 'ул. Мира', 'ул. Победы',
            'ул. Советская', 'ул. Молодежная', 'ул. Центральная', 'ул. Садовая',
            'ул. Школьная', 'пр. Невский', 'пр. Ленинский', 'ул. Кирова',
            'ул. Комсомольская', 'ул. Рабочая'
        ]
        
        # Диагнозы
        self.diagnoses = [
            'ОРВИ легкой степени тяжести',
            'Артериальная гипертензия I степени',
            'Хронический гастрит в стадии обострения', 
            'Остеохондроз поясничного отдела позвоночника',
            'Аллергический ринит',
            'Хронический тонзиллит',
            'Бронхиальная астма легкой степени',
            'Железодефицитная анемия легкой степени',
            'Вегето-сосудистая дистония',
            'Синдром раздраженного кишечника'
        ]
        
        # Жалобы
        self.complaints = [
            'Головная боль, общая слабость',
            'Повышенная температура, кашель',
            'Боль в горле, насморк',
            'Боль в спине, ограничение движений',
            'Головокружение, тошнота',
            'Боль в животе, изжога',
            'Одышка при физической нагрузке',
            'Бессонница, повышенная утомляемость',
            'Заложенность носа, чихание',
            'Боль в грудной клетке'
        ]
        
        # Препараты
        self.medications = [
            'Парацетамол', 'Ибупрофен', 'Амоксициллин', 'Цитрамон', 'АЦЦ',
            'Супрастин', 'Но-шпа', 'Анальгин', 'Аспирин', 'Лоратадин',
            'Нурофен', 'Фервекс', 'Мукалтин', 'Валидол', 'Корвалол'
        ]
        
        self.encryption = AESEncryption()
    
    def generate_phone(self):
        """Генерация случайного телефона"""
        area_code = random.randint(900, 999)
        number = random.randint(1000000, 9999999)
        return f"+7 ({area_code}) {str(number)[:3]}-{str(number)[3:5]}-{str(number)[5:]}"
    
    def generate_email(self, first_name, last_name, domain_type='personal'):
        """Генерация email"""
        domains = {
            'personal': ['mail.ru', 'gmail.com', 'yandex.ru', 'rambler.ru', 'outlook.com'],
            'medical': ['clinic.ru', 'hospital.ru', 'med.ru', 'health.ru']
        }
        
        domain = random.choice(domains[domain_type])
        username = f"{first_name.lower()}.{last_name.lower()}"
        suffix = random.randint(1, 999)
        
        return f"{username}{suffix}@{domain}"
    
    def generate_address(self):
        """Генерация адреса"""
        city = random.choice(self.cities)
        street = random.choice(self.streets)
        house = random.randint(1, 150)
        apartment = random.randint(1, 200) if random.random() > 0.3 else None
        
        address = f"г. {city}, {street}, д. {house}"
        if apartment:
            address += f", кв. {apartment}"
        
        return address
    
    def generate_birth_date(self):
        """Генерация даты рождения"""
        start_date = datetime(1950, 1, 1)
        end_date = datetime(2005, 12, 31)
        
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        
        return start_date + timedelta(days=random_days)
    
    def generate_person(self, gender=None):
        """Генерация данных человека"""
        if gender is None:
            gender = random.choice(['M', 'F'])
        
        if gender == 'M':
            first_name = random.choice(self.male_names)
            patronymic = random.choice(self.male_patronymics)
        else:
            first_name = random.choice(self.female_names)
            patronymic = random.choice(self.female_patronymics)
        
        # Для женщин добавляем окончание -а к фамилии
        surname = random.choice(self.surnames)
        if gender == 'F' and not surname.endswith('а'):
            surname += 'а'
        
        return {
            'first_name': first_name,
            'last_name': surname,
            'middle_name': patronymic,
            'gender': gender,
            'birth_date': self.generate_birth_date(),
            'phone': self.generate_phone(),
            'address': self.generate_address()
        }

def clear_all_data():
    """Очистка всех таблиц"""
    print("Очистка существующих данных...")
    
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                TRUNCATE TABLE prescriptions, medical_records, appointments, doctors, patients 
                RESTART IDENTITY CASCADE;
            """)
            conn.commit()
        print("✅ Данные очищены")
        return True
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")
        return False

def generate_doctors(generator, count=20):
    """Генерация врачей"""
    print(f"Генерация {count} врачей...")
    
    doctors = []
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for i in range(count):
                person = generator.generate_person()
                specialization = random.choice(generator.specializations)
                email = generator.generate_email(person['first_name'], person['last_name'], 'medical')
                license_number = f"ЛИЦ-{datetime.now().year}-{5000 + i:04d}"
                
                cursor.execute("""
                    INSERT INTO doctors (first_name, last_name, middle_name, specialization, 
                                       license_number, phone, email)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    person['first_name'], person['last_name'], person['middle_name'],
                    specialization, license_number, person['phone'], email
                ))
                
                doctor_id = cursor.fetchone()[0]
                doctors.append(doctor_id)
            
            conn.commit()
        
        print(f"✅ Создано {len(doctors)} врачей")
        return doctors
    except Exception as e:
        print(f"❌ Ошибка создания врачей: {e}")
        return []

def generate_patients(generator, count=100):
    """Генерация пациентов"""
    print(f"Генерация {count} пациентов...")
    
    patients = []
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for i in range(count):
                person = generator.generate_person()
                email = generator.generate_email(person['first_name'], person['last_name'])
                
                cursor.execute("""
                    INSERT INTO patients (first_name, last_name, middle_name, birth_date,
                                        gender, phone, email, address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    person['first_name'], person['last_name'], person['middle_name'],
                    person['birth_date'], person['gender'], person['phone'], email, person['address']
                ))
                
                patient_id = cursor.fetchone()[0]
                patients.append(patient_id)
            
            conn.commit()
        
        print(f"✅ Создано {len(patients)} пациентов")
        return patients
    except Exception as e:
        print(f"❌ Ошибка создания пациентов: {e}")
        return []

def generate_appointments(generator, doctor_ids, patient_ids, count=200):
    """Генерация приемов"""
    print(f"Генерация {count} приемов...")
    
    appointments = []
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for i in range(count):
                patient_id = random.choice(patient_ids)
                doctor_id = random.choice(doctor_ids)
                
                # Случайная дата за последний год
                days_ago = random.randint(1, 365)
                appointment_date = datetime.now() - timedelta(days=days_ago)
                
                # Случайное время в рабочие часы
                hour = random.randint(9, 17)
                minute = random.choice([0, 10, 20, 30, 40, 50])
                appointment_date = appointment_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                status = random.choices(['completed', 'scheduled', 'cancelled'], weights=[70, 20, 10])[0]
                
                cursor.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (patient_id, doctor_id, appointment_date, status))
                
                appointment_id = cursor.fetchone()[0]
                appointments.append((appointment_id, status))
            
            conn.commit()
        
        print(f"✅ Создано {len(appointments)} приемов")
        return appointments
    except Exception as e:
        print(f"❌ Ошибка создания приемов: {e}")
        return []

def generate_medical_records(generator, appointments):
    """Генерация медицинских записей"""
    completed_appointments = [app for app in appointments if app[1] == 'completed']
    
    if not completed_appointments:
        print("⚠️ Нет завершенных приемов для медкарт")
        return []
    
    print(f"Генерация медкарт для {len(completed_appointments)} завершенных приемов...")
    
    records = []
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            for appointment_id, _ in completed_appointments:
                diagnosis = random.choice(generator.diagnoses)
                complaints = random.choice(generator.complaints)
                
                # Генерируем результаты осмотра
                temp = round(36.0 + random.random() * 3, 1)
                pressure_high = random.randint(110, 150)
                pressure_low = random.randint(70, 90)
                pulse = random.randint(60, 100)
                
                examination = f"Температура {temp}°C, давление {pressure_high}/{pressure_low} мм.рт.ст., пульс {pulse} уд/мин"
                
                # Шифруем диагноз
                encrypted_diagnosis, iv = generator.encryption.encrypt(diagnosis)
                
                cursor.execute("""
                    INSERT INTO medical_records (appointment_id, diagnosis_encrypted, diagnosis_iv,
                                               complaints, examination_results)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (appointment_id, encrypted_diagnosis, iv, complaints, examination))
                
                record_id = cursor.fetchone()[0]
                
                # Добавляем 1-3 назначения
                prescription_count = random.randint(1, 3)
                for _ in range(prescription_count):
                    medication = random.choice(generator.medications)
                    dosage = random.choice(['500мг', '200мг', '1000мг', '250мг', '100мг'])
                    frequency = random.choice(['1 раз в день', '2 раза в день', '3 раза в день', 'по необходимости'])
                    duration = random.choice(['3 дня', '5 дней', '7 дней', '10 дней', '14 дней'])
                    
                    cursor.execute("""
                        INSERT INTO prescriptions (medical_record_id, medication_name, dosage, frequency, duration)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (record_id, medication, dosage, frequency, duration))
                
                records.append(record_id)
            
            conn.commit()
        
        print(f"✅ Создано {len(records)} медицинских записей")
        return records
    except Exception as e:
        print(f"❌ Ошибка создания медкарт: {e}")
        return []

def main():
    print("🏥 ГЕНЕРАТОР СЛУЧАЙНЫХ МЕДИЦИНСКИХ ДАННЫХ")
    print("=" * 50)
    
    # Проверяем подключение
    if not db.test_connection():
        print("❌ Нет подключения к БД!")
        return False
    
    generator = RussianDataGenerator()
    
    print("\nВыберите количество записей:")
    print("1. Мало данных (10 врачей, 50 пациентов, 100 приемов)")
    print("2. Средне данных (20 врачей, 100 пациентов, 200 приемов)")
    print("3. Много данных (50 врачей, 500 пациентов, 1000 приемов)")
    
    choice = input("Введите номер (1-3): ").strip()
    
    if choice == '1':
        doctors_count, patients_count, appointments_count = 10, 50, 100
    elif choice == '2':
        doctors_count, patients_count, appointments_count = 20, 100, 200
    elif choice == '3':
        doctors_count, patients_count, appointments_count = 50, 500, 1000
    else:
        doctors_count, patients_count, appointments_count = 20, 100, 200
        print("Используются средние значения")
    
    print(f"\nБудет создано:")
    print(f"  Врачей: {doctors_count}")
    print(f"  Пациентов: {patients_count}")
    print(f"  Приемов: {appointments_count}")
    
    confirm = input("\nПродолжить? (y/n): ").lower()
    if confirm != 'y':
        print("Отменено")
        return False
    
    # Очищаем данные
    if not clear_all_data():
        return False
    
    # Генерируем данные
    print("\n" + "="*50)
    
    doctor_ids = generate_doctors(generator, doctors_count)
    if not doctor_ids:
        return False
    
    patient_ids = generate_patients(generator, patients_count)
    if not patient_ids:
        return False
    
    appointments = generate_appointments(generator, doctor_ids, patient_ids, appointments_count)
    if not appointments:
        return False
    
    medical_records = generate_medical_records(generator, appointments)
    
    # Финальная статистика
    print("\n" + "="*50)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM doctors")
            doctors = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM patients")
            patients = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM appointments")
            appointments_total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM medical_records")
            records = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM prescriptions")
            prescriptions = cursor.fetchone()[0]
            
            print(f"  ✅ Врачей: {doctors}")
            print(f"  ✅ Пациентов: {patients}")
            print(f"  ✅ Приемов: {appointments_total}")
            print(f"  ✅ Медкарт: {records}")
            print(f"  ✅ Назначений: {prescriptions}")
            
            print(f"\n🎉 ГЕНЕРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
            print(f"🚀 Запускайте систему: python run.py")
            
            return True
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        input("\nНажмите Enter для выхода...")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        input("Нажмите Enter...")
        sys.exit(1)