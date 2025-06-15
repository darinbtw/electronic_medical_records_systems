from dataclasses import dataclass  # Для создания класса-карточки
from datetime import date, datetime  # Для работы с датами
from typing import Optional  # Для необязательных полей

@dataclass
class Patient:  # Название нашей "карточки"
    # Поля карточки (как строки в бумажной карточке)
    id: Optional[int] = None  # Номер карточки (может не быть сначала)
    first_name: str = ""      # Имя (обязательное, по умолчанию пустое)
    last_name: str = ""       # Фамилия
    middle_name: Optional[str] = None  # Отчество (может не быть)
    birth_date: date = None   # Дата рождения
    gender: str = ""          # Пол (M или F)
    phone: Optional[str] = None   # Телефон (может не быть)
    email: Optional[str] = None   # Email (может не быть)
    address: Optional[str] = None # Адрес (может не быть)
    created_at: Optional[datetime] = None  # Когда создали карточку
    updated_at: Optional[datetime] = None  # Когда последний раз меняли

    def full_name(self) -> str:
        """Метод для получения полного имени"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)