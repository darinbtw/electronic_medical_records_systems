"""
Python backup без использования pg_dump
"""
import os
import sys
import datetime
import gzip
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.database.connection import db

def python_backup():
    """Backup через Python без pg_dump"""
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/python_backup_{timestamp}.sql"
    
    print("Python backup starting...")
    
    try:
        with db.get_cursor() as cursor:
            backup_content = []
            
            # Заголовок
            backup_content.append("-- Python Backup")
            backup_content.append(f"-- Created: {datetime.datetime.now()}")
            backup_content.append("-- " + "=" * 40)
            backup_content.append("")
            
            # Список таблиц в правильном порядке
            tables = [
                ('patients', ['id', 'first_name', 'last_name', 'middle_name', 'birth_date', 'gender', 'phone', 'email', 'address']),
                ('doctors', ['id', 'first_name', 'last_name', 'middle_name', 'specialization', 'license_number', 'phone', 'email']),
                ('appointments', ['id', 'patient_id', 'doctor_id', 'appointment_date', 'status']),
                ('medical_records', ['id', 'appointment_id', 'diagnosis_encrypted', 'diagnosis_iv', 'complaints', 'examination_results']),
                ('prescriptions', ['id', 'medical_record_id', 'medication_name', 'dosage', 'frequency', 'duration', 'notes'])
            ]
            
            total_records = 0
            
            for table_name, columns in tables:
                print(f"Processing {table_name}...", end=" ")
                
                try:
                    # Получаем данные
                    cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
                    rows = cursor.fetchall()
                    
                    if rows:
                        backup_content.append(f"-- Table: {table_name}")
                        backup_content.append(f"-- Records: {len(rows)}")
                        backup_content.append("")
                        
                        # Генерируем INSERT statements
                        for row in rows:
                            values = []
                            for col in columns:
                                val = row.get(col)
                                if val is None:
                                    values.append('NULL')
                                elif isinstance(val, str):
                                    escaped = val.replace("'", "''")
                                    values.append(f"'{escaped}'")
                                elif isinstance(val, (bytes, memoryview)):
                                    hex_data = bytes(val).hex()
                                    values.append(f"'\\x{hex_data}'")
                                elif isinstance(val, datetime.datetime):
                                    values.append(f"'{val.isoformat()}'")
                                elif isinstance(val, datetime.date):
                                    values.append(f"'{val.isoformat()}'")
                                else:
                                    values.append(str(val))
                        
                            values_str = ', '.join(values)
                            columns_str = ', '.join(columns)
                            backup_content.append(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});")
                        
                        backup_content.append("")
                        total_records += len(rows)
                        print(f"OK ({len(rows)} records)")
                    else:
                        print("empty")
                        
                except Exception as e:
                    print(f"ERROR: {e}")
            
            # Записываем backup
            backup_text = '\n'.join(backup_content)
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(backup_text)
            
            size = os.path.getsize(backup_file)
            print(f"Backup created: {size:,} bytes, {total_records} records")
            
            # Сжимаем
            import shutil
            with open(backup_file, 'rb') as f_in:
                with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            os.remove(backup_file)
            
            compressed_size = os.path.getsize(f"{backup_file}.gz")
            compression = (1 - compressed_size/size) * 100
            
            print(f"Compressed: {compressed_size:,} bytes ({compression:.1f}% saved)")
            print(f"BACKUP_SUCCESS: {backup_file}.gz")
            
            return True
            
    except Exception as e:
        print(f"BACKUP_ERROR: {e}")
        return False

if __name__ == "__main__":
    python_backup()