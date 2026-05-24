import os
import uuid
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile, Form, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.api.deps import get_db_session, get_current_doctor
from app.db.models.user import User
from app.db.models.patient import Patient
from app.db.models.file import File as DBFile
from app.schemas.file import FileRead
from fastapi.responses import FileResponse
from app.api.deps import get_current_user
from app.db.models.user import UserRole
from sqlalchemy.sql import func
from typing import Optional
from app.services.document_validator import document_validator

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp", "image/gif"}
UPLOAD_DIR = "/app/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=FileRead, status_code=status.HTTP_201_CREATED)
async def upload_support_document(
    patient_id: Optional[uuid.UUID] = Form(None),
    teleconsultation_id: Optional[uuid.UUID] = Form(None),
    file: UploadFile = FastAPIFile(...),
    db: AsyncSession = Depends(get_db_session),
    current_doctor: User = Depends(get_current_doctor)
):
    if patient_id and teleconsultation_id:
        raise HTTPException(status_code=400, detail="Apenas um dos campos deve ser preenchido: patient_id ou teleconsultation_id.")

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Tipo de arquivo não suportado.")

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo muito grande, o limite é 10MB.")

    validation = await document_validator.validate(file_content)
    if not validation["is_valid"]:
        raise HTTPException(
            status_code=422, 
            detail=f"Documento rejeitado pela IA (Score: {validation['score']})."
        )

    if patient_id:
        result = await db.execute(select(Patient).filter_by(id=patient_id))
        if not result.scalars().first():
            raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file_content)

    db_file = DBFile(
        nome_arquivo=file.filename,
        caminho_arquivo=file_path,
        content_type=file.content_type,
        size_bytes=len(file_content),
        patient_id=patient_id,
        teleconsultation_id=teleconsultation_id,
        uploaded_by_id=current_doctor.id,
        ai_score=validation["score"],
        ai_provider=validation["provider"],
        ai_threshold=validation["threshold_applied"]
    )
    
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    return db_file

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_doctor: User = Depends(get_current_doctor)
):
    """Soft delete."""
    result = await db.execute(select(DBFile).filter_by(id=file_id, deleted_at=None))
    db_file = result.scalars().first()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado ou já deletado.")

    db_file.deleted_at = func.now()
    
    db.add(db_file)
    await db.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/{file_id}/download")
async def download_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_doctor: User = Depends(get_current_user)
):
    """Download de um arquivo apenas se ele não estiver deletado."""
    result = await db.execute(
        select(DBFile).filter_by(id=file_id, deleted_at=None)
    )
    db_file = result.scalars().first()
    
    if not db_file or not os.path.exists(db_file.caminho_arquivo):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado ou indisponível.")
    
    return FileResponse(db_file.caminho_arquivo, media_type=db_file.content_type, filename=db_file.nome_arquivo)