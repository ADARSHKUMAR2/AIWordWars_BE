from datetime import datetime, timezone
from firebase_admin import auth as firebase_auth
from models.user import User


async def login_or_register(id_token: str) -> User:
    """
    Verifies a Firebase ID token, then finds or creates the user in MongoDB.
    Returns the user document.
    """
    # 1. Verify the Firebase ID token
    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
    except Exception as e:
        raise ValueError(f"Invalid Firebase token: {e}")

    firebase_uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    display_name = decoded_token.get("name")
    photo_url = decoded_token.get("picture")

    # 2. Find or create the user in MongoDB
    user = await User.find_one(User.firebase_uid == firebase_uid)

    if user:
        # Update last login time
        user.last_login = datetime.now(timezone.utc)
        await user.save()
    else:
        # Create a new user document
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
    """Returns a user by their Firebase UID."""
    return await User.find_one(User.firebase_uid == firebase_uid)
