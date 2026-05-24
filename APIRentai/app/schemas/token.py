from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    """Schema para a resposta do token de acesso."""
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema para os dados contidos dentro do token JWT."""
    email: Optional[str] = None

class RefreshToken(BaseModel):
    """Schema para receber o refresh token no corpo da requisição."""
    refresh_token: str

class AccessTokenResponse(BaseModel):
    """Schema para a resposta da rota de renovação de token."""
    access_token: str
    token_type: str = "bearer"