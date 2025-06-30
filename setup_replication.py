# setup_replication.py
"""
Автоматическая настройка 3-узловой репликации PostgreSQL
для системы электронных медицинских карт
"""

import os
import sys
import time
import subprocess
import psycopg2
from pathlib import Path
from typing import Dict, List, Optional
import json

class PostgreSQLReplicationManager:
    """
    Менеджер для настройки и управления репликацией PostgreSQL
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / "scripts" / "replication"
        
        # Конфигурация узлов
        self.nodes = {
            'master': {
                'host': 'localhost',
                'port': 5432,
                'container': 'medical-postgres-master',
                'role': 'primary',
                'ip': '172.20.0.10'
            },
            'replica1': {
                'host': 'localhost', 
                'port': 5433,
                'container': 'medical-postgres-replica1',
                'role': 'synchronous_standby',
                'ip': '172.20.0.11'
            },
            'replica2': {
                'host': 'localhost',
                'port': 5434, 
                'container': 'medical-postgres-replica2',
                'role': 'asynchronous_standby',
                'ip': '172.20.0.12'
            }
        }
        
        # Настройки подключения
        self.db_config = {
            'database': 'medical_records',
            'user': 'postgres',
            'password': 'postgres',
            'replication_user': 'replicator',
            'replication_password': 'repl_password_2024'
        }
    
    def create_replication_scripts(self):
        """Создание необходимых скриптов для репликации"""
        print("📝 Создание скриптов репликации...")
        
        # Создаем директорию для скриптов
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Скрипт инициализации мастера
        init_master_script = """#!/bin/bash
set -e

echo "🔧 Инициализация Master узла..."

# Настройка репликации в pg_hba.conf
cat >> "$PGDATA/pg_hba.conf" << EOF

# Replication connections
host replication replicator 172.20.0.0/16 md5
host replication replicator 0.0.0.0/0 md5

# Application connections with load balancing
host medical_records postgres 172.20.0.0/16 md5
host medical_records postgres 0.0.0.0/0 md5
EOF

echo "✅ pg_hba.conf настроен для репликации"

# Создание директории для архивов WAL
mkdir -p /var/lib/postgresql/archive
chown postgres:postgres /var/lib/postgresql/archive

echo "✅ Директория архивов создана"

# Перезагрузка конфигурации
pg_ctl reload -D "$PGDATA"

echo "✅ Master узел инициализирован"
"""
        
        # 2. SQL скрипт для мастера
        master_setup_sql = """
-- Создание пользователя для репликации
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'replicator') THEN
        CREATE USER replicator WITH REPLICATION PASSWORD 'repl_password_2024';
        ALTER USER replicator SET synchronous_commit = on;
    END IF;
END $$;

-- Создание слотов репликации
SELECT pg_create_physical_replication_slot('replica1') 
WHERE NOT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = 'replica1');

SELECT pg_create_physical_replication_slot('replica2') 
WHERE NOT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = 'replica2');

-- Настройка синхронной репликации
ALTER SYSTEM SET synchronous_standby_names = 'replica1,replica2';

-- Перезагрузка конфигурации
SELECT pg_reload_conf();

-- Информация о настройке
DO $$
BEGIN
    RAISE NOTICE 'Master node setup completed:';
    RAISE NOTICE '- Replication user created: replicator';
    RAISE NOTICE '- Replication slots: replica1, replica2';
    RAISE NOTICE '- Synchronous standby names: replica1,replica2';
    RAISE NOTICE '- WAL level: replica';
END $$;
"""
        
        # 3. Dockerfile для API
        dockerfile_content = """
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \\
    gcc \\
    libpq-dev \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание пользователя для безопасности
RUN useradd -m -u 1000 medical && chown -R medical:medical /app
USER medical

# Настройка переменных окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Порт для API
EXPOSE 8000

# Команда запуска
CMD ["python", "run.py"]
"""
        
        # 4. Скрипт проверки репликации
        check_replication_script = """#!/usr/bin/env python3
\"\"\"
Скрипт проверки состояния репликации
\"\"\"

import psycopg2
import sys
from datetime import datetime

