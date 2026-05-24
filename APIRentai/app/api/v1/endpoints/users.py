from fastapi import APIRouter, Depends, HTTPException, status, Response, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import jwt
from app.core.config import settings
import datetime
from datetime import timezone
from app.api.deps import get_db_session, get_current_user, oauth2_scheme
from app.schemas.user import UserCreate, UserRead, UserVerify, UserUpdate
from app.schemas.token import Token, RefreshToken 
from app.services.user_service import user_service
from app.services.redis_service import redis_service
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.db.models.user import User
from app.db.models.user import UserRole
from typing import List

router = APIRouter()

@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def create_user_endpoint(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    """
    Inicia o processo de criação de um novo usuário criando-o como inativo e disparando 
    um evento para envio de e-mail de verificação.
    """
    existing_user = await user_service.get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Um usuário com este e-mail já está cadastrado.",
        )

    await user_service.create_user(db, user_in=user_in)

    return {"message": "Registro iniciado. Por favor, verifique seu e-mail para o código de ativação."}

@router.post("/login", response_model=Token)
async def login_for_access_token(
    db: AsyncSession = Depends(get_db_session),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """Endpoint para autenticar o usuário e retornar tokens de acesso e refresh."""
    user = await user_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = {"sub": user.email}
    
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Endpoint protegido que retorna os dados do usuário logado."""
    return current_user

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_user_email(
    verification_data: UserVerify,
    db: AsyncSession = Depends(get_db_session)
):
    """Verifica o código enviado por e-mail e ativa a conta do usuário."""
    redis_key = f"verification_code:{verification_data.email}"
    stored_code = await redis_service.get(redis_key)

    if not stored_code or stored_code != verification_data.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de verificação inválido ou expirado."
        )

    user = await user_service.get_user_by_email(db, email=verification_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado."
        )

    if user.is_active:
        return {"message": "Conta já está ativa."}

    await user_service.activate_user(db, user)
    await redis_service.delete(redis_key)

    return {"message": "Conta ativada com sucesso! Você já pode fazer o login."}

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    token: str = Depends(oauth2_scheme),
    refresh_token_payload: RefreshToken = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Invalida o access token e o refresh token do usuário, adicionando-os à blacklist."""
    try:
        access_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        access_jti = access_payload.get("jti")
        access_exp = access_payload.get("exp")
        
        refresh_token = refresh_token_payload.refresh_token
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        refresh_jti = refresh_payload.get("jti")
        refresh_exp = refresh_payload.get("exp")

        now = int(datetime.datetime.now(timezone.utc).timestamp())

        if access_exp > now:
            await redis_service.add_to_blacklist(access_jti, access_exp - now)
        if refresh_exp > now:
            await redis_service.add_to_blacklist(refresh_jti, refresh_exp - now)
            
    except jwt.InvalidTokenError:
        pass
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/new-access", response_model=Token)
async def get_new_access_token(
    refresh_token_payload: RefreshToken = Body(...),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Gera um novo par de access e refresh tokens a partir de um refresh token válido,
    invalidando o refresh token antigo..
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token inválido, expirado ou já utilizado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    refresh_token = refresh_token_payload.refresh_token
    
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        jti = payload.get("jti")
        email = payload.get("sub")
        if jti is None or email is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    if await redis_service.is_in_blacklist(jti):
        raise credentials_exception

    user = await user_service.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    exp = payload.get("exp")
    now = int(datetime.datetime.now(timezone.utc).timestamp())
    remaining_time = exp - now
    if remaining_time > 0:
        await redis_service.add_to_blacklist(jti, remaining_time)

    new_token_data = {"sub": user.email}
    new_access_token = create_access_token(data=new_token_data)
    new_refresh_token = create_refresh_token(data=new_token_data)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.get("/specialists", response_model=List[UserRead])
async def list_specialists(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Lista todos os médicos especialistas para seleção no formulário."""
    result = await db.execute(select(User).filter_by(role=UserRole.DOCTOR_SPECIALIST))
    return result.scalars().all()

@router.patch("/me", response_model=UserRead)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db_session),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Atualiza os dados do próprio usuário logado. 
    Apenas os campos fornecidos no corpo da requisição serão alterados.
    """
    
    update_data = user_in.model_dump(exclude_unset=True)

    if not update_data:
        return current_user

    
    if "email" in update_data and update_data["email"] != current_user.email:
        existing_user = await user_service.get_user_by_email(db, email=update_data["email"])
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este e-mail já está em uso por outra conta."
            )

    
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)

    return current_user