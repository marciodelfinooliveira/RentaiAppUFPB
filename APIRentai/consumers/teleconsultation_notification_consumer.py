import json
import logging
import asyncio
import os
import sys
from aiokafka import AIOKafkaConsumer
from app.core.config import settings
from app.services.redis_service import redis_service

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)

async def consume_teleconsultation_notifications():
    print("DEBUG: Iniciando loop de consumo...")
    
    while True:
        consumer = None
        try:
            print(f"DEBUG: Criando consumer para {settings.KAFKA_BROKERS}...")
            consumer = AIOKafkaConsumer(
                "parecer_registrado",
                "nova_teleconsulta",
                bootstrap_servers=settings.KAFKA_BROKERS,
                group_id="teleconsultation_notif_group_redis",
                auto_offset_reset='earliest'
            )
            
            await consumer.start()
            print("DEBUG: Consumer iniciado com sucesso!")
            
            async for msg in consumer:
                data = json.loads(msg.value.decode('utf-8'))
                
                if msg.topic == "parecer_registrado":
                    payload = {
                        "user_id": data.get("solicitante_id"),
                        "message": {"type": "RELOAD_TABLE", "message": data.get("message"), "teleconsultation_id": data.get("teleconsultation_id")}
                    }
                else:
                    payload = {
                        "user_id": data.get("destinatario_id"),
                        "message": {"type": "RELOAD_TABLE", "message": data.get("message")}
                    }
                
                await redis_service.publish("notify_user", json.dumps(payload))
                
        except Exception as e:
            logger.error(f"Erro no consumer Kafka: {type(e).__name__}: {e}")
            if consumer:
                await consumer.stop()
            await asyncio.sleep(5)

if __name__ == "__main__":
    print("DEBUG: Entrando no bloco main...")
    asyncio.run(consume_teleconsultation_notifications())