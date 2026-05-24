import asyncio
import json
import logging
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from aiokafka import AIOKafkaConsumer
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.config import settings
from app.core.logging_config import setup_logging 
from app.services.redis_service import redis_service

setup_logging()
logger = logging.getLogger(__name__)

async def send_verification_email(name: str, email: str, code: str):
    """Envia o e-mail de verificação usando o MailHog."""
    message = MIMEMultipart("alternative")
    message["Subject"] = "Código de Verificação - API"
    message["From"] = "noreply@api.com"
    message["To"] = email

    text = f"Olá {name}! Seu código de verificação é: {code}"
    html = f"""
    <html>
        <body>
            <h2>Olá {name}!</h2>
            <p>Obrigado por se registrar. Seu código de verificação é:</p>
            <p style="font-size: 24px; font-weight: bold; letter-spacing: 2px;">{code}</p>
            <p>Este código expira em 10 minutos.</p>
        </body>
    </html>
    """
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.sendmail(message["From"], message["To"], message.as_string())
        logger.info(f"E-mail de verificação enviado para {email}")
    except Exception as e:
        logger.error(f"Falha ao enviar e-mail para {email}: {e}")

async def consume_registration_events():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_USER_REGISTRATION_TOPIC,
        bootstrap_servers=settings.KAFKA_BROKERS,
        group_id="user_verification_group",
        auto_offset_reset='earliest'
    )
    await consumer.start()
    logger.info("Consumidor Kafka de registro de usuários iniciado.")

    try:
        async for msg in consumer:
            try:
                data = json.loads(msg.value.decode('utf-8'))
                email = data.get("email")
                user_id = data.get("user_id")
                name = data.get("nome")

                if not email or not user_id:
                    logger.warning(f"Mensagem inválida recebida: {data}")
                    continue

                logger.info(f"Processando evento de registro para o e-mail: {email}")

                verification_code = str(random.randint(100000, 999999))

                redis_key = f"verification_code:{email}"
                await redis_service.set_with_expiry(redis_key, verification_code, 600)
                logger.info(f"Código de verificação para {email} salvo no Redis.")
                
                await send_verification_email(name, email, verification_code)

            except json.JSONDecodeError:
                logger.error(f"Erro ao decodificar mensagem JSON: {msg.value}")
            except Exception as e:
                logger.error(f"Erro inesperado ao processar mensagem: {e}")
    finally:
        await consumer.stop()
        logger.info("Consumidor Kafka parado.")

if __name__ == "__main__":
    asyncio.run(consume_registration_events())