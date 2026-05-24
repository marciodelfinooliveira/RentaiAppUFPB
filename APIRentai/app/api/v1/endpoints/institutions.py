from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.api.deps import get_db_session, get_current_admin
from app.db.models.institution import Institution
from app.db.models.user import User
from app.schemas.institution import InstitutionCreate, InstitutionRead, InstitutionUpdate

router = APIRouter()

@router.post("/", response_model=InstitutionRead, status_code=status.HTTP_201_CREATED)
async def create_institution(
    *,
    db: AsyncSession = Depends(get_db_session),
    institution_in: InstitutionCreate,
    current_admin: User = Depends(get_current_admin)
):
    """
    Cria uma nova instituição, apenas o GLOBAL_ADMIN pode acessar esta rota.
    """
    if institution_in.cnpj:
        result = await db.execute(
            select(Institution).filter(
                Institution.cnpj == institution_in.cnpj,
                Institution.deleted_at.is_(None)
            )
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe uma Instituição ativa cadastrada com este CNPJ."
            )

    db_obj = Institution(
        nome=institution_in.nome,
        cnpj=institution_in.cnpj
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    return db_obj

@router.get("/", response_model=list[InstitutionRead])
async def list_institutions(
    db: AsyncSession = Depends(get_db_session)
):
    """Retorna todas as instituições cadastradas e ativas (não deletadas)."""
    result = await db.execute(
        select(Institution).filter(Institution.deleted_at.is_(None))
    )
    return result.scalars().all()

@router.get("/{institution_id}", response_model=InstitutionRead)
async def get_institution(
    *,
    db: AsyncSession = Depends(get_db_session),
    institution_id: UUID
):
    """
    Retorna os detalhes de uma instituição específica pelo ID.
    """
    result = await db.execute(
        select(Institution).filter(
            Institution.id == institution_id,
            Institution.deleted_at.is_(None)
        )
    )
    db_obj = result.scalars().first()
    
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instituição não encontrada."
        )
        
    return db_obj

@router.patch("/{institution_id}", response_model=InstitutionRead)
async def update_institution(
    *,
    db: AsyncSession = Depends(get_db_session),
    institution_id: UUID,
    institution_in: InstitutionUpdate,
    current_admin: User = Depends(get_current_admin)
):
    """
    Atualiza uma instituição existente. Requer privilégios de GLOBAL_ADMIN.
    """
    result = await db.execute(
        select(Institution).filter(
            Institution.id == institution_id,
            Institution.deleted_at.is_(None)
        )
    )
    db_obj = result.scalars().first()
    
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instituição não encontrada."
        )

    if institution_in.cnpj and institution_in.cnpj != db_obj.cnpj:
        result_cnpj = await db.execute(
            select(Institution).filter(
                Institution.cnpj == institution_in.cnpj,
                Institution.deleted_at.is_(None)
            )
        )
        if result_cnpj.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe outra Instituição ativa cadastrada com este CNPJ."
            )

    update_data = institution_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    
    return db_obj

@router.delete("/{institution_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_institution(
    *,
    db: AsyncSession = Depends(get_db_session),
    institution_id: UUID,
    current_admin: User = Depends(get_current_admin)
):
    """
    Realiza o Soft Delete de uma instituição. Requer privilégios de GLOBAL_ADMIN.
    """
    result = await db.execute(
        select(Institution).filter(
            Institution.id == institution_id,
            Institution.deleted_at.is_(None)
        )
    )
    db_obj = result.scalars().first()
    
    if not db_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instituição não encontrada."
        )

    db_obj.deleted_at = func.now()
    
    db.add(db_obj)
    await db.commit()
    
    return None