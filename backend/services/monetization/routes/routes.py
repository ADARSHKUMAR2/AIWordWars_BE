"""
Monetization API Routes

All endpoints for the monetization service:
- Purchase validation
- Inventory management
- Battle pass operations
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from services.monetization.controllers.purchase_controller import validate_and_process_purchase
from services.monetization.controllers.inventory_controller import (
    get_user_inventory,
    consume_hint,
    equip_cosmetic,
    grant_cosmetic
)
from services.monetization.controllers.battlepass_controller import (
    get_battle_pass_status,
    add_battle_pass_xp,
    claim_battle_pass_reward,
    upgrade_to_premium
)

router = APIRouter(prefix="/api")


# ════════════════════════════════════════════════
# Purchase Validation Endpoints
# ════════════════════════════════════════════════

class PurchaseValidationRequest(BaseModel):
    """
    Request body for purchase validation
    Unity sends this after a successful IAP
    """
    user_id: str  # Firebase UID
    product_id: str  # e.g., "com.wordwars.hints_10"
    purchase_token: str  # Token from Google Play


@router.post("/purchase/validate")
async def validate_purchase(request: PurchaseValidationRequest):
    """
    Validate a Google Play purchase and grant items
    
    Flow:
    1. Unity completes purchase with Google Play
    2. Unity sends purchase token to this endpoint
    3. We verify with Google Play API
    4. Grant items to user's inventory
    5. Return success to Unity
    """
    try:
        result = await validate_and_process_purchase(
            user_id=request.user_id,
            product_id=request.product_id,
            purchase_token=request.purchase_token
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


# ════════════════════════════════════════════════
# Inventory Endpoints
# ════════════════════════════════════════════════

@router.get("/inventory/{user_id}")
async def get_inventory(user_id: str):
    """
    Get user's complete inventory
    
    Called by Unity to display owned items in UI
    """
    try:
        inventory = await get_user_inventory(user_id)
        return inventory
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ConsumeHintRequest(BaseModel):
    user_id: str


@router.post("/inventory/consume_hint")
async def use_hint(request: ConsumeHintRequest):
    """
    Consume one hint from inventory
    
    Called when player uses a hint during gameplay
    """
    try:
        result = await consume_hint(request.user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class EquipCosmeticRequest(BaseModel):
    user_id: str
    cosmetic_type: str  # "theme", "avatar", or "title"
    cosmetic_id: str


@router.post("/inventory/equip")
async def equip_item(request: EquipCosmeticRequest):
    """
    Equip a cosmetic item
    
    Called when player changes their theme/avatar/title in UI
    """
    try:
        result = await equip_cosmetic(
            user_id=request.user_id,
            cosmetic_type=request.cosmetic_type,
            cosmetic_id=request.cosmetic_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════
# Battle Pass Endpoints
# ════════════════════════════════════════════════

@router.get("/battlepass/{user_id}")
async def get_battlepass(user_id: str, season_id: str = "season_1"):
    """
    Get battle pass status for current season
    
    Called by Unity to display battle pass UI
    """
    try:
        status = await get_battle_pass_status(user_id, season_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AddBattlePassXPRequest(BaseModel):
    user_id: str
    season_id: str
    xp_amount: int


@router.post("/battlepass/add_xp")
async def add_xp(request: AddBattlePassXPRequest):
    """
    Add XP to battle pass
    
    Called by game-logic service after each game
    """
    try:
        result = await add_battle_pass_xp(
            user_id=request.user_id,
            season_id=request.season_id,
            xp_amount=request.xp_amount
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ClaimRewardRequest(BaseModel):
    user_id: str
    season_id: str
    tier: int
    reward_type: str  # "free" or "premium"


@router.post("/battlepass/claim")
async def claim_reward(request: ClaimRewardRequest):
    """
    Claim a battle pass reward
    
    Called when player clicks claim button in UI
    """
    try:
        result = await claim_battle_pass_reward(
            user_id=request.user_id,
            season_id=request.season_id,
            tier=request.tier,
            reward_type=request.reward_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "monetization"}
