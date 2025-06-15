from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Appointment:
    id: Optional[int] = None
    patient_id: int = None
    doctor_id: int = None
    appointment_date: datetime = None
    status: str = 'scheduled'
    created_at: Optional[datetime] = None