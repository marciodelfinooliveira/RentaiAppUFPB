import re
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
import logging
from app.schemas.file import FileRead

logger = logging.getLogger(__name__)

def validate_cpf_logic(v: str) -> str:
    """Lógica unificada de validação e limpeza de CPF."""

    cpf = re.sub(r'\D', '', v)
    
    if len(cpf) != 11:
        raise ValueError('O CPF deve conter exatamente 11 dígitos.')

    if cpf == cpf[0] * 11:
        raise ValueError('CPF inválido.')

    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            raise ValueError('CPF inválido.')

    return cpf

class PatientBase(BaseModel):
    nome: str = Field(..., min_length=3, max_length=200, description="Nome completo do paciente.")
    cpf: str = Field(..., description="CPF do paciente (apenas números).")
    data_nascimento: date = Field(..., description="Data no formato YYYY-MM-DD")

    @field_validator('nome')
    @classmethod
    def validate_nome(cls, v: str) -> str:
        if not re.match(r'^[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+$', v):
            raise ValueError('O nome deve conter apenas letras e espaços.')
        return v.strip()

    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        return validate_cpf_logic(v)

    @field_validator('data_nascimento')
    @classmethod
    def validate_idade(cls, v: date) -> date:
        hoje = date.today()

        if v > hoje:
            raise ValueError('A data de nascimento não pode ser no futuro.')

        idade = hoje.year - v.year - ((hoje.month, hoje.day) < (v.month, v.day))

        if idade > 120:
            raise ValueError(
                'A data de nascimento indica uma idade superior a 120 anos.'
            )

        return v

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=3, max_length=200)
    cpf: Optional[str] = None
    data_nascimento: Optional[date] = None

    @field_validator('nome')
    @classmethod
    def validate_nome_optional(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r'^[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+$', v):
            raise ValueError('O nome deve conter apenas letras e espaços.')
        return v.strip() if v else v

    @field_validator('cpf')
    @classmethod
    def validate_cpf_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_cpf_logic(v)

    @field_validator('data_nascimento')
    @classmethod
    def validate_idade_optional(cls, v: Optional[date]) -> Optional[date]:
        hoje = date.today()

        if v > hoje:
            raise ValueError('A data de nascimento não pode ser no futuro.')

        idade = hoje.year - v.year - ((hoje.month, hoje.day) < (v.month, v.day))

        if idade > 120:
            raise ValueError(
                'A data de nascimento indica uma idade superior a 120 anos.'
            )

        return v

class PatientRead(PatientBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    files: List[FileRead] = []

    model_config = ConfigDict(from_attributes=True)