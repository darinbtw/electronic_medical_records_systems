from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Doctor:
    id: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    middle_name: Optional[str] = None
    specialization: str = ""
    license_number: str = ""
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[datetime] = None

    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    def __str__(self):
        return f"Д-р {self.full_name()} ({self.specialization})"