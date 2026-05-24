from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re

class InstitutionBase(BaseModel):
    nome: str = Field(
        ..., 
        min_length=3, 
        max_length=200, 
        description="Nome da Instituição"
    )
    cnpj: Optional[str] = Field(
        None, 
        max_length=14, 
        description="CNPJ da Instituição"
    )

class InstitutionCreate(BaseModel):
    nome: str = Field(..., max_length=200)
    cnpj: str = Field(...)

    @field_validator('nome')
    @classmethod
    def validate_nome(cls, v: str) -> str:
        if not re.match(r'^[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+$', v):
            raise ValueError('O nome deve conter apenas letras e espaços, sem números ou caracteres especiais.')
        
        return v.strip()

    @field_validator('cnpj')
    @classmethod
    def validate_and_clean_cnpj(cls, v: str) -> str:
        cleaned_cnpj = re.sub(r'[^a-zA-Z0-9]', '', v)
        
        if len(cleaned_cnpj) != 14:
            raise ValueError('O CNPJ deve conter exatamente 14 caracteres alfanuméricos válidos.')
            
        return cleaned_cnpj.upper()

class InstitutionUpdate(BaseModel):

    nome: Optional[str] = Field(None, max_length=200)
    cnpj: Optional[str] = Field(None)

    @field_validator('nome')
    @classmethod
    def validate_nome(cls, v: Optional[str]) -> Optional[str]:

        if v is None:
            return v
            
        if not re.match(r'^[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+$', v):
            raise ValueError('O nome deve conter apenas letras e espaços, sem números ou caracteres especiais.')
        
        return v.strip()

    @field_validator('cnpj')
    @classmethod
    def validate_and_clean_cnpj(cls, v: Optional[str]) -> Optional[str]:

        if v is None:
            return v
            
        cleaned_cnpj = re.sub(r'[^a-zA-Z0-9]', '', v)
        
        if len(cleaned_cnpj) != 14:
            raise ValueError('O CNPJ deve conter exatamente 14 caracteres alfanuméricos válidos.')
            
        return cleaned_cnpj.upper()

class InstitutionRead(InstitutionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)