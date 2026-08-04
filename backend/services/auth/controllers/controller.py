from datetime import datetime, timezone
from firebase_admin import auth as firebase_auth
from services.auth.models.user import User


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
