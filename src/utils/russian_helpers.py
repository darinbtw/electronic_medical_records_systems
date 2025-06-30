from datetime import datetime
import locale

class RussianDateFormatter:
    """Форматирование дат для русского интерфейса"""
    
    @staticmethod
    def format_date(date_obj):
        """Форматирование даты в русском формате"""
        if isinstance(date_obj, str):
            try:
                # Пробуем разные форматы
                formats = [
                    '%Y-%m-%d',
                    '%Y-%m-%d %H:%M:%S',
                    '%a, %d %b %Y %H:%M:%S %Z'
                ]
                
                for fmt in formats:
                    try:
                        date_obj = datetime.strptime(date_obj, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # Если не получилось распарсить
                    return date_obj
            except:
                return date_obj
        
        if isinstance(date_obj, datetime):
            # Русский формат: дд.мм.гггг
            return date_obj.strftime('%d.%m.%Y')
        
        return str(date_obj)
    
    @staticmethod
    def format_datetime(datetime_obj):
        """Форматирование даты и времени в русском формате"""
        if isinstance(datetime_obj, str):
            try:
                datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))
            except:
                return datetime_obj
        
        if isinstance(datetime_obj, datetime):
            # Русский формат: дд.мм.гггг чч:мм
            return datetime_obj.strftime('%d.%m.%Y %H:%M')
        
        return str(datetime_obj)

def format_phone_russian(phone):
    """Форматирование телефона в русском стиле"""
    if not phone:
        return "не указан"
    
    # Убираем все кроме цифр
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) == 11 and digits.startswith('7'):
        # +7 (999) 123-45-67
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    elif len(digits) == 11 and digits.startswith('8'):
        # 8 (999) 123-45-67
        return f"8 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    else:
        return phone

def format_email_russian(email):
    """Форматирование email"""
    return email if email else "не указан"

def format_gender_russian(gender):
    """Форматирование пола на русском"""
    gender_map = {
        'M': 'Мужской',
        'F': 'Женский',
        'm': 'Мужской', 
        'f': 'Женский'
    }
    return gender_map.get(gender, gender or 'не указан')