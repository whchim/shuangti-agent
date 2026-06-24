"""用户认证服务"""
from typing import Optional
from uuid import uuid4

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token


async def register_user(username: str, email: str, password: str) -> dict:
    db = await get_db()
    email = email or f"{username}@shuangti.ai"

    # 检查唯一性
    cursor = await db.execute(
        "SELECT id FROM users WHERE username = ? OR (email != '' AND email = ?)",
        (username, email),
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
    profile = json.loads(user.get("profile_data", "{}"))
    user["profile_data"] = profile
    user["nickname"] = profile.get("nickname", user["username"])
    return user


async def update_user_profile(user_id: str, email: Optional[str] = None,
                              nickname: Optional[str] = None,
                              avatar: Optional[str] = None):
    db = await get_db()
    if avatar is not None:
        await db.execute("UPDATE users SET avatar = ? WHERE id = ?", (avatar, user_id))
    if email is not None:
        await db.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
    if nickname is not None:
        # 昵称存到 profile_data JSON 中
        import json
        cursor = await db.execute("SELECT profile_data FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        profile = json.loads(row["profile_data"]) if row and row["profile_data"] else {}
        profile["nickname"] = nickname
        await db.execute(
            "UPDATE users SET profile_data = ? WHERE id = ?",
            (json.dumps(profile, ensure_ascii=False), user_id),
        )
    await db.execute(
        "UPDATE users SET updated_at = datetime('now') WHERE id = ?", (user_id,)
    )
    await db.commit()


async def change_password(user_id: str, old_password: str, new_password: str):
    """修改密码：验证旧密码后更新为新密码"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT password_hash FROM users WHERE id = ?", (user_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise ValueError("用户不存在")

    if not verify_password(old_password, row["password_hash"]):
        raise ValueError("旧密码不正确")

    new_hash = hash_password(new_password)
    await db.execute(
        "UPDATE users SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
        (new_hash, user_id),
    )
    await db.commit()


async def delete_account(user_id: str, password: str):
    """注销账号：验证密码后删除用户及关联数据"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT password_hash FROM users WHERE id = ?", (user_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise ValueError("用户不存在")

    if not verify_password(password, row["password_hash"]):
        raise ValueError("密码不正确")

    # 删除关联数据
    await db.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
    await db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    await db.commit()


async def change_username(user_id: str, new_username: str):
    """修改用户名：验证唯一性后更新"""
    db = await get_db()
    # 检查唯一性
    cursor = await db.execute(
        "SELECT id FROM users WHERE username = ? AND id != ?", (new_username, user_id)
    )
    if await cursor.fetchone():
        raise ValueError("用户名已被占用")

    await db.execute(
        "UPDATE users SET username = ?, updated_at = datetime('now') WHERE id = ?",
        (new_username, user_id),
    )
    await db.commit()
