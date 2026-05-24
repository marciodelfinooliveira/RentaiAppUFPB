import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List, Optional
import logging
from app.api.deps import get_db_session, get_current_doctor
from app.db.models.patient import Patient
from app.db.models.user import User
from app.db.models.file import File as DBFile
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from app.services.document_validator import document_validator

UPLOAD_DIR = "/app/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png", "image/webp", "image/gif"}
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def create_patient(
    *,
    db: AsyncSession = Depends(get_db_session),
    patient_data: str = Form(...), 
    files: Optional[List[UploadFile]] = FastAPIFile(None),
    current_doctor: User = Depends(get_current_doctor)
):
    """Cadastra um novo paciente e seus arquivos vinculados."""
    patient_in = PatientCreate.model_validate_json(patient_data)

    result = await db.execute(
        select(Patient).filter(
            Patient.cpf == patient_in.cpf,
            Patient.deleted_at.is_(None)
        )
    )
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Paciente com este CPF já cadastrado e ativo.")

    db_patient = Patient(
        nome=patient_in.nome,
        cpf=patient_in.cpf,
        data_nascimento=patient_in.data_nascimento
    )
    db_patient.doctors.append(current_doctor)
    db.add(db_patient)
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
                patient_id=db_patient.id,
                uploaded_by_id=current_doctor.id,
                ai_score=validation["score"],
                ai_provider=validation["provider"],
                ai_threshold=validation["threshold_applied"]
            )
            db.add(db_file)
        
    await db.commit()
    await db.refresh(db_patient, ["files", "updated_at", "created_at"])
    
    return db_patient

@router.patch("/{patient_id}", response_model=PatientRead)
async def update_patient(
    *,
    db: AsyncSession = Depends(get_db_session),
    patient_id: UUID,
    patient_in: PatientUpdate,
    current_doctor: User = Depends(get_current_doctor)
):
    query = (
        select(Patient)
        .options(selectinload(Patient.files))
        .join(Patient.doctors)
        .filter(Patient.id == patient_id, User.id == current_doctor.id)
    )
    result = await db.execute(query)
    db_patient = result.scalars().first()

    if not db_patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    if patient_in.cpf and patient_in.cpf != db_patient.cpf:
        dup_check = await db.execute(
            select(Patient).filter(
                Patient.cpf == patient_in.cpf,
                Patient.id != patient_id,
                Patient.deleted_at.is_(None)
            )
        )
        if dup_check.scalars().first():
            raise HTTPException(status_code=400, detail="CPF já em uso por outro paciente ativo.")

    update_data = patient_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_patient, field, value)

    db.add(db_patient)
    await db.flush() 
    
    await db.refresh(db_patient, ["files", "updated_at", "created_at"])
    
    await db.commit()
    
    return db_patient

@router.get("/", response_model=List[PatientRead])
async def list_patients(
    db: AsyncSession = Depends(get_db_session),
    current_doctor: User = Depends(get_current_doctor)
):
    """Lista apenas os pacientes vinculados ao médico logado."""
    query = (
        select(Patient)
        .options(selectinload(Patient.files))
        .filter(
            Patient.doctors.any(User.id == current_doctor.id),
            Patient.deleted_at.is_(None)
        )
    )
    
    result = await db.execute(query)
    return result.scalars().unique().all()

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    *,
    db: AsyncSession = Depends(get_db_session),
    patient_id: UUID,
    current_doctor: User = Depends(get_current_doctor)
):
    """Realiza Soft Delete do paciente."""
    query = select(Patient).join(Patient.doctors).filter(
        Patient.id == patient_id,
        User.id == current_doctor.id,
        Patient.deleted_at.is_(None)
    )
    result = await db.execute(query)
    db_patient = result.scalars().first()

    if not db_patient:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")

    db_patient.deleted_at = func.now()
    db.add(db_patient)
    await db.commit()
    return None