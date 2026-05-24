import os
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Form, File as FastAPIFile, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import func
from sqlalchemy import and_
from app.api.deps import get_db_session, get_current_user
from app.db.models.user import User, UserRole
from app.db.models.teleconsultation import Teleconsultation
from app.db.models.file import File as DBFile
from app.schemas.teleconsultation import TeleconsultationCreate, TeleconsultationRead, TeleconsultationCancel, TeleconsultationStatus
from app.schemas.file import FileRead
from app.services.kafka_service import kafka_service
from app.services.document_validator import document_validator
from typing import List, Optional
from datetime import date

UPLOAD_DIR = "/app/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp", "image/gif"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=TeleconsultationRead, status_code=status.HTTP_201_CREATED)
async def create_teleconsultation(
    *,
    db: AsyncSession = Depends(get_db_session),
    data_in: str = Form(...),
    files: Optional[List[UploadFile]] = FastAPIFile(None),
    current_user: User = Depends(get_current_user)
):
    '''Cria uma nova teleconsulta.'''
    if current_user.role != UserRole.DOCTOR_APS:
        raise HTTPException(status_code=403, detail="Apenas Médicos APS podem criar teleconsultas.")
    
    tele_in = TeleconsultationCreate.model_validate_json(data_in)
        
    db_obj = Teleconsultation(
        **tele_in.model_dump(),
        aps_doctor_id=current_user.id 
    )
    db.add(db_obj)
    await db.flush()

    if files:
        for file in files:
            if file.content_type not in ALLOWED_MIME_TYPES:
                raise HTTPException(status_code=415, detail=f"Tipo {file.content_type} não suportado.")
            
            file_content = await file.read()
            
            if len(file_content) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="Arquivo muito grande (limite 10MB).")
            
            validation = await document_validator.validate(file_content)

            if not validation["is_valid"]:
                raise HTTPException(
                    status_code=422, 
                    detail=f"Documento rejeitado pela IA. Score: {validation['score']}. Limiar: {validation['threshold_applied']}"
                )

            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            db_file = DBFile(
                nome_arquivo=file.filename,
                caminho_arquivo=file_path,
                content_type=file.content_type,
                size_bytes=len(file_content),
                teleconsultation_id=db_obj.id,
                uploaded_by_id=current_user.id,
                ai_score=validation["score"],
                ai_provider=validation["provider"],
                ai_threshold=validation["threshold_applied"]
            )
            db.add(db_file)
    
    await db.commit()
    await db.refresh(db_obj, ["files", "created_at", "patient"]) 

    await kafka_service.send_message("nova_teleconsulta", {
        "destinatario_id": str(db_obj.specialist_doctor_id),
        "message": "Nova teleconsulta disponível."
    })

    return db_obj

@router.get("/{id}", response_model=TeleconsultationRead)
async def get_teleconsultation_detail(
    id: uuid.UUID, 
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    query = (
        select(Teleconsultation)
        .options(joinedload(Teleconsultation.patient)) 
        .filter(Teleconsultation.id == id)
    )
    result = await db.execute(query)
    tele = result.scalars().unique().first()
    
    if not tele: 
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada.")
    
    if current_user.role != UserRole.GLOBAL_ADMIN and \
       tele.aps_doctor_id != current_user.id and \
       tele.specialist_doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    if current_user.role == UserRole.DOCTOR_SPECIALIST and tele.status == TeleconsultationStatus.PENDING:
        tele.status = TeleconsultationStatus.IN_PROGRESS
        await db.commit()
        await db.refresh(tele)

        await kafka_service.send_message("parecer_registrado", {
            "solicitante_id": str(tele.aps_doctor_id),
            "message": "Teleconsultoria em andamento.",
            "teleconsultation_id": str(tele.id)
        })
        
    return tele
@router.get("/", response_model=List[TeleconsultationRead])
async def list_teleconsultations(
    db: AsyncSession = Depends(get_db_session),
    status_filter: Optional[TeleconsultationStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    query = (
        select(Teleconsultation)
        .options(
            selectinload(Teleconsultation.files),
            joinedload(Teleconsultation.patient)
        )
    )
    
    if current_user.role == UserRole.DOCTOR_APS:
        query = query.filter(Teleconsultation.aps_doctor_id == current_user.id)
    elif current_user.role == UserRole.DOCTOR_SPECIALIST:
        query = query.filter(Teleconsultation.specialist_doctor_id == current_user.id)
    
    if status_filter: 
        query = query.filter(Teleconsultation.status == status_filter)
    
    if start_date:
        query = query.filter(Teleconsultation.scheduled_at >= start_date)
    if end_date:
        query = query.filter(Teleconsultation.scheduled_at <= end_date)
        
    query = query.order_by(Teleconsultation.scheduled_at.desc())
        
    result = await db.execute(query)
    return result.scalars().unique().all()

@router.patch("/{id}/cancel", response_model=TeleconsultationRead)
async def cancel_teleconsultation(
    id: uuid.UUID,
    data_in: TeleconsultationCancel,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    query = select(Teleconsultation).filter(Teleconsultation.id == id)
    result = await db.execute(query)
    tele = result.scalars().first()

    if not tele:
        raise HTTPException(status_code=404, detail="Teleconsulta não encontrada.")

    if current_user.role != UserRole.GLOBAL_ADMIN and tele.specialist_doctor_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o especialista pode cancelar esta consulta.")

    tele.status = TeleconsultationStatus.CANCELED
    tele.rejection_justification = data_in.justification
    tele.deleted_at = func.now()

    await db.commit()
    await db.refresh(tele)

    await kafka_service.send_message("parecer_registrado", {
        "solicitante_id": str(tele.aps_doctor_id),
        "message": f"Teleconsultoria cancelada pelo especialista: {data_in.justification}",
        "teleconsultation_id": str(tele.id)
    })
    
    return tele

