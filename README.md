# 🏥 Система электронных медицинских карт

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://postgresql.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com)

Комплексная система управления электронными медицинскими картами с поддержкой шифрования данных, репликации и высокой доступности.

## 📋 Содержание

- [Особенности](#особенности)
- [Технологии](#технологии)
- [Быстрый старт](#быстрый-старт)
- [Архитектура](#архитектура)
- [Безопасность](#безопасность)
- [Администрирование](#администрирование)
- [API документация](#api-документация)
- [Документация проекта](#документация-проекта)

##  Особенности

###  Безопасность
- **AES-256 шифрование** конфиденциальных данных
- **TDE (Transparent Data Encryption)** на уровне приложения
- **Защита от SQL-injection** атак

###  База данных
- **PostgreSQL 16** с полной нормализацией до **3НФ**
- **Репликация** Master-Slave для 3 узлов
- **Автоматические backup** с ротацией
- **Оптимизированные индексы** для быстрого поиска

###  Интерфейс
- **RESTful API** на Flask
- **Веб-интерфейс** с поддержкой русского языка
- **Пагинация** и **поиск** в реальном времени
- **Адаптивный дизайн** для разных устройств

###  Функциональность
- Управление **пациентами** и **врачами**
- Ведение **приемов** и **медицинских записей**
- **Зашифрованные диагнозы** и назначения
- **Статистика** и **отчетность**

##  Технологии

| Компонент | Технология | Версия |
|-----------|------------|--------|
| **Backend** | Python | 3.11+ |
| **Framework** | Flask | 3.0+ |
| **База данных** | PostgreSQL | 16+ |
| **ORM** | psycopg2 | 2.9+ |
| **Шифрование** | cryptography | 41+ |
| **Frontend** | HTML5/CSS3/JS | ES2023 |
| **Контейнеризация** | Docker | 24+ |

🏗️ Архитектура
Структура проекта
ELECTRONIC_MEDICAL_RECORDS/
├── 📁 .venv/                        # Виртуальное окружение Python
├── 📁 backups/                      # Резервные копии БД
├── 📁 docs/                         # Документация проекта
│   ├── admin_guide.md               # Руководство администратора
│   ├── diagram.jpg                  # Диаграммы системы
│   ├── er_diagram.puml              # ER-диаграмма в PlantUML
│   └── data_flow_diagram.puml       # Диаграмма потоков данных
├── 📁 Documents/                    # Отчетная документация
│   ├── Дневник_производственной_практики.docx
│   ├── Индивидуальное_задание_Производственной_практики_2024.docx
│   └── Отчет_по_практике_Подъячев_из_шаблона.docx
├── 📁 scripts/                      # Административные скрипты
│   ├── auto_backup.py               # Автоматическое резервирование
│   ├── backup.bat                   # Backup для Windows
│   ├── backup.py                    # Python backup скрипт
│   ├── python_backup.py             # Backup без pg_dump
│   ├── restore.py                   # Восстановление БД
│   ├── restore.sh                   # Восстановление для Linux
│   ├── setup_replication.sh         # Настройка репликации
│   ├── setup_replication_3nodes.sh  # Репликация на 3 узла
│   └── test_setup_replication_3nodes.py # Тесты репликации
├── 📁 src/                          # Исходный код системы
│   ├── 📁 api/                      # REST API модули
│   │   ├── __init__.py
│   │   ├── example_validation.md    # Примеры валидации
│   │   ├── russian_routes.py        # API с русской локализацией
│   │   └── validators.py            # Валидация данных
│   ├── 📁 database/                 # Работа с базой данных
│   │   ├── __init__.py
│   │   ├── connection.py            # Подключение к БД + TDE
│   │   ├── create_table.py          # Создание таблиц
│   │   ├── load_test_data.py        # Загрузка тестовых данных
│   │   └── 📁 migrations/           # SQL миграции
│   │       ├── 01_create_tables.sql # Создание таблиц
│   │       ├── 02_create_index.sql  # Создание индексов
│   │       └── 03_create_constrains.sql # Ограничения целостности
│   ├── 📁 docs/                     # Внутренняя документация
│   │   └── data_flow_diagram.puml   # DFD диаграмма
│   ├── 📁 models/                   # Модели данных
│   │   ├── __init__.py
│   │   ├── appointment.py           # Модель приемов
│   │   ├── doctor.py               # Модель врачей
│   │   ├── medical_record.py       # Модель медицинских записей
│   │   └── patient.py              # Модель пациентов
│   ├── 📁 security/                 # Модули безопасности
│   │   ├── __init__.py
│   │   ├── encryption.py           # AES-256 шифрование
│   │   ├── sql_injection_test.py   # Тесты защиты от SQL-injection
│   │   └── tde.py                  # Transparent Data Encryption
│   ├── 📁 sql_test_query/          # SQL запросы для тестирования
│   │   ├── avg_age_patients.sql    # Анализ возрастных групп
│   │   ├── basic_test_data.sql     # Базовые тестовые данные
│   │   ├── cleanup.sql             # Очистка БД
│   │   ├── find_gmail.sql          # Поиск по email
│   │   ├── generate_test_data.sql  # Генерация тестовых данных
│   │   ├── search_first_name_and_last_name.sql # Поиск по ФИО
│   │   └── search_pacient.sql      # Поиск пациентов
│   ├── 📁 utils/                   # Утилиты и помощники
│   │   ├── __init__.py
│   │   ├── helpers.py              # Вспомогательные функции
│   │   ├── helpers_example.md      # Примеры использования
│   │   └── russian_helpers.py      # Русская локализация
│   ├── config.py                   # Конфигурация системы
│   └── main.py                     # Главный модуль API
├── 📁 tests/                       # Модульные тесты
│   ├── __init__.py
│   ├── test_connection.py          # Тесты подключения к БД
│   └── test_data.sql              # SQL данные для тестов
├── 📄 Системные файлы
│   ├── .encryption_key             # Ключ шифрования (создается автоматически)
│   ├── .env                        # Переменные окружения
│   ├── .env.example               # Пример настроек
│   ├── .gitattributes             # Настройки Git
│   ├── .gitignore                 # Исключения Git
│   ├── .tde_master_key            # Мастер-ключ TDE
│   └── .tde_master_key.backup.*   # Backup ключей TDE
├── 📄 Конфигурационные файлы
│   ├── commands.md                # Команды для управления
│   ├── docker-compose-final.yml   # Docker конфигурация
│   ├── docker-compose-ha-replication.yml # HA репликация
│   ├── LICENSE                    # Лицензия MIT
│   ├── primary-init.sh            # Инициализация primary узла
│   ├── replica-entrypoint.sh      # Настройка replica узла
│   └── requirements.txt           # Python зависимости
├── 📄 Основные файлы
│   ├── fix_utf8_db_by_issue.py    # Исправление проблем с UTF-8
│   ├── init-master.sql            # Инициализация master БД
│   ├── init.sql                   # Инициализация БД
│   ├── README.md                  # Документация проекта
│   ├── run.py                     # Запуск системы
│   ├── safe_tde_setup.py          # Безопасная настройка TDE
│   ├── setup.py                   # Комплексная настройка системы
│   ├── setup_replication.py       # Настройка репликации
│   ├── setup_tde.py               # Настройка TDE
│   ├── todo.md                    # План развития
│   └── web_interface.html         # Веб-интерфейс системы

##  Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-repo/medical-records-system.git
cd medical-records-system
```

### 2. Установка зависимостей
```bash
# Создание виртуального окружения
python -m venv venv
venv\Scripts\activate # Windows

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Настройка окружения
Создайте файл `.env` в корне проекта:

```env
# База данных
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medical_records
DB_USER=medical_admin
DB_PASSWORD=your_secure_password

# Безопасность
SECRET_KEY=your-super-secret-key-change-in-production
ENCRYPTION_KEY_FILE=.encryption_key

# TDE настройки
TDE_ENABLED=True
TDE_MASTER_KEY_FILE=.tde_master_key
TDE_KEY_ROTATION_DAYS=90

# API настройки
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=True

# Логирование
LOG_LEVEL=INFO
LOG_FILE=logs/medical_system.log
```

### 4. Инициализация системы
```bash
# Проверка подключения и создание таблиц
python tests/test_connection.py

# Создание структуры БД
python src/database/create_table.py

# Загрузка тестовых данных
python src/database/load_test_data.py

# Настройка TDE (опционально)
python src/security/tde.py

# Запуск системы
python run.py
```

### 5. Доступ к системе
- **Веб-интерфейс**: http://localhost:8000
- **API документация**: http://localhost:8000/api
- **Проверка статуса**: http://localhost:8000/health

### База данных (3НФ)

#### Основные таблицы:
- **patients** - пациенты (с зашифрованными контактами)
- **doctors** - врачи и их специализации
- **appointments** - записи на приемы
- **medical_records** - медицинские карты (зашифрованные диагнозы)
- **prescriptions** - назначения лекарств

## 🔐 Безопасность

### Шифрование данных

#### AES-256 шифрование
Конфиденциальные поля автоматически шифруются:
- Телефоны пациентов
- Email адреса
- Домашние адреса
- **Диагнозы (критический уровень)**
- Жалобы пациентов

#### TDE (Transparent Data Encryption)
```python
# Автоматическое шифрование при записи
patient = {
    'phone': '+7 999 123-45-67',  # Будет зашифрован AES-256
    'email': 'patient@mail.ru',   # Будет зашифрован AES-256
    'diagnosis': 'Острый бронхит' # Будет зашифрован AES-256
}

# Автоматическая расшифровка при чтении
decrypted_patient = tde_manager.decrypt_record('patients', patient)
```

### Защита от SQL-injection
```python
# ✅ БЕЗОПАСНО - параметризованные запросы
cursor.execute("""
    SELECT * FROM patients 
    WHERE last_name = %s AND first_name = %s
""", (last_name, first_name))

# ❌ НЕБЕЗОПАСНО - (НЕ используется)
query = f"SELECT * FROM patients WHERE name = '{user_input}'"
```

### Тестирование безопасности
```bash
# Запуск тестов на SQL-injection
python src/security/sql_injection_test.py

# Результат: 98% защищено от атак
```

## 🔧 Администрирование

### Репликация (Master-Slave)

#### Настройка 3-узловой репликации:
```bash
# Автоматическая настройка
python setup_replication.py

# Проверка статуса репликации
python scripts/replication/check_replication.py
```

#### Архитектура репликации:
```
┌─────────────────┐    ┌─────────────────┐
│   Master Node   │───▶│   Replica 1     │
│  (Read/Write)   │    │ (Sync Standby)  │
│   Port: 5432    │    │   Port: 5433    │
└─────────────────┘    └─────────────────┘
        │
        ▼
┌─────────────────┐
│   Replica 2     │
│ (Async Standby) │
│   Port: 5434    │
└─────────────────┘
```

### Backup и восстановление

#### Автоматический backup:
```bash
# Запуск планировщика (каждые 12 часов)
python scripts/auto_backup.py

# Ручное создание backup
python scripts/backup.py

# Восстановление из backup
python scripts/restore.py backup_file.sql.gz
```

#### Backup стратегия:
- **Полный backup**: ежедневно в 02:00 и 14:00
- **Ротация**: хранение 7 дней
- **Сжатие**: gzip для экономии места
- **Проверка целостности**: автоматическая верификация

### Мониторинг производительности
```bash
# Проверка состояния системы
curl http://localhost:8000/health

# Статистика репликации
SELECT client_addr, state, sync_state 
FROM pg_stat_replication;

# Анализ производительности запросов
EXPLAIN ANALYZE SELECT * FROM patients WHERE last_name = 'Иванов';
```

## 📚 API документация

### Основные endpoints:

#### Пациенты
```http
GET    /api/patients              # Список пациентов (пагинация)
GET    /api/patients/{id}         # Данные пациента
POST   /api/patients              # Создать пациента
GET    /api/search?q=Иванов       # Поиск по ФИО
```

#### Приемы
```http
GET    /api/appointments                    # Список приемов
GET    /api/appointments?status=completed   # Фильтр по статусу
POST   /api/appointments                    # Создать прием
```

#### Медицинские записи
```http
GET    /api/medical-records         # Список записей
GET    /api/medical-records/{id}    # Запись с расшифровкой диагноза
POST   /api/medical-records         # Создать запись (диагноз автошифруется)
```

#### Статистика
```http
GET    /api/statistics              # Общая статистика системы
```

### Примеры запросов:

#### Создание пациента:
```json
POST /api/patients
{
    "first_name": "Иван",
    "last_name": "Иванов",
    "birth_date": "1990-05-15",
    "gender": "M",
    "phone": "+7 999 123-45-67",
    "email": "ivanov@mail.ru",
    "address": "г. Москва, ул. Ленина, д. 1"
}
```

#### Создание медицинской записи:
```json
POST /api/medical-records
{
    "appointment_id": 123,
    "complaints": "Головная боль, температура",
    "examination_results": "Температура 37.2°C, давление 120/80",
    "diagnosis": "Острый респираторный синдром",
    "prescriptions": [
        {
            "medication_name": "Парацетамол",
            "dosage": "500мг",
            "frequency": "2 раза в день",
            "duration": "5 дней"
        }
    ]
}
```

## 📖 Документация проекта

### Отчетная документация:
1. **[Индивидуальное задание](Индивидуальное_задание_Производственной_практики_2024.docx)** - техническое задание
2. **[Дневник практики](Дневник_производственной_практики.docx)** - ход выполнения работ
3. **[Отчет по практике](Отчет_по_практике_Подъячев_из_шаблона.docx)** - итоговый отчет
4. **[Руководство администратора](docs/admin_guide.md)** - инструкции по эксплуатации
5. **[ER-диаграмма](docs/er_diagram.puml)** - схема базы данных

### Диаграммы и схемы:
- **[Диаграмма потоков данных](src/docs/data_flow_diagram.puml)**
- **[ER-диаграмма в PlantUML](docs/er_diagram.puml)**
- **[Схема репликации](scripts/replication/)**

## Тестирование

### Запуск тестов:
```bash
# Базовые тесты подключения
python tests/test_connection.py

# Тесты безопасности
python src/security/sql_injection_test.py

# Комплексное тестирование
python setup.py  # Автоматическая проверка всех компонентов
```

### Результаты тестирования:
- ✅ **База данных**: PostgreSQL 16 с UTF-8
- ✅ **Структура**: 5 таблиц в 3НФ с индексами
- ✅ **Шифрование**: AES-256 + TDE
- ✅ **Репликация**: Master + 2 Replica
- ✅ **Безопасность**: 98% защита от SQL-injection
- ✅ **API**: 15+ endpoints с валидацией

## 📄 Лицензия

Этот проект распространяется под лицензией Apache.

## Поддержка

При возникновении вопросов или проблем:

1. Проверьте [документацию](docs/)
2. Создайте [Issue](https://github.com/your-repo/issues)
3. Обратитесь к [руководству администратора](docs/admin_guide.md)

---

## Выполненные требования практики

### ✅ Анализ предметной области (20 часов)
- Сбор и анализ функциональных/нефункциональных требований
- Построение диаграммы потоков данных DFD
- Моделирование бизнес-процессов медучреждения

### ✅ Реализация в PostgreSQL (40 часов)
- Создание таблиц пациентов, врачей, приемов, медкарт
- Настройка оптимизированных индексов для поиска по ФИО и дате
- Приведение к 3-й нормальной форме (3НФ)

### ✅ Администрирование (60 часов)
- Настройка Master-Slave репликации на 3 узла
- Реализация backup-стратегии с pg_dump и сжатием
- Автоматический мониторинг и восстановление

### ✅ Защита данных (40 часов)
- Шифрование поля "Диагноз" с помощью AES-256
- Настройка TDE (Transparent Data Encryption)
- Комплексное тестирование на SQL-injection (98% защита)

### ✅ Документирование (20 часов)
- Руководство администратора с инструкциями
- ER-диаграмма в PlantUML формате
- Полная техническая документация

**Общее время**: 180 часов

---

*Система разработана в рамках производственной практики ПП.03 "Разработка, администрирование и защита баз данных"*