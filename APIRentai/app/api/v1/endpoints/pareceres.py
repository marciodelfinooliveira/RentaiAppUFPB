from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.deps import get_db_session, get_current_doctor_specialist
from app.db.models.teleconsultation import Teleconsultation, TeleconsultationStatus
from app.db.models.parecer import Parecer
from app.schemas.parecer import ParecerCreate, ParecerRead
from app.services.kafka_service import kafka_service
import uuid
from app.db.models.user import User

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def registrar_parecer(
    data: ParecerCreate,
    db: AsyncSession = Depends(get_db_session),
    current_doctor: User = Depends(get_current_doctor_specialist)
):
    tele = await db.get(Teleconsultation, data.teleconsultation_id)
    if not tele:
        raise HTTPException(status_code=404, detail="Teleconsultoria não encontrada.")

    novo_parecer = Parecer(
        teleconsultation_id=tele.id,
        doctor_id=current_doctor.id,
        comment=data.comment,
        status_at_time=tele.status
    )
    
    tele.status = TeleconsultationStatus.COMPLETED
    
    db.add(novo_parecer)
    await db.commit()

    await kafka_service.send_message("parecer_registrado", {
        "solicitante_id": str(tele.aps_doctor_id),
        "message": f"Novo parecer registrado para o paciente {tele.patient.nome}.",
        "type": "RELOAD_TABLE",
        "teleconsultation_id": str(tele.id)
    })
    
    return {"message": "Parecer registrado e Solicitante notificado."}

@router.get("/{tele_id}/timeline", response_model=list[ParecerRead])
async def get_timeline(tele_id: uuid.UUID, db: AsyncSession = Depends(get_db_session)):
    query = select(Parecer).filter(Parecer.teleconsultation_id == tele_id).order_by(Parecer.created_at)
    result = await db.execute(query)
    return result.scalars().all()