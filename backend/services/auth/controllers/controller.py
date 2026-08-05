from datetime import datetime, timezone
from firebase_admin import auth as firebase_auth
from services.auth.models.user import User
from rich import print

async def login_or_register(id_token: str) -> User:
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
    except Exception as e:
        raise ValueError(f"Invalid Firebase token: {e}")

    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    display_name = decoded_token.get("name")
    photo_url = decoded_token.get("picture")

    user = await User.find_one(User.firebase_uid == firebase_uid)
    if user:
        user.last_login = datetime.now(timezone.utc)
        await user.save()
    else:
        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
        )
        await user.insert()
        print(f"✅ New user created: {firebase_uid}")

    return user


async def get_user_by_uid(firebase_uid: str) -> User | None:
    return await User.find_one(User.firebase_uid == firebase_uid)

# ──────────────────────────────────────────────
# XP required to reach each level
# Level 1→2: 100 XP, Level 2→3: 250 XP, etc.
# ──────────────────────────────────────────────
LEVEL_THRESHOLDS = [0, 100, 250, 500, 900, 1400, 2000, 2700, 3500, 4400, 5400]

def xp_for_next_level(current_level: int) -> int:
    """Returns total XP needed to reach the next level. Returns -1 at max level."""
    if current_level >= len(LEVEL_THRESHOLDS) - 1:
        return -1  # Max level reached
    return LEVEL_THRESHOLDS[current_level]

async def award_xp_and_coins(
    firebase_uid: str,
    xp_earned: int,
    coins_earned: int
) -> dict:
    """
    Awards XP and coins to a user after a successful game.
    Handles automatic leveling up.
    Returns a dict with updated stats and whether a level-up occurred.
    """
    user = await User.find_one(User.firebase_uid == firebase_uid)
    if not user:
        raise ValueError(f"User not found: {firebase_uid}")

    old_level = user.level
    user.xp += xp_earned
    user.coins += coins_earned

    # Auto level-up loop (handles multiple level-ups at once)
    leveled_up = False
    while True:
        threshold = xp_for_next_level(user.level)
        if threshold == -1:
            break  # Max level
        if user.xp >= threshold:
            user.level += 1
            leveled_up = True
            print(f"🎉 User {firebase_uid} leveled up to {user.level}!")
        else:
            break

    await user.save()

    return {
        "firebase_uid": user.firebase_uid,
        "xp": user.xp,
        "coins": user.coins,
        "level": user.level,
        "leveled_up": leveled_up,
        "old_level": old_level,
        "xp_earned": xp_earned,
        "coins_earned": coins_earned,
        "xp_to_next_level": xp_for_next_level(user.level),
    }


async def get_user_progression(firebase_uid: str) -> dict:
    """Returns the full progression stats for a user."""
    user = await User.find_one(User.firebase_uid == firebase_uid)
    if not user:
        raise ValueError(f"User not found: {firebase_uid}")

    return {
        "firebase_uid": user.firebase_uid,
        "display_name": user.display_name,
        "xp": user.xp,
        "coins": user.coins,
        "level": user.level,
        "xp_to_next_level": xp_for_next_level(user.level),
    }