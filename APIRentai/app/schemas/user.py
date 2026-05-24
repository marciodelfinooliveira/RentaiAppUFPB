import enum
import re
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator, field_validator
from datetime import datetime
from typing import Optional
from uuid import UUID
from app.db.models.user import UserRole 

class SpecialtyEnum(str, enum.Enum):
    CARDIOLOGIA = "Cardiologia"
    CIRURGIA_ROBOTICA = "Cirurgia Robótica"
    ODONTOLOGIA = "Odontologia"
    DOENCAS_RARAS = "Doenças Raras"
    OXIGENOTERAPIA = "Oxigenoterapia"

class UserBase(BaseModel):
    nome: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Nome de usuário."
    )
    email: EmailStr
    role: UserRole
    specialty: Optional[SpecialtyEnum] = Field(
        None, 
        description="Especialidade do médico. Obrigatória se o perfil for Especialista."
    )
    institution_id: Optional[UUID] = Field(
        None, 
        description="Instituição é obrigatória para médicos."
    )

    @field_validator('nome')
    @classmethod
    def validate_nome(cls, v: str) -> str:
        if not re.match(r'^[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+$', v):
            raise ValueError('O nome deve conter apenas letras e espaços, sem números ou caracteres especiais.')
        return v.strip()

class UserCreate(UserBase):
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=128, 
        description="Senha do usuário, deve ter entre 8 e 128 caracteres."
    )

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("A senha deve conter pelo menos uma letra maiúscula.")
        if not re.search(r"[0-9]", v):
            raise ValueError("A senha deve conter pelo menos um número.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("A senha deve conter pelo menos um caractere especial.")
        return v

    @model_validator(mode='after')
    def validate_doctor_fields(self) -> 'UserCreate':

        if self.role == UserRole.DOCTOR_SPECIALIST and not self.specialty:
            raise ValueError("A especialidade é obrigatória para o perfil Especialista.")
            

        if self.role != UserRole.DOCTOR_SPECIALIST and self.specialty:
            raise ValueError("Apenas médicos com perfil Especialista podem possuir uma especialidade vinculada.")
            

        if self.role in [UserRole.DOCTOR_APS, UserRole.DOCTOR_SPECIALIST] and not self.institution_id:
            raise ValueError("O vínculo com uma instituição é obrigatório para médicos.")
            
        return self

class UserUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=5, max_length=100)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    specialty: Optional[SpecialtyEnum] = None
    institution_id: Optional[UUID] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)

    @field_validator('nome')
    @classmethod
    def validate_nome_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.match(r'^[A-Za-záàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ\s]+$', v):
            raise ValueError('O nome deve conter apenas letras e espaços, sem números ou caracteres especiais.')
        return v.strip()

    @field_validator('password')
    @classmethod
    def validate_password_strength_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.search(r"[A-Z]", v) or not re.search(r"[0-9]", v) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("A nova senha deve conter letra maiúscula, número e caractere especial.")
        return v

class UserRead(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
        
class UserVerify(BaseModel):
    email: EmailStr
    code: str = Field(
        ..., 
        min_length=6, 
        max_length=6, 
        description="Código de 6 dígitos recebido por e-mail."
    )

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not re.match(r'^\d{6}$', v):
            raise ValueError('O código de verificação deve ser estritamente numérico e conter exatamente 6 dígitos.')
        
        return v