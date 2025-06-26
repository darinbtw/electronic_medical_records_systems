#!/usr/bin/env python3
"""
Демонстрация и проверка настройки репликации PostgreSQL
Для учебного проекта - симуляция работы на 3 нодах
"""
import os
import sys
from datetime import datetime

class ReplicationDemo:
    def __init__(self):
        self.master_ip = "192.168.1.10"
        self.slave1_ip = "192.168.1.11"
        self.slave2_ip = "192.168.1.12"
        
    def print_header(self, text):
        """Красивый вывод заголовков"""
        print("\n" + "="*60)
        print(f"🔧 {text}")
        print("="*60)
    
    def demo_master_setup(self):
        """Демонстрация настройки Master"""
        self.print_header("НАСТРОЙКА MASTER УЗЛА")
        
        print(f"📍 IP адрес: {self.master_ip}")
        print("\n1. Добавление в postgresql.conf:")
        print("""
# Replication Master Settings
wal_level = replica
max_wal_senders = 5
wal_keep_segments = 64
archive_mode = on
archive_command = 'test ! -f /archive/%f && cp %p /archive/%f'
synchronous_commit = on
synchronous_standby_names = 'slave1,slave2'
        """)
        
        print("\n2. Добавление в pg_hba.conf:")
        print(f"""
# Replication connections
host    replication     replicator      {self.slave1_ip}/32    md5
host    replication     replicator      {self.slave2_ip}/32    md5
        """)
        
        print("\n3. Создание пользователя репликации:")
        print("CREATE USER replicator WITH REPLICATION PASSWORD 'repl_password';")
        
        print("\n✅ Master настройка завершена!")
        
    def demo_slave_setup(self, slave_name, slave_ip):
        """Демонстрация настройки Slave"""
        self.print_header(f"НАСТРОЙКА {slave_name.upper()} УЗЛА")
        
        print(f"📍 IP адрес: {slave_ip}")
        print(f"📍 Имя узла: {slave_name}")
        
        print("\n1. Остановка PostgreSQL:")
        print("systemctl stop postgresql")
        
        print("\n2. Создание базового backup с master:")
        print(f"""
pg_basebackup \\
    -h {self.master_ip} \\
    -D /var/lib/postgresql/14/main \\
    -U replicator \\
    -v -P -W \\
    -R -X stream \\
    -C -S {slave_name}
        """)
        
        print("\n3. Создание postgresql.auto.conf:")
        print(f"""
primary_conninfo = 'host={self.master_ip} port=5432 user=replicator password=repl_password application_name={slave_name}'
restore_command = 'cp /archive/%f %p'
recovery_target_timeline = 'latest'
        """)
        
        print("\n4. Создание standby.signal")
        print("touch /var/lib/postgresql/14/main/standby.signal")
        
        print(f"\n✅ {slave_name} настройка завершена!")
    
    def demo_replication_check(self):
        """Демонстрация проверки репликации"""
        self.print_header("ПРОВЕРКА СТАТУСА РЕПЛИКАЦИИ")
        
        print("\n📊 На MASTER узле:")
        print("SELECT client_addr, state, sync_state FROM pg_stat_replication;")
        print("\nОжидаемый результат:")
        print("""
┌─────────────────┬─────────────┬────────────┐
│  client_addr    │    state    │ sync_state │
├─────────────────┼─────────────┼────────────┤
│ 192.168.1.11    │  streaming  │    sync    │
│ 192.168.1.12    │  streaming  │    sync    │
└─────────────────┴─────────────┴────────────┘
        """)
        
        print("\n📊 На SLAVE узлах:")
        print("SELECT pg_is_in_recovery();")
        print("\nОжидаемый результат: true")
        
    def generate_docker_compose(self):
        """Генерация docker-compose для тестирования"""
        self.print_header("DOCKER-COMPOSE ДЛЯ ЛОКАЛЬНОГО ТЕСТИРОВАНИЯ")
        
        print("""
version: '3.8'

services:
  postgres-master:
    image: postgres:16
    environment:
      POSTGRES_DB: medical_records
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_REPLICATION_MODE: master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: repl_password
    ports:
      - "5432:5432"
    networks:
      - postgres-network
    volumes:
      - master-data:/var/lib/postgresql/data

  postgres-slave1:
    image: postgres:14
    environment:
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_MASTER_SERVICE: postgres-master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: repl_password
    ports:
      - "5433:5432"
    depends_on:
      - postgres-master
    networks:
      - postgres-network
    volumes:
      - slave1-data:/var/lib/postgresql/data

  postgres-slave2:
    image: postgres:14
    environment:
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_MASTER_SERVICE: postgres-master
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: repl_password
    ports:
      - "5434:5432"
    depends_on:
      - postgres-master
    networks:
      - postgres-network
    volumes:
      - slave2-data:/var/lib/postgresql/data

networks:
  postgres-network:
    driver: bridge

volumes:
  master-data:
  slave1-data:
  slave2-data:
        """)
        
        print("\nСохраните как docker-compose-replication.yml")
        print("\nЗапуск: docker-compose -f docker-compose-replication.yml up")
    
    def test_failover_scenario(self):
        """Сценарий отказоустойчивости"""
        self.print_header("СЦЕНАРИЙ ОТКАЗОУСТОЙЧИВОСТИ")
        
        print("1️⃣ Нормальная работа:")
        print("   Master (W) ← Slave1 (R)")
        print("           ↖")
        print("             Slave2 (R)")
        
        print("\n2️⃣ Отказ Master:")
        print("   Master (X) ← Slave1 (R)")
        print("           ↖")
        print("             Slave2 (R)")
        
        print("\n3️⃣ Промоут Slave1 в Master:")
        print("   # На Slave1:")
        print("   pg_ctl promote")
        print("   # или")
        print("   SELECT pg_promote();")
        
        print("\n4️⃣ Новая конфигурация:")
        print("   Old Master (X)   Slave1→Master (W)")
        print("                            ↖")
        print("                              Slave2 (R)")
        
        print("\n5️⃣ Перенастройка Slave2:")
        print("   Изменить primary_conninfo на новый Master")
    
    def generate_monitoring_queries(self):
        """SQL запросы для мониторинга"""
        self.print_header("SQL ЗАПРОСЫ ДЛЯ МОНИТОРИНГА")
        
        queries = {
            "Статус репликации на Master": """
-- Просмотр всех подключенных реплик
SELECT 
    pid,
    usename,
    application_name,
    client_addr,
    state,
    sync_state,
    sync_priority,
    pg_size_pretty(pg_wal_lsn_diff(sent_lsn, replay_lsn)) as lag
FROM pg_stat_replication
ORDER BY application_name;
            """,
            
            "Лаг репликации": """
-- Проверка отставания реплик
SELECT 
    application_name,
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)) AS replication_lag,
    replay_lag
FROM pg_stat_replication;
            """,
            
            "Статус на Slave": """
-- Проверка режима recovery
SELECT pg_is_in_recovery();

-- Информация о подключении к Master
SELECT * FROM pg_stat_wal_receiver;
            """,
            
            "История репликации": """
-- Просмотр слотов репликации
SELECT slot_name, plugin, slot_type, active, 
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) as behind_master
FROM pg_replication_slots;
            """
        }
        
        for name, query in queries.items():
            print(f"\n📋 {name}:")
            print(query)
    
    def run_demo(self):
        """Запуск полной демонстрации"""
        print("🏥 ДЕМОНСТРАЦИЯ НАСТРОЙКИ РЕПЛИКАЦИИ PostgreSQL")
        print("Система электронных медицинских карт")
        print(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Настройка узлов
        self.demo_master_setup()
        self.demo_slave_setup("slave1", self.slave1_ip)
        self.demo_slave_setup("slave2", self.slave2_ip)
        
        # Проверка
        self.demo_replication_check()
        
        # Отказоустойчивость
        self.test_failover_scenario()
        
        # Мониторинг
        self.generate_monitoring_queries()
        
        # Docker
        self.generate_docker_compose()
        
        print("\n" + "="*60)
        print("✅ Демонстрация завершена!")
        print("="*60)
        
        print("\n📚 Дополнительная информация:")
        print("- Скрипт: scripts/setup_replication_3nodes.sh")
        print("- Требования: 3 сервера с PostgreSQL 16+")
        print("- Сеть: Открытые порты 5432 между серверами")
        print("- Тестирование: Используйте docker-compose")

if __name__ == "__main__":
    demo = ReplicationDemo()
    demo.run_demo()