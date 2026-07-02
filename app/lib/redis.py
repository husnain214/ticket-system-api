import redis.asyncio as aioredis
import os
from dotenv import load_dotenv

load_dotenv()

redis_client = aioredis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    encoding="utf-8",
    decode_responses=True,
)
