"""
Battle Pass Controller - Manages battle pass progression and rewards

Battle Pass System:
- 50 tiers, each requiring XP to unlock
- Free rewards: Available to all players
- Premium rewards: Only for users who purchased premium battle pass
- XP is earned from playing games (handled by game-logic service)

This controller handles:
- Getting battle pass status
- Adding XP and leveling up tiers
- Claiming rewards
- Purchasing premium upgrade
"""

from services.monetization.models.battle_pass import BattlePass
from services.monetization.models.inventory import InventoryItem
from datetime import datetime, timedelta
from typing import Dict, Any, List

# XP required for each tier
# Example: Tier 1->2 needs 100 XP, Tier 2->3 needs 150 XP, etc.
XP_PER_TIER = {tier: 100 + (tier * 50) for tier in range(1, 51)}

# Battle Pass rewards configuration
# In production, this could be stored in a database
BATTLE_PASS_REWARDS = {
    1: {"free": {"coins": 100}, "premium": {"hints": 5}},
    2: {"free": {"coins": 150}, "premium": {"theme": "neon"}},
    3: {"free": {"hints": 2}, "premium": {"coins": 300}},
    # ... define rewards for all 50 tiers
    # For brevity, not listing all tiers here
}


async def get_battle_pass_status(user_id: str, season_id: str) -> Dict[str, Any]:
    """
    Get user's battle pass progress for current season
    
    Args:
        user_id: Firebase UID
        season_id: Current season ID (e.g., "season_1")
    
    Returns:
        dict: Battle pass status including tier, XP, premium status
    """
    battle_pass = await BattlePass.find_one(
        BattlePass.user_id == user_id,
        BattlePass.season_id == season_id
    )
    
    if not battle_pass:
        # Create new battle pass entry for this season
        battle_pass = BattlePass(
            user_id=user_id,
            season_id=season_id,
            season_start=datetime.utcnow(),
            season_end=datetime.utcnow() + timedelta(days=90)  # 3 months
        )
        await battle_pass.insert()
    
    # Calculate XP needed for next tier
    xp_for_next = XP_PER_TIER.get(battle_pass.current_tier, 0)
    
    return {
        "current_tier": battle_pass.current_tier,
        "total_xp": battle_pass.total_xp,
        "xp_for_next_tier": xp_for_next,
        "is_premium": battle_pass.is_premium,
        "claimed_free_tiers": battle_pass.claimed_free_tiers,
        "claimed_premium_tiers": battle_pass.claimed_premium_tiers,
        "season_start": battle_pass.season_start.isoformat(),
        "season_end": battle_pass.season_end.isoformat(),
    }


async def add_battle_pass_xp(user_id: str, season_id: str, xp_amount: int) -> Dict[str, Any]:
    """
    Add XP to battle pass and level up tiers if enough XP
    
    This is called by game-logic service after each game
    
    Args:
        user_id: Firebase UID
        season_id: Current season ID
        xp_amount: Amount of XP to add
    
    Returns:
        dict: Updated battle pass status with tier ups
    """
    battle_pass = await BattlePass.find_one(
        BattlePass.user_id == user_id,
        BattlePass.season_id == season_id
    )
    
    if not battle_pass:
        # Create if doesn't exist
        battle_pass = BattlePass(
            user_id=user_id,
            season_id=season_id,
            season_start=datetime.utcnow(),
            season_end=datetime.utcnow() + timedelta(days=90)
        )
    
    # Add XP
    battle_pass.total_xp += xp_amount
    
    # Check for tier ups
    tiers_gained = []
    while battle_pass.current_tier < 50:
        xp_needed = XP_PER_TIER.get(battle_pass.current_tier, float('inf'))
        
        if battle_pass.total_xp >= xp_needed:
            battle_pass.current_tier += 1
            tiers_gained.append(battle_pass.current_tier)
        else:
            break
    
    battle_pass.updated_at = datetime.utcnow()
    await battle_pass.save()
    
    return {
        "success": True,
        "xp_added": xp_amount,
        "current_tier": battle_pass.current_tier,
        "total_xp": battle_pass.total_xp,
        "tiers_gained": tiers_gained,
    }


