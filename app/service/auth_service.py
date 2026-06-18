"""用户认证服务"""
from typing import Optional
from uuid import uuid4

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token


async def register_user(username: str, email: str, password: str) -> dict:
    db = await get_db()

    # 检查唯一性
    cursor = await db.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
    )
    if await cursor.fetchone():
        raise ValueError("用户名或邮箱已存在")

    user_id = uuid4().hex
    password_hash = hash_password(password)

    await db.execute(
        "INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)",
        (user_id, username, email, password_hash),
    )
    await db.commit()

    return {"id": user_id, "username": username, "email": email}


async def login_user(username: str, password: str) -> dict:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, username, email, password_hash FROM users WHERE username = ?", (username,)
    )
    row = await cursor.fetchone()
    if not row:
        raise ValueError("用户名或密码错误")

    user = dict(row)
    if not verify_password(password, user["password_hash"]):
        raise ValueError("用户名或密码错误")

    token = create_access_token(user["id"], user["username"])
    return {
        "token": token,
        "user": {"id": user["id"], "username": user["username"], "email": user["email"]},
    }


async def get_user_profile(user_id: str) -> Optional[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, username, email, avatar, profile_data, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return None

    user = dict(row)
    import json
    user["profile_data"] = json.loads(user.get("profile_data", "{}"))
    return user


async def update_user_profile(user_id: str, avatar: Optional[str], profile_data: Optional[dict]):
    db = await get_db()
    if avatar is not None:
        await db.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))
    if profile_data is not None:
        import json
        await db.execute(
            "UPDATE users SET profile_data = ? WHERE id = ?",
            (json.dumps(profile_data, ensure_ascii=False), user_id),
        )
    await db.execute(
        "UPDATE users SET updated_at = datetime('now') WHERE id = ?", (user_id,)
    )
    await db.commit()
