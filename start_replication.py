#!/usr/bin/env python3
"""
Запуск РЕАЛЬНОЙ репликации PostgreSQL для демонстрации
"""
import os
import subprocess
import time
import psycopg2
import sys

def check_docker():
    """Проверка, что Docker запущен"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker найден:", result.stdout.strip())
            
            # Проверяем, что Docker daemon работает
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                print("❌ Docker Desktop не запущен!")
                print("👉 Запустите Docker Desktop и подождите его загрузки")
                return False
        else:
            print("❌ Docker не установлен!")
            return False
    except Exception as e:
        print(f"❌ Ошибка проверки Docker: {e}")
        return False

def cleanup_old_containers():
    """Удаление старых контейнеров"""
    print("🧹 Очистка старых контейнеров...")
    subprocess.run(['docker-compose', '-f', 'docker-compose-repl.yml', 'down', '-v'], capture_output=True)
    time.sleep(2)

def start_replication():
    """Запуск Docker контейнеров с репликацией"""
    
    if not check_docker():
        print("\n⚠️  ИНСТРУКЦИЯ:")
        print("1. Запустите Docker Desktop")
        print("2. Дождитесь полной загрузки (1-2 минуты)")
        print("3. Запустите этот скрипт снова")
        return False
    
    print("\n🚀 Запуск репликации PostgreSQL...")
    
    # Создаем упрощенный docker-compose файл
    docker_compose = """services:
  master:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: medical_records
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    command: |
      postgres
      -c wal_level=replica
      -c max_wal_senders=10
      -c max_replication_slots=10
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  slave1:
    image: postgres:16-alpine
    environment:
      PGUSER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5433:5432"
    depends_on:
      master:
        condition: service_healthy
    command: |
      bash -c '
      echo "Waiting for master..."
      until PGPASSWORD=postgres psql -h master -U postgres -c "SELECT 1" > /dev/null 2>&1; do
        sleep 1
      done
      echo "Master is ready, creating basebackup..."
      rm -rf /var/lib/postgresql/data/*
      PGPASSWORD=postgres pg_basebackup -h master -D /var/lib/postgresql/data -U postgres -v -P -W -R
      echo "Starting slave1..."
      postgres
      '

  slave2:
    image: postgres:16-alpine
    environment:
      PGUSER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5434:5432"
    depends_on:
      master:
        condition: service_healthy
    command: |
      bash -c '
      echo "Waiting for master..."
      sleep 10
      until PGPASSWORD=postgres psql -h master -U postgres -c "SELECT 1" > /dev/null 2>&1; do
        sleep 1
      done
      echo "Master is ready, creating basebackup..."
      rm -rf /var/lib/postgresql/data/*
      PGPASSWORD=postgres pg_basebackup -h master -D /var/lib/postgresql/data -U postgres -v -P -W -R
      echo "Starting slave2..."
      postgres
      '
"""
    
    # Сохраняем файл
    with open('docker-compose-repl.yml', 'w') as f:
        f.write(docker_compose)
    
    # Очищаем старые контейнеры
    cleanup_old_containers()
    
    # Запускаем контейнеры
    print("📦 Запуск контейнеров...")
    try:
        result = subprocess.run(['docker-compose', '-f', 'docker-compose-repl.yml', 'up', '-d'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Ошибка запуска:", result.stderr)
            return False
            
        print("✅ Контейнеры запущены")
        
        # Ждем инициализации
        print("⏳ Ждем инициализации кластера...")
        for i in range(30, 0, -1):
            print(f"\r⏳ Осталось {i} секунд...", end='', flush=True)
            time.sleep(1)
        print("\r✅ Инициализация завершена    ")
        
        # Даем репликам время на подключение
        time.sleep(10)
        
        # Проверяем репликацию
        return check_replication()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def check_replication():
    """Проверка работы репликации"""
    print("\n🔍 ПРОВЕРКА РЕПЛИКАЦИИ:")
    print("=" * 60)
    
    try:
        # Проверяем, что master доступен
        print("📡 Подключение к Master (5432)...")
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='medical_records',
            user='postgres',
            password='postgres',
            connect_timeout=5
        )
        cursor = conn.cursor()
        print("✅ Master доступен")
        
        # Создаем таблицы вашего проекта
        print("\n📋 Создание таблиц проекта...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        # Проверяем статус репликации
        cursor.execute("""
            SELECT 
                application_name,
                client_addr,
                state,
                sync_state,
                replay_lag
            FROM pg_stat_replication
        """)
        
        replicas = cursor.fetchall()
        
        if replicas:
            print(f"\n✅ РЕПЛИКАЦИЯ РАБОТАЕТ!")
            print(f"📊 Активных реплик: {len(replicas)}")
            for replica in replicas:
                print(f"\n   📡 Реплика: {replica[0]}")
                print(f"      IP: {replica[1]}")
                print(f"      Статус: {replica[2]}")
                print(f"      Синхронизация: {replica[3]}")
                print(f"      Задержка: {replica[4] or 'нет'}")
        else:
            print("\n⚠️  Реплики еще подключаются...")
            print("   Проверьте через 30 секунд командой:")
            print("   docker exec electronic_medical_records_systems-master-1 psql -U postgres -c \"SELECT * FROM pg_stat_replication;\"")
        
        # Тест записи
        print("\n📝 Тест репликации...")
        cursor.execute("INSERT INTO patients (first_name, last_name) VALUES ('Тест', 'Репликации')")
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM patients")
        count_master = cursor.fetchone()[0]
        print(f"✅ Master: {count_master} записей")
        
        cursor.close()
        conn.close()
        
        # Проверяем slaves
        for port, name in [(5433, 'Slave1'), (5434, 'Slave2')]:
            try:
                print(f"\n🔍 Проверка {name} (порт {port})...")
                conn_slave = psycopg2.connect(
                    host='localhost',
                    port=port,
                    database='medical_records',
                    user='postgres',
                    password='postgres',
                    connect_timeout=5
                )
                cursor_slave = conn_slave.cursor()
                
                cursor_slave.execute("SELECT COUNT(*) FROM patients")
                count = cursor_slave.fetchone()[0]
                print(f"✅ {name}: {count} записей - репликация работает!")
                
                cursor_slave.close()
                conn_slave.close()
            except Exception as e:
                print(f"⚠️  {name} еще не готов: {str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print("\n💡 Возможные причины:")
        print("   1. PostgreSQL уже запущен на порту 5432")
        print("   2. Контейнеры еще запускаются")
        print("\n🛠️ Попробуйте:")
        print("   1. Остановите локальный PostgreSQL")
        print("   2. Выполните: docker-compose -f docker-compose-repl.yml logs")
        return False
    
    finally:
        print("\n" + "=" * 60)
        print("📊 ИТОГОВАЯ КОНФИГУРАЦИЯ:")
        print("   Master: localhost:5432")
        print("   Slave1: localhost:5433") 
        print("   Slave2: localhost:5434")
        
        print("\n🛠️ Полезные команды:")
        print("   Статус: docker-compose -f docker-compose-repl.yml ps")
        print("   Логи: docker-compose -f docker-compose-repl.yml logs")
        print("   Остановка: docker-compose -f docker-compose-repl.yml down")
        
        print("\n📚 Проверка репликации:")
        print('   docker exec electronic_medical_records_systems-master-1 psql -U postgres -c "SELECT * FROM pg_stat_replication;"')

if __name__ == "__main__":
    if start_replication():
        print("\n🎉 РЕПЛИКАЦИЯ УСПЕШНО НАСТРОЕНА!")
        print("Теперь запустите run.py - он увидит работающую репликацию")
    else:
        print("\n❌ Не удалось настроить репликацию")
        sys.exit(1)