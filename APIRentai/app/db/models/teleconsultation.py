import uuid
import enum
from sqlalchemy import Column, String, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.db.models.file import File

class TeleconsultationStatus(str, enum.Enum):
    PENDING = "PENDENTE"
    IN_PROGRESS = "EM_ANDAMENTO"
    COMPLETED = "CONCLUIDA"
    CANCELED = "CANCELADA"

class AllowedSpecialty(str, enum.Enum):
    CARDIOLOGIA = "Cardiologia"
    CIRURGIA_ROBOTICA = "Cirurgia Robótica"
    ODONTOLOGIA = "Odontologia"
    DOENCAS_RARAS = "Doenças Raras"
    OXIGENOTERAPIA = "Oxigenoterapia"

class Teleconsultation(Base):
    __tablename__ = 'teleconsultations'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    specialty = Column(Enum(AllowedSpecialty), nullable=False)
    diagnostic_hypothesis = Column(Text, nullable=False)
    clinical_history = Column(Text, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(Enum(TeleconsultationStatus), default=TeleconsultationStatus.PENDING, nullable=False)
    rejection_justification = Column(Text, nullable=True)
    aps_doctor_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    specialist_doctor_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    patient_id = Column(PG_UUID(as_uuid=True), ForeignKey('patients.id'), nullable=False)
    aps_doctor = relationship("User", foreign_keys=[aps_doctor_id])
    specialist_doctor = relationship("User", foreign_keys=[specialist_doctor_id])
    patient = relationship("Patient", foreign_keys=[patient_id])
    files = relationship(
        "File", 
        back_populates="teleconsultation",
        cascade="all, delete-orphan", 
        lazy="selectin",
        primaryjoin="and_(File.teleconsultation_id == Teleconsultation.id, File.deleted_at == None)"
    )
    patient = relationship("Patient", foreign_keys=[patient_id], lazy="joined")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Teleconsultation(specialty='{self.specialty}', status='{self.status}')>"