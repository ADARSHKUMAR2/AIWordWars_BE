from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from services.auth.controllers.controller import login_or_register, get_user_by_uid
from shared.session_manager import create_session, validate_session, delete_session, get_user_id_from_session

router = APIRouter(prefix="/api")


class LoginRequest(BaseModel):
    id_token: str

class SessionRequest(BaseModel):
    session_id: str

@router.post("/login")
async def login(body: LoginRequest, response: Response):
    try:
        user = await login_or_register(body.id_token)

        session_id = await create_session(
            user_id=user.firebase_uid, 
            metadata={"email": user.email, "display_name": user.display_name}
        )

        # 3. Set a cookie (Optional, but good practice for web clients)
        response.set_cookie(
            key="session_id", 
            value=session_id, 
            httponly=True, 
            max_age=7 * 24 * 60 * 60, # 7 days
            samesite="lax"
        )

        return {
            "session_id": session_id,
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

@router.post("/logout")
async def logout(body: SessionRequest, response: Response):
    """Delete the Redis session to log the user out"""
    try:
        # Delete from Redis
        deleted = await delete_session(body.session_id)
        
        # Clear cookie
        response.delete_cookie("session_id")
        
        if not deleted:
            return {"message": "Session already cleared or invalid"}
            
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/validate")
async def validate_session_endpoint(body: SessionRequest):
    """Check if a session is still valid (used by Unity on startup)"""
    is_valid = await validate_session(body.session_id)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    user_id = await get_user_id_from_session(body.session_id)
    return {
        "valid": True, 
        "user_id": user_id
    }