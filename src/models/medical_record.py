from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class MedicalRecord:
    id: Optional[int] = None
    appointment_id: Optional[int] = None
    diagnosis_encrypted: Optional[bytes] = None
    diagnosis_iv: Optional[bytes] = None
    complaints: Optional[str] = None
    examination_results: Optional[str] = None
    created_at: Optional[datetime] = None
    prescriptions: Optional[List['Prescription']] = None

@dataclass
class Prescription:
    id: Optional[int] = None
    medical_record_id: Optional[int] = None
    medication_name: str = ""
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    notes: Optional[str] = None

    def __str__(self):
        return f"{self.medication_name} {self.dosage} - {self.frequency}"