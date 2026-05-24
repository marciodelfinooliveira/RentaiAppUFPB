import uuid
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Parecer(Base):
    __tablename__ = 'pareceres'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teleconsultation_id = Column(PG_UUID(as_uuid=True), ForeignKey('teleconsultations.id'), nullable=False)
    doctor_id = Column(PG_UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    comment = Column(Text, nullable=False)
    status_at_time = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    doctor = relationship("User", foreign_keys=[doctor_id])
    teleconsultation = relationship("Teleconsultation", backref="pareceres")