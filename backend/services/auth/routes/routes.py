from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.auth.controllers.controller import login_or_register, get_user_by_uid

router = APIRouter(prefix="/api")


class LoginRequest(BaseModel):
    id_token: str


@router.post("/login")
async def login(body: LoginRequest):
    try:
        user = await login_or_register(body.id_token)
        return {
            "firebase_uid": user.firebase_uid,
            "display_name": user.display_name,
            "email": user.email,
            "photo_url": user.photo_url,
            "coins": user.coins,
            "xp": user.xp,
            "level": user.level,
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me/{firebase_uid}")
async def get_me(firebase_uid: str):
    user = await get_user_by_uid(firebase_uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "firebase_uid": user.firebase_uid,
        "display_name": user.display_name,
        "email": user.email,
        "photo_url": user.photo_url,
        "coins": user.coins,
        "xp": user.xp,
        "level": user.level,
    }
