import re
from datetime import datetime, date
from typing import Optional

class Validators:
    @staticmethod
    def validate_email(email: str) -> bool:
        """Валидация email"""
        if not email:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Валидация телефона"""
        if not phone:
            return False
        digits_only = re.sub(r'\D', '', phone)
        return len(digits_only) >= 10 and len(digits_only) <= 15
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """Санитизация строки"""
        if not input_str:
            return ""
        sanitized = re.sub(r'[<>&"\'`]', '', input_str)
        return sanitized[:max_length].strip()