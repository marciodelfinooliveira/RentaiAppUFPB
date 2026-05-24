import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.models.patient import doctor_patient_assoc
from app.db.models.institution import Institution

class UserRole(str, enum.Enum):
    GLOBAL_ADMIN = "GLOBAL_ADMIN"
    DOCTOR_APS = "DOCTOR_APS"               
    DOCTOR_SPECIALIST = "DOCTOR_SPECIALIST" 

class User(Base):
    __tablename__ = 'users'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(200), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password = Column(Text, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    specialty = Column(String(100), nullable=True)     
    institution_id = Column(PG_UUID(as_uuid=True), ForeignKey('institutions.id'), nullable=True)
    institution = relationship("Institution", back_populates="users")
    is_active = Column(Boolean, default=False, nullable=False)
    patients = relationship(
        "Patient", 
        secondary=doctor_patient_assoc, 
        back_populates="doctors",
        lazy="select"
    )
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)