import random
import string
import json
from typing import Optional
from services.matchmaking.models.room import Room, RoomStatus
from shared.redis_client import get_redis_client
from rich import print

ROOM_TTL_SECONDS = 10 * 60  # 10 minutes


def _generate_room_code() -> str:
    """Generate a random 6-character alphanumeric room code."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


async def create_room(host_uid: str, difficulty: int = 5) -> Room:
    """
    Called when a player clicks 'Create Room'.
    Generates a unique room code and stores the room in Redis.
    """
    redis = await get_redis_client()

    # Keep generating until we get a unique code (collision is extremely rare)
    for _ in range(10):
        code = _generate_room_code()
        key = f"room:{code}"
        exists = await redis.exists(key)
        if not exists:
            break

    room = Room(
        room_code=code,
        host_uid=host_uid,
        status=RoomStatus.waiting,
        difficulty=difficulty,
    )

    # Store in Redis as JSON with TTL
    await redis.setex(key, ROOM_TTL_SECONDS, room.model_dump_json())
    print(f"✅ Room {code} created by {host_uid}")
    return room


async def join_room(room_code: str, guest_uid: str) -> Room:
    """
    Called when a player enters a room code and clicks 'Join'.
    Validates the room and adds the guest player.
    """
    redis = await get_redis_client()
    key = f"room:{room_code}"

    raw = await redis.get(key)
    if not raw:
        raise ValueError(f"Room '{room_code}' not found or has expired.")

    room = Room.model_validate_json(raw)

    if room.status != RoomStatus.waiting:
        raise ValueError(f"Room '{room_code}' is no longer available (status: {room.status}).")

    if room.host_uid == guest_uid:
        raise ValueError("You cannot join your own room.")

    # Add guest and mark room as ready
    room.guest_uid = guest_uid
    room.status = RoomStatus.ready

    # Save updated room back to Redis (reset TTL)
    await redis.setex(key, ROOM_TTL_SECONDS, room.model_dump_json())
    print(f"✅ {guest_uid} joined room {room_code}. Room is READY.")
    return room


async def get_room(room_code: str) -> Optional[Room]:
    """Fetch room state from Redis. Returns None if not found."""
    redis = await get_redis_client()
    raw = await redis.get(f"room:{room_code}")
    if not raw:
        return None
    return Room.model_validate_json(raw)


async def update_room_status(room_code: str, status: RoomStatus):
    """Update only the status field of a room in Redis."""
    redis = await get_redis_client()
    key = f"room:{room_code}"
    raw = await redis.get(key)
    if raw:
        room = Room.model_validate_json(raw)
        room.status = status
        await redis.setex(key, ROOM_TTL_SECONDS, room.model_dump_json())
