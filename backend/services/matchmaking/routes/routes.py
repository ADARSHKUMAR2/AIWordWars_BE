from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.matchmaking.controllers.controller import create_room, join_room, get_room

router = APIRouter(prefix="/api")

MULTIPLAYER_SESSION_WS_URL = "ws://localhost:8007"  # Change to deployed URL in production


class CreateRoomRequest(BaseModel):
    user_id: str
    difficulty: int = 5


class JoinRoomRequest(BaseModel):
    room_code: str
    user_id: str


@router.post("/match/create")
async def create_match(body: CreateRoomRequest):
    """
    Player 1 calls this to create a private room.
    Returns the room_code they share with their opponent.
    """
    try:
        room = await create_room(host_uid=body.user_id, difficulty=body.difficulty)
        return {
            "room_code": room.room_code,
            "status": room.status,
            "difficulty": room.difficulty,
            "message": "Room created! Share the room_code with your opponent.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match/join")
async def join_match(body: JoinRoomRequest):
    """
    Player 2 calls this with the room_code.
    Returns the WebSocket URL to connect to for the game.
    """
    try:
        room = await join_room(room_code=body.room_code.upper(), guest_uid=body.user_id)
        ws_url = f"{MULTIPLAYER_SESSION_WS_URL}/ws/{room.room_code}"
        return {
            "room_code": room.room_code,
            "status": room.status,
            "difficulty": room.difficulty,
            "ws_url": ws_url,
            "message": "Joined successfully! Connect to ws_url to start the game.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match/{room_code}")
async def get_match_status(room_code: str):
    """Poll room status. Useful for Player 1 to know when Player 2 has joined."""
    room = await get_room(room_code.upper())
    if not room:
        raise HTTPException(status_code=404, detail="Room not found or expired.")
    return {
        "room_code": room.room_code,
        "status": room.status,
        "difficulty": room.difficulty,
        "host_uid": room.host_uid,
        "guest_uid": room.guest_uid,
    }
