import aiosqlite
from typing import Optional
from loguru import logger
from app.core.config import settings

_db: Optional[aiosqlite.Connection] = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        import os
        db_dir = os.path.dirname(settings.database_url)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        _db = await aiosqlite.connect(settings.database_url)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
        logger.info("数据库连接已建立")
    return _db


async def init_db():
    """初始化数据库表结构"""
    db = await get_db()

    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        avatar TEXT,
        profile_data TEXT DEFAULT '{}',
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL DEFAULT '新对话',
        session_type TEXT NOT NULL DEFAULT 'chat',
        trigger_count INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
        content TEXT NOT NULL,
        round_number INTEGER NOT NULL DEFAULT 0,
        vector_embedding TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS long_term_memories (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        fact TEXT NOT NULL,
        source_session_id TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (source_session_id) REFERENCES sessions(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS knowledge_documents (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT '未分类',
        chunk_count INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
    CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_long_term_memories_user ON long_term_memories(user_id);
    """

    await db.executescript(sql)
    await db.commit()
    logger.info("数据库表初始化完成")


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None
        logger.info("数据库连接已关闭")
