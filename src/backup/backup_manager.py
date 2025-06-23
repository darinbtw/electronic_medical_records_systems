import os
import subprocess
from datetime import datetime
import logging
from typing import Optional
from src.config import config

class BackupManager:
    def __init__(self):
        self.backup_dir = os.getenv('BACKUP_DIR', './backups')
        os.makedirs(self.backup_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def create_backup(self, backup_type: str = 'full') -> Optional[str]:
        """Создание резервной копии базы данных"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(
            self.backup_dir, 
            f"{config.DB_NAME}_{backup_type}_{timestamp}.sql"
        )
        
        try:
            # Формирование команды pg_dump
            cmd = [
                'pg_dump',
                '-h', config.DB_HOST,
                '-p', str(config.DB_PORT),
                '-U', config.DB_USER,
                '-d', config.DB_NAME,
                '-f', backup_file,
                '--verbose'
            ]
            
            # Установка переменной окружения для пароля
            env = os.environ.copy()
            env['PGPASSWORD'] = config.DB_PASSWORD
            
            # Выполнение backup
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info(f"Backup создан: {backup_file}")
                
                # Сжатие
                subprocess.run(['gzip', backup_file])
                return backup_file + '.gz'
            else:
                self.logger.error(f"Ошибка: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Ошибка backup: {e}")
            return None
    
    def cleanup_old_backups(self, days_to_keep: int = 7):
        """Удаление старых backup файлов"""
        import time
        
        current_time = time.time()
        
        for filename in os.listdir(self.backup_dir):
            file_path = os.path.join(self.backup_dir, filename)
            
            if os.path.isfile(file_path):
                file_age_days = (current_time - os.path.getmtime(file_path)) / 86400
                
                if file_age_days > days_to_keep:
                    os.remove(file_path)
                    self.logger.info(f"Удален старый backup: {filename}")