from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from app.db.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.services.kafka_service import kafka_service

class UserService:
    
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Busca um usuário pelo seu endereço de e-mail.
        """
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()
    
    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """
        Cria um novo usuário no banco de dados.
        """ 
        hashed_password = get_password_hash(user_in.password)
        
        db_user = User(
            nome=user_in.nome,
            email=user_in.email,
            password=hashed_password,
            role=user_in.role,
            specialty=user_in.specialty,
            institution_id=user_in.institution_id
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        message = {"user_id": str(db_user.id), "nome": str(db_user.nome), "email": db_user.email}
        await kafka_service.send_message(
            settings.KAFKA_USER_REGISTRATION_TOPIC,
            message
        )

        return db_user
        
    async def authenticate_user(self, db: AsyncSession, email: str, password: str) -> Optional[User]:
        """
        Autentica um usuário, verificando e-mail e senha.
        """
        user = await self.get_user_by_email(db, email=email)
        
        if not user or not user.is_active:
            return None
        
        if not verify_password(password, user.password):
            return None
            
        return user
    
    async def activate_user(self, db: AsyncSession, user: User) -> User:
        """Ativa a conta de um usuário."""
        user.is_active = True
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
user_service = UserService()