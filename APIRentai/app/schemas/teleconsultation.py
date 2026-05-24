from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date, timedelta
from typing import Optional, List
from uuid import UUID
from app.db.models.teleconsultation import TeleconsultationStatus, AllowedSpecialty
from app.schemas.file import FileRead
from app.schemas.patient import PatientRead

class TeleconsultationCreate(BaseModel):
    specialty: AllowedSpecialty
    diagnostic_hypothesis: str = Field(..., min_length=5, max_length=500)
    clinical_history: str = Field(..., min_length=10, max_length=2000)
    scheduled_at: datetime
    patient_id: UUID
    specialist_doctor_id: UUID

    @field_validator('scheduled_at')
    @classmethod
    def validate_scheduled_at(cls, v: datetime) -> datetime:
        agora = datetime.now()
        v = v.replace(tzinfo=None)
        
        if v < agora:
            raise ValueError('A data da consulta não pode ser no passado.')
        
        limite_maximo = agora + timedelta(days=730)
        if v > limite_maximo:
            raise ValueError('A consulta não pode ser agendada para mais de 2 anos no futuro.')
            
        return v

class TeleconsultationRead(TeleconsultationCreate):
    id: UUID
    status: TeleconsultationStatus
    aps_doctor_id: UUID
    created_at: datetime
    rejection_justification: Optional[str] = None
    deleted_at: Optional[datetime] = None
    files: List[FileRead] = []
    patient: Optional[PatientRead]
    
    class Config:
        from_attributes = True

class TeleconsultationCancel(BaseModel):
    justification: str = Field(..., min_length=5, max_length=500)