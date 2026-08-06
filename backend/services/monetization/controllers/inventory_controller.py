"""
Inventory Controller - Manages user inventory operations

Handles:
- Fetching user inventory
- Consuming items (e.g., using a hint)
- Equipping cosmetics (themes, avatars)
- Checking if user owns specific items
"""

from services.monetization.models.inventory import InventoryItem
from datetime import datetime
from typing import Dict, Any, Optional


async def get_user_inventory(user_id: str) -> Dict[str, Any]:
    """
    Get a user's complete inventory
    
    Args:
        user_id: Firebase UID
    
    Returns:
        dict: User's inventory data
    """
    inventory = await InventoryItem.find_one(InventoryItem.user_id == user_id)
    
    if not inventory:
        # Create default inventory if doesn't exist
        inventory = InventoryItem(user_id=user_id)
        await inventory.insert()
    
    return {
        "hints": inventory.hints,
        "remove_ads": inventory.remove_ads,
        "is_premium": inventory.is_premium,
        "premium_expires_at": inventory.premium_expires_at.isoformat() if inventory.premium_expires_at else None,
        "owned_themes": inventory.owned_themes,
        "owned_avatars": inventory.owned_avatars,
        "owned_titles": inventory.owned_titles,
        "active_theme": inventory.active_theme,
        "active_avatar": inventory.active_avatar,
        "active_title": inventory.active_title,
    }


async def consume_hint(user_id: str) -> Dict[str, Any]:
    """
    Consume one hint from user's inventory
    
    Called when user uses a hint during gameplay
    
    Args:
        user_id: Firebase UID
    
    Returns:
        dict: Updated hint count
    
    Raises:
        ValueError: If user has no hints
    """
    inventory = await InventoryItem.find_one(InventoryItem.user_id == user_id)
    
    if not inventory or inventory.hints <= 0:
        raise ValueError("No hints available")
    
    inventory.hints -= 1
    inventory.updated_at = datetime.utcnow()
    await inventory.save()
    
    return {
        "success": True,
        "remaining_hints": inventory.hints
    }


async def equip_cosmetic(
    user_id: str,
    cosmetic_type: str,
    cosmetic_id: str
) -> Dict[str, Any]:
    """
    Equip a cosmetic item (theme, avatar, or title)
    
    Args:
        user_id: Firebase UID
        cosmetic_type: "theme", "avatar", or "title"
        cosmetic_id: ID of the cosmetic to equip
    
    Returns:
        dict: Success status
    
    Raises:
        ValueError: If user doesn't own the cosmetic or invalid type
    """
    inventory = await InventoryItem.find_one(InventoryItem.user_id == user_id)
    
    if not inventory:
        raise ValueError("Inventory not found")
    
    # Check if user owns the cosmetic
    if cosmetic_type == "theme":
        if cosmetic_id not in inventory.owned_themes:
            raise ValueError("Theme not owned")
        inventory.active_theme = cosmetic_id
        
    elif cosmetic_type == "avatar":
        if cosmetic_id not in inventory.owned_avatars:
            raise ValueError("Avatar not owned")
        inventory.active_avatar = cosmetic_id
        
    elif cosmetic_type == "title":
        if cosmetic_id not in inventory.owned_titles:
            raise ValueError("Title not owned")
        inventory.active_title = cosmetic_id
        
    else:
        raise ValueError(f"Invalid cosmetic type: {cosmetic_type}")
    
    inventory.updated_at = datetime.utcnow()
    await inventory.save()
    
    return {
        "success": True,
        "equipped": {
            "type": cosmetic_type,
            "id": cosmetic_id
        }
    }


async def grant_cosmetic(
    user_id: str,
    cosmetic_type: str,
    cosmetic_id: str
) -> Dict[str, Any]:
    """
    Grant a cosmetic item to a user (from purchase or reward)
    
    Args:
        user_id: Firebase UID
        cosmetic_type: "theme", "avatar", or "title"
        cosmetic_id: ID of the cosmetic to grant
    
    Returns:
        dict: Success status
    """
    inventory = await InventoryItem.find_one(InventoryItem.user_id == user_id)
    
    if not inventory:
        inventory = InventoryItem(user_id=user_id)
    
    # Add to appropriate list if not already owned
    if cosmetic_type == "theme":
        if cosmetic_id not in inventory.owned_themes:
            inventory.owned_themes.append(cosmetic_id)
            
    elif cosmetic_type == "avatar":
        if cosmetic_id not in inventory.owned_avatars:
            inventory.owned_avatars.append(cosmetic_id)
            
    elif cosmetic_type == "title":
        if cosmetic_id not in inventory.owned_titles:
            inventory.owned_titles.append(cosmetic_id)
            
    else:
        raise ValueError(f"Invalid cosmetic type: {cosmetic_type}")
    
    inventory.updated_at = datetime.utcnow()
    await inventory.save()
    
    return {
        "success": True,
        "granted": {
            "type": cosmetic_type,
            "id": cosmetic_id
        }
    }
