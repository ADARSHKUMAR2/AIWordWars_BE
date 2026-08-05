"""
Redis Client Module
Provides a singleton Redis client for the entire backend.
Supports async operations for FastAPI services.
"""

import os
from typing import Optional
import redis.asyncio as redis
from redis.asyncio import Redis

# Global Redis client instance
_redis_client: Optional[Redis] = None


async def get_redis_client() -> Redis:
    """
    Get or create the Redis client singleton.
    
    Returns:
        Redis: Async Redis client instance
    
    Usage:
        redis = await get_redis_client()
        await redis.set("key", "value")
        value = await redis.get("key")
    """
    global _redis_client
    
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        _redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10
        )
        
        # Test connection
        try:
            await _redis_client.ping()
            print(f"✅ Redis connected: {redis_url}")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            raise
    
    return _redis_client


async def close_redis_client():
    """
    Close the Redis client connection.
    Should be called during application shutdown.
    """
    global _redis_client
    
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        print("✅ Redis connection closed")


# Convenience functions for common operations

async def redis_set(key: str, value: str, expire: Optional[int] = None) -> bool:
    """
    Set a key-value pair in Redis with optional expiration.
    
    Args:
        key: Redis key
        value: Value to store
        expire: Optional expiration time in seconds
    
    Returns:
        bool: True if successful
    """
    redis = await get_redis_client()
    await redis.set(key, value)
    
    if expire:
        await redis.expire(key, expire)
    
    return True


async def redis_get(key: str) -> Optional[str]:
    """
    Get a value from Redis by key.
    
    Args:
        key: Redis key
    
    Returns:
        Optional[str]: Value if exists, None otherwise
    """
    redis = await get_redis_client()
    return await redis.get(key)


async def redis_delete(key: str) -> bool:
    """
    Delete a key from Redis.
    
    Args:
        key: Redis key to delete
    
    Returns:
        bool: True if key was deleted
    """
    redis = await get_redis_client()
    result = await redis.delete(key)
    return result > 0


async def redis_exists(key: str) -> bool:
    """
    Check if a key exists in Redis.
    
    Args:
        key: Redis key
    
    Returns:
        bool: True if key exists
    """
    redis = await get_redis_client()
    result = await redis.exists(key)
    return result > 0


async def redis_lpush(key: str, value: str) -> int:
    """
    Push a value to the left (head) of a Redis list.
    
    Args:
        key: Redis list key
        value: Value to push
    
    Returns:
        int: Length of the list after push
    """
    redis = await get_redis_client()
    return await redis.lpush(key, value)


async def redis_lrange(key: str, start: int, stop: int) -> list:
    """
    Get a range of elements from a Redis list.
    
    Args:
        key: Redis list key
        start: Start index (0-based)
        stop: Stop index (inclusive, -1 for end)
    
    Returns:
        list: List of values
    """
    redis = await get_redis_client()
    return await redis.lrange(key, start, stop)


async def redis_ltrim(key: str, start: int, stop: int) -> bool:
    """
    Trim a Redis list to the specified range.
    
    Args:
        key: Redis list key
        start: Start index
        stop: Stop index
    
    Returns:
        bool: True if successful
    """
    redis = await get_redis_client()
    await redis.ltrim(key, start, stop)
    return True


async def redis_expire(key: str, seconds: int) -> bool:
    """
    Set an expiration time on a Redis key.
    
    Args:
        key: Redis key
        seconds: Time to live in seconds
    
    Returns:
        bool: True if timeout was set
    """
    redis = await get_redis_client()
    result = await redis.expire(key, seconds)
    return result


async def redis_hset(key: str, field: str, value: str) -> bool:
    """
    Set a field in a Redis hash.
    
    Args:
        key: Hash key
        field: Field name
        value: Field value
    
    Returns:
        bool: True if field is new, False if updated
    """
    redis = await get_redis_client()
    result = await redis.hset(key, field, value)
    return result == 1


async def redis_hget(key: str, field: str) -> Optional[str]:
    """
    Get a field from a Redis hash.
    
    Args:
        key: Hash key
        field: Field name
    
    Returns:
        Optional[str]: Field value if exists
    """
    redis = await get_redis_client()
    return await redis.hget(key, field)


async def redis_hgetall(key: str) -> dict:
    """
    Get all fields and values from a Redis hash.
    
    Args:
        key: Hash key
    
    Returns:
        dict: Dictionary of field-value pairs
    """
    redis = await get_redis_client()
    return await redis.hgetall(key)


async def redis_incr(key: str) -> int:
    """
    Increment a Redis key's integer value by 1.
    
    Args:
        key: Redis key
    
    Returns:
        int: New value after increment
    """
    redis = await get_redis_client()
    return await redis.incr(key)


async def redis_decr(key: str) -> int:
    """
    Decrement a Redis key's integer value by 1.
    
    Args:
        key: Redis key
    
    Returns:
        int: New value after decrement
    """
    redis = await get_redis_client()
    return await redis.decr(key)
