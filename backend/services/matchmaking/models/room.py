from pydantic import BaseModel
from typing import Optional
from enum import Enum


class RoomStatus(str, Enum):
    waiting = "waiting"    # Host created room, waiting for guest
    ready = "ready"        # Both players joined, game can start
    in_game = "in_game"    # Game is actively being played
    finished = "finished"  # Game is done


class Room(BaseModel):
    room_code: str                  # 6-char alphanumeric code players share (e.g., "AB12CD")
    host_uid: str                   # Firebase UID of the room creator
    guest_uid: Optional[str] = None # Firebase UID of the player who joins
    status: RoomStatus = RoomStatus.waiting
    difficulty: int = 5             # Puzzle difficulty for this match
