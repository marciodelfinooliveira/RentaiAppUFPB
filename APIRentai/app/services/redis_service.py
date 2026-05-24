import redis.asyncio as redis
from app.core.config import settings

class RedisService:
    def __init__(self):
        self.pool = redis.ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        self.client = redis.Redis(connection_pool=self.pool)

    def get_connection(self):
        """Retorna uma instância de cliente Redis usando o pool de conexões."""
        return redis.Redis(connection_pool=self.pool)

    async def publish(self, channel: str, message: str):
        """Publica uma mensagem em um canal do Redis."""
        await self.client.publish(channel, message)

    def pubsub(self):
        """Retorna o objeto pubsub do Redis para escutar eventos."""
        return self.client.pubsub()

    async def add_to_whitelist(self, jti: str, user_id: str, expire_time: int):
        """Adiciona o JTI de um token à whitelist."""
        conn = self.get_connection()
        await conn.setex(f"whitelist:{jti}", expire_time, user_id)

    async def add_to_blacklist(self, jti: str, expire_time: int):
        """Adiciona o JTI de um token à blacklist."""
        conn = self.get_connection()
        await conn.setex(f"blacklist:{jti}", expire_time, "revoked")

    async def is_in_blacklist(self, jti: str) -> bool:
        """Verifica se um JTI está na blacklist."""
        conn = self.get_connection()
        return await conn.exists(f"blacklist:{jti}") > 0

    async def set_with_expiry(self, key: str, value: str, expiry_seconds: int):
        """Define uma chave no Redis com um tempo de expiração especificado em segundos."""
        conn = self.get_connection()
        await conn.setex(name=key, time=expiry_seconds, value=value)

    async def get(self, key: str):
        conn = self.get_connection()
        return await conn.get(key)

    async def delete(self, key: str):
        conn = self.get_connection()
        await conn.delete(key)

redis_service = RedisService()