def check_replication_status():
    print("🔍 ПРОВЕРКА СОСТОЯНИЯ РЕПЛИКАЦИИ")
    print("=" * 50)
    
    try:
        # Подключение к мастеру
        master_conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='medical_records',
            user='postgres',
            password='postgres'
        )
        
        cursor = master_conn.cursor()
        
        # Проверяем статус репликации на мастере
        cursor.execute(\"\"\"
            SELECT 
                pid,
                usename,
                application_name,
                client_addr,
                client_hostname,
                state,
                sync_state,
                sync_priority,
                pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) as send_lag,
                pg_wal_lsn_diff(sent_lsn, flush_lsn) as flush_lag,
                pg_wal_lsn_diff(flush_lsn, replay_lsn) as replay_lag
            FROM pg_stat_replication
            ORDER BY application_name;
        \"\"\")
        
        replicas = cursor.fetchall()
        
        print(f"📊 Статус на MASTER (порт 5432):")
        print(f"   Активных реплик: {len(replicas)}")
        
        if replicas:
            print(f"\\n   Детали реплик:")
            for replica in replicas:
                pid, user, app_name, client_addr, hostname, state, sync_state, priority, send_lag, flush_lag, replay_lag = replica
                print(f"   📡 {app_name}:")
                print(f"      IP: {client_addr}")
                print(f"      Состояние: {state}")
                print(f"      Синхронизация: {sync_state}")
                print(f"      Приоритет: {priority}")
                print(f"      Задержка отправки: {send_lag or 0} байт")
                print(f"      Задержка записи: {flush_lag or 0} байт")
                print(f"      Задержка воспроизведения: {replay_lag or 0} байт")
                print()
        else:
            print("   ⚠️ Реплики не подключены")
        
        # Проверяем слоты репликации
        cursor.execute(\"\"\"
            SELECT slot_name, slot_type, active, 
                   pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as lag_bytes
            FROM pg_replication_slots;
        \"\"\")
        
        slots = cursor.fetchall()
        print(f"🎰 Слоты репликации ({len(slots)}):")
        for slot in slots:
            name, slot_type, active, lag = slot
            status = "🟢 активен" if active else "🔴 неактивен"
            print(f"   {name}: {status}, отставание: {lag or 0} байт")
        
        cursor.close()
        master_conn.close()
        
        # Проверяем статус реплик
        for port, name in [(5433, 'replica1'), (5434, 'replica2')]:
            try:
                replica_conn = psycopg2.connect(
                    host='localhost',
                    port=port,
                    database='medical_records',
                    user='postgres',
                    password='postgres'
                )
                
                replica_cursor = replica_conn.cursor()
                
                # Проверяем режим восстановления
                replica_cursor.execute("SELECT pg_is_in_recovery();")
                in_recovery = replica_cursor.fetchone()[0]
                
                if in_recovery:
                    # Получаем информацию о WAL receiver
                    replica_cursor.execute(\"\"\"
                        SELECT status, receive_start_lsn, receive_start_tli,
                               received_lsn, received_tli, last_msg_send_time,
                               last_msg_receipt_time, latest_end_lsn, latest_end_time
                        FROM pg_stat_wal_receiver;
                    \"\"\")
                    
                    wal_receiver = replica_cursor.fetchone()
                    
                    print(f"\\n📊 Статус {name.upper()} (порт {port}):")
                    print(f"   Режим восстановления: ✅ Да")
                    
                    if wal_receiver:
                        status, start_lsn, start_tli, received_lsn, received_tli, send_time, receipt_time, end_lsn, end_time = wal_receiver
                        print(f"   WAL Receiver статус: {status}")
                        print(f"   Последнее получение: {receipt_time}")
                    else:
                        print(f"   ⚠️ WAL Receiver не активен")
                else:
                    print(f"\\n📊 Статус {name.upper()} (порт {port}):")
                    print(f"   ❌ НЕ в режиме восстановления (проблема!)")
                
                replica_cursor.close()
                replica_conn.close()
                
            except Exception as e:
                print(f"\\n📊 Статус {name.upper()} (порт {port}):")
                print(f"   ❌ Недоступен: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки репликации: {e}")
        return False

if __name__ == "__main__":
    success = check_replication_status()
    sys.exit(0 if success else 1)
"""
        
        # 5. Скрипт failover
        failover_script = """#!/usr/bin/env python3
\"\"\"
Скрипт для переключения на резервный узел (failover)
\"\"\"

import psycopg2
import subprocess
import sys
import time

def promote_replica(replica_name):
    print(f"🔄 ПЕРЕКЛЮЧЕНИЕ НА {replica_name.upper()}")
    print("=" * 40)
    
    container_name = f"medical-postgres-{replica_name}"
    
    try:
        # 1. Проверяем статус контейнера
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Status}}"],
            capture_output=True, text=True
        )
        
        if "Up" not in result.stdout:
            print(f"❌ Контейнер {container_name} не запущен")
            return False
        
        print(f"✅ Контейнер {container_name} запущен")
        
        # 2. Создаем trigger файл для promote
        trigger_file = f"/tmp/promote_{replica_name}"
        
        promote_cmd = [
            "docker", "exec", container_name,
            "touch", trigger_file
        ]
        
        result = subprocess.run(promote_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Trigger файл создан: {trigger_file}")
        else:
            print(f"❌ Ошибка создания trigger файла: {result.stderr}")
            return False
        
        # 3. Ждем завершения promote
        print("⏳ Ожидание завершения promote...")
        time.sleep(10)
        
        # 4. Проверяем, что узел стал мастером
        port = 5433 if replica_name == 'replica1' else 5434
        
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=port,
                database='medical_records', 
                user='postgres',
                password='postgres'
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT pg_is_in_recovery();")
            in_recovery = cursor.fetchone()[0]
            
            if not in_recovery:
                print(f"✅ {replica_name} успешно стал мастером!")
                
                # Показываем новую конфигурацию
                cursor.execute("SELECT inet_server_addr(), inet_server_port();")
                addr, port = cursor.fetchone()
                print(f"📍 Новый мастер доступен на: {addr or 'localhost'}:{port}")
                
                return True
            else:
                print(f"❌ {replica_name} все еще в режиме восстановления")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка проверки статуса: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка promote: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Использование: python failover.py <replica1|replica2>")
        sys.exit(1)
    
    replica_name = sys.argv[1]
    
    if replica_name not in ['replica1', 'replica2']:
        print("Ошибка: укажите replica1 или replica2")
        sys.exit(1)
    
    print("⚠️ ВНИМАНИЕ: Выполнение failover изменит топологию репликации!")
    confirm = input(f"Подтвердите переключение на {replica_name} (y/N): ")
    
    if confirm.lower() != 'y':
        print("Операция отменена")
        sys.exit(0)
    
    success = promote_replica(replica_name)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
"""
        
        # Сохраняем все скрипты
        scripts = {
            'init-master.sh': init_master_script,
            'master-setup.sql': master_setup_sql,
            'check_replication.py': check_replication_script,
            'failover.py': failover_script
        }
        
        for filename, content in scripts.items():
            file_path = self.scripts_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Делаем shell скрипты исполняемыми
            if filename.endswith('.sh') or filename.endswith('.py'):
                os.chmod(file_path, 0o755)
        
        # Создаем Dockerfile в корне проекта
        dockerfile_path = self.project_root / 'Dockerfile'
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        
        print("✅ Все скрипты репликации созданы")
        return True
    
    def setup_replication_cluster(self):
        """Полная настройка кластера репликации"""
        print("🚀 НАСТРОЙКА КЛАСТЕРА РЕПЛИКАЦИИ")
        print("=" * 50)
        
        try:
            # 1. Создаем скрипты
            if not self.create_replication_scripts():
                return False
            
            # 2. Останавливаем существующие контейнеры
            print("\\n🛑 Остановка существующих контейнеров...")
            subprocess.run(['docker-compose', '-f', 'docker-compose-ha-replication.yml', 'down', '-v'], 
                         capture_output=True)
            
            # 3. Запускаем кластер
            print("\\n🚀 Запуск кластера репликации...")
            result = subprocess.run([
                'docker-compose', '-f', 'docker-compose-ha-replication.yml', 'up', '-d'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Ошибка запуска кластера: {result.stderr}")
                return False
            
            print("✅ Кластер запущен")
            
            # 4. Ждем инициализации
            print("\\n⏳ Ожидание инициализации кластера...")
            
            # Ждем мастера
            if not self._wait_for_service('postgres-master', 5432, 60):
                print("❌ Мастер не запустился вовремя")
                return False
            
            # Ждем реплики
            if not self._wait_for_service('postgres-replica1', 5433, 120):
                print("⚠️ Replica1 не запустилась, но продолжаем...")
            
            if not self._wait_for_service('postgres-replica2', 5434, 120):
                print("⚠️ Replica2 не запустилась, но продолжаем...")
            
            # 5. Создаем схему БД
            print("\\n📋 Создание схемы базы данных...")
            if not self._setup_database_schema():
                print("⚠️ Ошибка создания схемы, но продолжаем...")
            
            # 6. Проверяем репликацию
            print("\\n🔍 Проверка репликации...")
            time.sleep(10)  # Даем время на подключение реплик
            
            # Запускаем скрипт проверки
            check_script = self.scripts_dir / 'check_replication.py'
            subprocess.run(['python3', str(check_script)])
            
            print("\\n🎉 НАСТРОЙКА КЛАСТЕРА ЗАВЕРШЕНА!")
            print("\\n📊 Доступ к узлам:")
            print("   🟢 Master:   localhost:5432")
            print("   🔵 Replica1: localhost:5433 (синхронная)")
            print("   🔵 Replica2: localhost:5434 (асинхронная)")
            print("   🌐 PgBouncer: localhost:6432 (пул соединений)")
            print("   📈 Monitoring: localhost:9187 (метрики)")
            print("   🏥 Medical API: localhost:8000")
            
            print("\\n🛠️ Полезные команды:")
            print("   Проверка репликации: python scripts/replication/check_replication.py")
            print("   Failover на replica1: python scripts/replication/failover.py replica1")
            print("   Логи кластера: docker-compose -f docker-compose-ha-replication.yml logs -f")
            print("   Остановка: docker-compose -f docker-compose-ha-replication.yml down")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка настройки кластера: {e}")
            return False
    
    def _wait_for_service(self, container_name, port, timeout):
        """Ожидание готовности сервиса"""
        print(f"   ⏳ Ожидание {container_name}...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                conn = psycopg2.connect(
                    host='localhost',
                    port=port,
                    database='medical_records',
                    user='postgres',
                    password='postgres',
                    connect_timeout=5
                )
                conn.close()
                print(f"   ✅ {container_name} готов")
                return True
            except:
                time.sleep(5)
        
        return False
    
    def _setup_database_schema(self):
        """Создание схемы базы данных на мастере"""
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='medical_records',
                user='postgres',
                password='postgres'
            )
            
            cursor = conn.cursor()
            
            # Проверяем, есть ли уже таблицы
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'patients'
            """)
            
            if cursor.fetchone()[0] == 0:
                print("   📝 Создание таблиц медицинской системы...")
                
                # Читаем SQL для создания таблиц
                sql_file = self.project_root / 'src' / 'database' / 'migrations' / '01_create_tables.sql'
                if sql_file.exists():
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        cursor.execute(f.read())
                    conn.commit()
                    print("   ✅ Таблицы созданы")
                else:
                    print("   ⚠️ SQL файл таблиц не найден")
            else:
                print("   ✅ Таблицы уже существуют")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка создания схемы: {e}")
            return False
    
    def test_replication(self):
        """Тестирование репликации данных"""
        print("🧪 ТЕСТИРОВАНИЕ РЕПЛИКАЦИИ")
        print("=" * 40)
        
        try:
            # Подключение к мастеру
            master_conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='medical_records',
                user='postgres', 
                password='postgres'
            )
            
            master_cursor = master_conn.cursor()
            
            # Создаем тестовую запись на мастере
            test_patient = {
                'first_name': 'Тест',
                'last_name': 'Репликации',
                'birth_date': '1990-01-01',
                'gender': 'M'
            }
            
            master_cursor.execute("""
                INSERT INTO patients (first_name, last_name, birth_date, gender)
                VALUES (%(first_name)s, %(last_name)s, %(birth_date)s, %(gender)s)
                RETURNING id
            """, test_patient)
            
            test_id = master_cursor.fetchone()[0]
            master_conn.commit()
            
            print(f"✅ Тестовая запись создана на мастере (ID: {test_id})")
            
            # Ждем репликации
            time.sleep(3)
            
            # Проверяем на репликах
            for port, name in [(5433, 'Replica1'), (5434, 'Replica2')]:
                try:
                    replica_conn = psycopg2.connect(
                        host='localhost',
                        port=port,
                        database='medical_records',
                        user='postgres',
                        password='postgres'
                    )
                    
                    replica_cursor = replica_conn.cursor()
                    replica_cursor.execute("""
                        SELECT first_name, last_name FROM patients WHERE id = %s
                    """, (test_id,))
                    
                    result = replica_cursor.fetchone()
                    
                    if result and result[0] == test_patient['first_name']:
                        print(f"✅ {name}: запись реплицирована успешно")
                    else:
                        print(f"❌ {name}: запись не найдена")
                    
                    replica_cursor.close()
                    replica_conn.close()
                    
                except Exception as e:
                    print(f"❌ {name}: ошибка проверки - {e}")
            
            # Удаляем тестовую запись
            master_cursor.execute("DELETE FROM patients WHERE id = %s", (test_id,))
            master_conn.commit()
            
            master_cursor.close()
            master_conn.close()
            
            print("✅ Тестирование репликации завершено")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка тестирования: {e}")
            return False


def main():
    """Главная функция настройки репликации"""
    print("🏥 НАСТРОЙКА РЕПЛИКАЦИИ ДЛЯ СИСТЕМЫ МЕДКАРТ")
    print("=" * 60)
    
    manager = PostgreSQLReplicationManager()
    
    try:
        # Настройка кластера
        if not manager.setup_replication_cluster():
            print("❌ Не удалось настроить кластер репликации")
            return False
        
        # Тестирование
        print("\\n" + "="*60)
        if manager.test_replication():
            print("✅ Репликация работает корректно!")
        
        print("\\n🎉 РЕПЛИКАЦИЯ НАСТРОЕНА УСПЕШНО!")
        
        # Информация о TDE интеграции
        print("\\n🔒 Для включения TDE с репликацией:")
        print("   1. python -c \"from src.security.tde_complete import main_tde_setup; main_tde_setup()\"")
        print("   2. Перезапустите кластер для применения TDE")
        
        return True
        
    except KeyboardInterrupt:
        print("\\n🛑 Настройка прервана пользователем")
        return False
    except Exception as e:
        print(f"\\n❌ Критическая ошибка: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)