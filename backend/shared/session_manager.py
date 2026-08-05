"""
Session Manager Module
Handles user session management using Redis.
Supports session creation, validation, and cleanup.
"""

import os
import uuid
from typing import Optional, Dict
from datetime import timedelta
from shared.redis_client import get_redis_client


# Session configuration
SESSION_PREFIX = "session:"
SESSION_EXPIRE_SECONDS = 60 * 60 * 24 * 7  # 7 days


async def create_session(user_id: str, metadata: Optional[Dict] = None) -> str:
    """
    Create a new user session in Redis.
    
    Args:
        user_id: User's Firebase UID or unique identifier
        metadata: Optional metadata to store with the session
    
    Returns:
        str: Session ID (token)
    
    Usage:
        session_id = await create_session("firebase_uid_123", {"role": "player"})
    """
    redis = await get_redis_client()
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    session_key = f"{SESSION_PREFIX}{session_id}"
    
    # Store session data
    session_data = {
        "user_id": user_id,
        "session_id": session_id,
    }
    
    # Add metadata if provided
    if metadata:
        session_data.update(metadata)
    
    # Save to Redis as hash
    for field, value in session_data.items():
        await redis.hset(session_key, field, str(value))
    
    # Set expiration
    await redis.expire(session_key, SESSION_EXPIRE_SECONDS)
    
    print(f"✅ Session created: {session_id} for user {user_id}")
    
    return session_id


async def get_session(session_id: str) -> Optional[Dict]:
    """
    Retrieve session data from Redis.
    
    Args:
        session_id: Session ID to retrieve
    
    Returns:
        Optional[Dict]: Session data if exists and valid, None otherwise
    """
    redis = await get_redis_client()
    session_key = f"{SESSION_PREFIX}{session_id}"
    
    # Get session data
    session_data = await redis.hgetall(session_key)
    
    if not session_data:
        return None
    
    # Refresh expiration on access
    await redis.expire(session_key, SESSION_EXPIRE_SECONDS)
    
    return session_data


async def validate_session(session_id: str) -> bool:
    """
    Check if a session is valid.
    
    Args:
        session_id: Session ID to validate
    
    Returns:
        bool: True if session exists and is valid
    """
    redis = await get_redis_client()
    session_key = f"{SESSION_PREFIX}{session_id}"
    
    exists = await redis.exists(session_key)
    return exists > 0


async def get_user_id_from_session(session_id: str) -> Optional[str]:
    """
    Get the user ID associated with a session.
    
    Args:
        session_id: Session ID
    
    Returns:
        Optional[str]: User ID if session is valid, None otherwise
    """
    session_data = await get_session(session_id)
    
    if session_data:
        return session_data.get("user_id")
    
    return None


async def delete_session(session_id: str) -> bool:
    """
    Delete a session (logout).
    
    Args:
        session_id: Session ID to delete
    
    Returns:
        bool: True if session was deleted
    """
    redis = await get_redis_client()
    session_key = f"{SESSION_PREFIX}{session_id}"
    
    result = await redis.delete(session_key)
    
    if result > 0:
        print(f"✅ Session deleted: {session_id}")
        return True
    
    return False


async def update_session(session_id: str, data: Dict) -> bool:
    """
    Update session metadata.
    
    Args:
        session_id: Session ID
        data: Dictionary of fields to update
    
    Returns:
        bool: True if session was updated
    """
    redis = await get_redis_client()
    session_key = f"{SESSION_PREFIX}{session_id}"
    
    # Check if session exists
    exists = await redis.exists(session_key)
    if not exists:
        return False
    
    # Update fields
    for field, value in data.items():
        await redis.hset(session_key, field, str(value))
    
    # Refresh expiration
    await redis.expire(session_key, SESSION_EXPIRE_SECONDS)
    
    return True


async def get_all_user_sessions(user_id: str) -> list[str]:
    """
    Get all session IDs for a specific user.
    
    Args:
        user_id: User's unique identifier
    
    Returns:
        list[str]: List of session IDs
    """
    redis = await get_redis_client()
    
    # Scan for all session keys
    pattern = f"{SESSION_PREFIX}*"
    sessions = []
    
    async for key in redis.scan_iter(match=pattern):
        session_data = await redis.hgetall(key)
        if session_data.get("user_id") == user_id:
            sessions.append(session_data.get("session_id"))
    
    return sessions


async def delete_all_user_sessions(user_id: str) -> int:
    """
    Delete all sessions for a specific user (logout from all devices).
    
    Args:
        user_id: User's unique identifier
    
    Returns:
        int: Number of sessions deleted
    """
    redis = await get_redis_client()
    
    # Get all user sessions
    sessions = await get_all_user_sessions(user_id)
    
    # Delete each session
    count = 0
    for session_id in sessions:
        if await delete_session(session_id):
            count += 1
    
    print(f"✅ Deleted {count} sessions for user {user_id}")
    
    return count


async def extend_session(session_id: str, extra_seconds: int = SESSION_EXPIRE_SECONDS) -> bool:
    """
    Extend a session's expiration time.
    
    Args:
        session_id: Session ID
        extra_seconds: Additional seconds to add to expiration
    
    Returns:
        bool: True if session expiration was extended
    """
    redis = await get_redis_client()
    session_key = f"{SESSION_PREFIX}{session_id}"
    
    exists = await redis.exists(session_key)
    if not exists:
        return False
    
    await redis.expire(session_key, extra_seconds)
    
    return True


# Helper function for middleware
async def extract_user_from_session(session_id: Optional[str]) -> Optional[str]:
    """
    Extract user ID from session, typically used in middleware.
    
    Args:
        session_id: Session ID from cookie/header
    
    Returns:
        Optional[str]: User ID if session is valid
    """
    if not session_id:
        return None
    
    return await get_user_id_from_session(session_id)
