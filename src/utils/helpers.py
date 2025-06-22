import re
import secrets
import string
from typing import Optional

def format_phone(phone: str) -> Optional[str]:
    """Форматирование номера телефона"""
    if not phone:
        return None
    
    digits = re.sub(r'\D', '', phone)
    
    if digits.startswith('8') and len(digits) == 11:
        digits = '7' + digits[1:]
    
    if len(digits) == 11 and digits.startswith('7'):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    
    return phone

def generate_password(length: int = 12) -> str:
    """Генерация случайного пароля"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))