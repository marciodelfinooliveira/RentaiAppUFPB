import uuid
from sqlalchemy import Column, String, DateTime, Table, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.db.models.file import File

doctor_patient_assoc = Table(
    'doctor_patient',
    Base.metadata,
    Column('doctor_id', PG_UUID(as_uuid=True), ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('patient_id', PG_UUID(as_uuid=True), ForeignKey('patients.id', ondelete="CASCADE"), primary_key=True)
)

class Patient(Base):
    """Tabela de Pacientes."""
    __tablename__ = 'patients'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(200), nullable=False)
    cpf = Column(String(11), index=True, nullable=False)
    data_nascimento = Column(Date, nullable=False) 
    doctors = relationship(
        "User", 
        secondary=doctor_patient_assoc, 
        back_populates="patients",
        lazy="select"
    )
    files = relationship(
        "File", 
        back_populates="patient", 
        cascade="all, delete-orphan", 
        lazy="selectin",
        primaryjoin="and_(File.patient_id == Patient.id, File.deleted_at == None)"
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)