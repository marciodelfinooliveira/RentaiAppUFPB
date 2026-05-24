import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
class File(Base):
    __tablename__ = 'files'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome_arquivo = Column(String, nullable=False)
    caminho_arquivo = Column(String, unique=True, nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey('patients.id'), nullable=True)
    patient = relationship("Patient", back_populates="files")
    teleconsultation_id = Column(PG_UUID(as_uuid=True), ForeignKey('teleconsultations.id'), nullable=True)
    teleconsultation = relationship("Teleconsultation", back_populates="files")
    uploaded_by_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    uploader = relationship("User", foreign_keys=[uploaded_by_id])
    ai_score = Column(Float, nullable=True)
    ai_provider = Column(String, nullable=True)
    ai_threshold = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)