import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

class Institution(Base):
    """Tabela de Instituições."""
    __tablename__ = 'institutions'

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(200), nullable=False)
    cnpj = Column(String(14), unique=True, nullable=True)
    users = relationship("User", back_populates="institution", cascade="all, delete-orphan")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Institution(nome='{self.nome}')>"