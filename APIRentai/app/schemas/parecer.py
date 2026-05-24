from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class ParecerCreate(BaseModel):
    teleconsultation_id: UUID
    comment: str

class ParecerRead(ParecerCreate):
    id: UUID
    doctor_id: UUID
    status_at_time: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)