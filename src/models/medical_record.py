from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class MedicalRecord:
    id: Optional[int] = None
    appointment_id: int = None
    diagnosis_encrypted: bytes = None
    diagnosis_iv: bytes = None
    complaints: Optional[str] = None
    examination_results: Optional[str] = None
    created_at: Optional[datetime] = None
    prescriptions: List['Prescription'] = None

@dataclass
class Prescription:
    id: Optional[int] = None
    medical_record_id: int = None
    medication_name: str = ""
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    notes: Optional[str] = None