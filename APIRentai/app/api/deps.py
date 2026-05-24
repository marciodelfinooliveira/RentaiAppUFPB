from typing import AsyncGenerator, Optional
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.schemas.token import TokenData
from app.db.models.user import User, UserRole
from app.services.user_service import user_service
from app.services.redis_service import redis_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependência que fornece uma sessão de banco de dados por requisição."""
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_db_session), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """Obtém o usuário atual a partir do token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    revoked_token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token revogado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        email: Optional[str] = payload.get("sub")
        jti: Optional[str] = payload.get("jti")

        if await redis_service.is_in_blacklist(jti):
            raise revoked_token_exception

        if email is None:
            raise credentials_exception
        
        token_data = TokenData(email=email)

    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await user_service.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
        
    return user

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Valida se o usuário logado é o Administrador Global."""
    if current_user.role != UserRole.GLOBAL_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação permitida apenas para o Administrador Global."
        )
    return current_user

def get_current_doctor_aps(current_user: User = Depends(get_current_user)) -> User:
    """Valida se o usuário logado é um Médico Solicitante (APS)."""
    if current_user.role != UserRole.DOCTOR_APS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação permitida apenas para Médicos Solicitantes (APS)."
        )
    return current_user

def get_current_doctor_specialist(current_user: User = Depends(get_current_user)) -> User:
    """Valida se o usuário logado é um Médico Especialista."""
    if current_user.role != UserRole.DOCTOR_SPECIALIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação permitida apenas para Médicos Especialistas."
        )
    return current_user

def get_current_doctor(current_user: User = Depends(get_current_user)) -> User:
    """Valida se o usuário é qualquer tipo de médico."""
    if current_user.role not in [UserRole.DOCTOR_APS, UserRole.DOCTOR_SPECIALIST]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação permitida apenas para Médicos."
        )
    return current_user