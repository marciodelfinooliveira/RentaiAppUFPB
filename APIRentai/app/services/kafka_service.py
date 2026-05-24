import json
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from app.core.config import settings
import logging
import asyncio


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("kafka_service")
class KafkaService:
    def __init__(self):
        self.producer = None

    async def start(self):
        """Inicia o produtor do Kafka."""
        logger.info("Tentando iniciar o produtor do Kafka...")
        
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BROKERS,
            request_timeout_ms=5000
        )
        
        await self.producer.start()
        logger.info("Produtor do Kafka iniciado com sucesso.")

    async def stop(self):
        """Para o produtor do Kafka."""
        if self.producer:
            logger.info("Parando o produtor do Kafka...")
            await self.producer.stop()
            logger.info("Produtor do Kafka parado com sucesso.")

    async def send_message(self, topic: str, message: dict):
        """Envia uma mensagem JSON para um tópico do Kafka."""
        if not self.producer:
            raise RuntimeError("Tentativa de enviar mensagem, mas o produtor Kafka não está iniciado.")
            
        value_bytes = json.dumps(message).encode('utf-8')
        logger.info(f"Enviando mensagem para o tópico {topic}: {value_bytes}")
        try:
            await self.producer.send_and_wait(topic, value_bytes)
            logger.info(f"Mensagem enviada com sucesso para o tópico {topic}.")
        except KafkaConnectionError as e:
            logger.error(f"Erro de conexão com o Kafka: {e}")
            raise e
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout ao enviar mensagem para o Kafka: {e}")
            raise e
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar mensagem para o Kafka: {e}")
            raise e

kafka_service = KafkaService()