async def claim_battle_pass_reward(
    user_id: str,
    season_id: str,
    tier: int,
    reward_type: str  # "free" or "premium"
) -> Dict[str, Any]:
    """
    Claim a battle pass reward for a specific tier
    
    Args:
        user_id: Firebase UID
        season_id: Current season ID
        tier: Tier number to claim (1-50)
        reward_type: "free" or "premium"
    
    Returns:
        dict: Claimed rewards
    
    Raises:
        ValueError: If reward already claimed, tier not reached, or premium not owned
    """
    battle_pass = await BattlePass.find_one(
        BattlePass.user_id == user_id,
        BattlePass.season_id == season_id
    )
    
    if not battle_pass:
        raise ValueError("Battle pass not found")
    
    # Check if tier is unlocked
    if tier > battle_pass.current_tier:
        raise ValueError(f"Tier {tier} not yet unlocked")
    
    # Check if already claimed
    if reward_type == "free":
        if tier in battle_pass.claimed_free_tiers:
            raise ValueError("Free reward already claimed")
    elif reward_type == "premium":
        if not battle_pass.is_premium:
            raise ValueError("Premium battle pass not owned")
        if tier in battle_pass.claimed_premium_tiers:
            raise ValueError("Premium reward already claimed")
    else:
        raise ValueError(f"Invalid reward type: {reward_type}")
    
    # Get reward configuration
    tier_rewards = BATTLE_PASS_REWARDS.get(tier, {})
    reward_data = tier_rewards.get(reward_type, {})
    
    if not reward_data:
        raise ValueError(f"No {reward_type} reward for tier {tier}")
    
    # Grant rewards to inventory
    inventory = await InventoryItem.find_one(InventoryItem.user_id == user_id)
    if not inventory:
        inventory = InventoryItem(user_id=user_id)
    
    granted = {}
    for key, value in reward_data.items():
        if key == "coins":
            # Award coins via auth service (not handled here)
            granted["coins"] = value
        elif key == "hints":
            inventory.hints += value
            granted["hints"] = value
        elif key == "theme":
            if value not in inventory.owned_themes:
                inventory.owned_themes.append(value)
            granted["theme"] = value
        elif key == "avatar":
            if value not in inventory.owned_avatars:
                inventory.owned_avatars.append(value)
            granted["avatar"] = value
    
    inventory.updated_at = datetime.utcnow()
    await inventory.save()
    
    # Mark as claimed
    if reward_type == "free":
        battle_pass.claimed_free_tiers.append(tier)
    else:
        battle_pass.claimed_premium_tiers.append(tier)
    
    battle_pass.updated_at = datetime.utcnow()
    await battle_pass.save()
    
    return {
        "success": True,
        "tier": tier,
        "reward_type": reward_type,
        "granted": granted
    }


async def upgrade_to_premium(user_id: str, season_id: str) -> Dict[str, Any]:
    """
    Upgrade user to premium battle pass
    
    This is called after IAP validation succeeds
    
    Args:
        user_id: Firebase UID
        season_id: Current season ID
    
    Returns:
        dict: Success status
    """
    battle_pass = await BattlePass.find_one(
        BattlePass.user_id == user_id,
        BattlePass.season_id == season_id
    )
    
    if not battle_pass:
        raise ValueError("Battle pass not found")
    
    if battle_pass.is_premium:
        raise ValueError("Already premium")
    
    battle_pass.is_premium = True
    battle_pass.updated_at = datetime.utcnow()
    await battle_pass.save()
    
    # Also update inventory
    inventory = await InventoryItem.find_one(InventoryItem.user_id == user_id)
    if inventory:
        inventory.is_premium = True
        inventory.updated_at = datetime.utcnow()
        await inventory.save()
    
    return {
        "success": True,
        "is_premium": True
    }
