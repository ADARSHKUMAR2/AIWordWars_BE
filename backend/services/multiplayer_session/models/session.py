from pydantic import BaseModel
from typing import Optional, Dict
from enum import Enum


class SessionStatus(str, Enum):
    waiting = "waiting"      # One player connected, waiting for the other
    active = "active"        # Both connected, game is live
    finished = "finished"    # A winner has been declared


class PlayerState(BaseModel):
    user_id: str
    connected: bool = True
    solved: bool = False
    time_taken: Optional[float] = None  # seconds taken to solve


class GameSession(BaseModel):
    room_code: str
    puzzle_id: str
    word: str                # The correct answer (server-side only, never sent to clients)
    scrambled: str           # The scrambled letters sent to players
    difficulty: int
    hint: Optional[str] = None
    status: SessionStatus = SessionStatus.waiting
    players: Dict[str, PlayerState] = {}   # keyed by user_id
    winner_id: Optional[str] = None
    loser_id: Optional[str] = None
