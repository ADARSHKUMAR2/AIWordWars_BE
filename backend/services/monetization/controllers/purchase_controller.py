"""
Purchase Controller - Handles IAP validation and item grants

Flow:
1. User makes purchase in Unity → Google Play processes payment
2. Unity sends purchase token to our backend
3. We verify with Google Play API (is this purchase real?)
4. If valid, grant items to user's inventory
5. Save transaction record for auditing
6. Return success response to Unity

Security Considerations:
- Always verify purchases server-side (never trust client)
- Check for duplicate purchase tokens
- Validate purchase state (0 = purchased, 1 = canceled)
- Log all transactions for fraud detection
"""

from services.monetization.models.transaction import Transaction
from services.monetization.models.inventory import InventoryItem
from services.monetization.config.google_play import get_google_play_client
from datetime import datetime
from typing import Dict, Any

# Product catalog - maps product IDs to what they grant
# In production, this could be stored in a database
PRODUCT_CATALOG = {
    "com.wordwars.hints_10": {
        "type": "consumable",
        "grants": {"hints": 10},
        "name": "10 Hints Pack"
    },
    "com.wordwars.hints_50": {
        "type": "consumable",
        "grants": {"hints": 50},
        "name": "50 Hints Pack"
    },
    "com.wordwars.remove_ads": {
        "type": "non_consumable",
        "grants": {"remove_ads": True},
        "name": "Remove Ads"
    },
    "com.wordwars.battlepass_premium": {
        "type": "non_consumable",
        "grants": {"is_premium": True},
        "name": "Battle Pass Premium"
    },
}


async def validate_and_process_purchase(
    user_id: str,
    product_id: str,
    purchase_token: str
) -> Dict[str, Any]:
    """
    Validate a purchase with Google Play and grant items
    
    Args:
        user_id: Firebase UID of the purchaser
        product_id: Product ID from Google Play Console
        purchase_token: Purchase token from Unity IAP
    
    Returns:
        dict: Result with status and granted items
    
    Raises:
        ValueError: If purchase is invalid or already processed
    """
    
    # Step 1: Check if we've already processed this purchase token
    existing_transaction = await Transaction.find_one(
        Transaction.purchase_token == purchase_token
    )
    
    if existing_transaction:
        if existing_transaction.status == "verified":
            raise ValueError("Purchase already processed")
        elif existing_transaction.status == "failed":
            raise ValueError("Purchase previously failed verification")
    
    # Step 2: Verify with Google Play API
    google_client = get_google_play_client()
    
    try:
        google_response = google_client.verify_purchase(product_id, purchase_token)
    except Exception as e:
        # Save failed transaction
        await Transaction(
            purchase_token=purchase_token,
            product_id=product_id,
            user_id=user_id,
            status="failed",
            google_response={"error": str(e)}
        ).insert()
        raise ValueError(f"Google Play verification failed: {e}")
    
    # Step 3: Check purchase state
    # purchaseState: 0 = purchased, 1 = canceled, 2 = pending
    purchase_state = google_response.get("purchaseState")
    
    if purchase_state != 0:
        await Transaction(
            purchase_token=purchase_token,
            product_id=product_id,
            user_id=user_id,
            status="failed",
            google_response=google_response
        ).insert()
        raise ValueError(f"Purchase not in valid state: {purchase_state}")
    
    # Step 4: Check if product exists in catalog
    if product_id not in PRODUCT_CATALOG:
        raise ValueError(f"Unknown product ID: {product_id}")
    
    product_info = PRODUCT_CATALOG[product_id]
    
    # Step 5: Grant items to user's inventory
    inventory = await InventoryItem.find_one(InventoryItem.user_id == user_id)
    
    if not inventory:
        # Create new inventory if user doesn't have one
        inventory = InventoryItem(user_id=user_id)
    
    # Apply grants based on product type
    granted_items = {}
    for key, value in product_info["grants"].items():
        if key == "hints":
            inventory.hints += value
            granted_items["hints"] = value
        elif key == "remove_ads":
            inventory.remove_ads = True
            granted_items["remove_ads"] = True
        elif key == "is_premium":
            inventory.is_premium = True
            granted_items["is_premium"] = True
    
    inventory.updated_at = datetime.utcnow()
    await inventory.save()
    
    # Step 6: Save successful transaction
    transaction = Transaction(
        purchase_token=purchase_token,
        product_id=product_id,
        user_id=user_id,
        status="verified",
        order_id=google_response.get("orderId"),
        purchase_time_millis=google_response.get("purchaseTimeMillis"),
        google_response=google_response,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    await transaction.insert()
    
    # Step 7: Return success response
    return {
        "success": True,
        "product_name": product_info["name"],
        "granted_items": granted_items,
        "transaction_id": str(transaction.id)
    }
