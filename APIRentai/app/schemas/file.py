from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class FileRead(BaseModel):
    id: UUID
    nome_arquivo: str
    caminho_arquivo: str
    content_type: str
    size_bytes: int
    patient_id: Optional[UUID] = None
    teleconsultation_id: Optional[UUID] = None
    uploaded_by_id: UUID
    created_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)