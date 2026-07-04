import json
import logging
from typing import Any
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_redis_client = None


async def get_redis(redis_url: str) -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def cache_set(redis_url: str, key: str, value: dict, ttl: int = 1800) -> bool:
    try:
        client = await get_redis(redis_url)
        serialized = json.dumps(value)
        await client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.warning(f"Redis cache_set failed for key={key}: {e}")
        return False


async def cache_get(redis_url: str, key: str) -> dict | None:
    try:
        client = await get_redis(redis_url)
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"Redis cache_get failed for key={key}: {e}")
        return None


async def cache_delete(redis_url: str, key: str) -> bool:
    try:
        client = await get_redis(redis_url)
        await client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"Redis cache_delete failed for key={key}: {e}")
        return False


async def publish(redis_url: str, channel: str, message: dict) -> bool:
    try:
        client = await get_redis(redis_url)
        await client.publish(channel, json.dumps(message))
        return True
    except Exception as e:
        logger.warning(f"Redis publish failed for channel={channel}: {e}")
        return False


async def ping_redis(redis_url: str) -> bool:
    try:
        client = await get_redis(redis_url)
        return await client.ping()
    except Exception:
        return False
