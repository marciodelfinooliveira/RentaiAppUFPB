from contextlib import asynccontextmanager
import asyncio
import json
import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models.user import User, UserRole
from app.db.session import AsyncSessionLocal
from app.services.kafka_service import kafka_service
from app.services.redis_service import redis_service
from app.services.websocket_manager import manager
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

async def create_first_admin():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).filter_by(email=settings.ADMIN_EMAIL))
        admin_user = result.scalars().first()

        if not admin_user:
            new_admin = User(
                nome=settings.ADMIN_NAME,
                email=settings.ADMIN_EMAIL,
                password=get_password_hash(settings.ADMIN_PASSWORD),
                role=UserRole.GLOBAL_ADMIN,
                is_active=True,
                institution_id=None
            )
            session.add(new_admin)
            await session.commit()

async def redis_listener():
    """Escuta o Redis e dispara a notificação via WebSocket para o processo da API."""
    try:
        pubsub = redis_service.pubsub()
        await pubsub.subscribe("notify_user")
        logger.info("Redis listener iniciado e aguardando eventos...")
        async for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    await manager.send_notification(data['user_id'], data['message'])
                except Exception as e:
                    logger.error(f"Erro ao processar mensagem do Redis: {e}")
    except Exception as e:
        logger.error(f"Erro na conexão com Redis Pub/Sub: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da API, serviços Kafka e Redis listener."""
    await kafka_service.start()
    await create_first_admin()
    
    task = asyncio.create_task(redis_listener())
    
    yield
    
    task.cancel()
    await kafka_service.stop()

app = FastAPI(
    title="API V4H",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ERROR_MESSAGES_PT_BR = {
    "string_too_short": "O campo deve ter pelo menos {min_length} caracteres.",
    "string_too_long": "O campo deve ter no máximo {max_length} caracteres.",
    "value_error.email": "O e-mail fornecido não é um endereço de e-mail válido.",
    "value_error": "{msg}",
}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    custom_errors = []
    for error in exc.errors():
        error_type = error["type"]
        if error_type == "value_error" and "email" in str(error["msg"]).lower():
            error_type = "value_error.email"
        msg = error["msg"]
        message_template = ERROR_MESSAGES_PT_BR.get(error_type, msg)
        formatted_message = message_template.format(msg=msg, **error.get("ctx", {}))
        custom_errors.append({
            "campo": ".".join(map(str, error["loc"])),
            "mensagem": formatted_message
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detalhe": custom_errors},
    )

app.include_router(api_router, prefix="/api/v1")