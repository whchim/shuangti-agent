import aiosqlite
from typing import Optional
from loguru import logger
from app.core.config import settings

_db: Optional[aiosqlite.Connection] = None


async def get_db() -> aiosqlite.Connection:
    global _db
    if _db is None:
        import os
        abs_path = os.path.abspath(settings.database_url)
        db_dir = os.path.dirname(abs_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        _db = await aiosqlite.connect(abs_path)
        _db.row_factory = aiosqlite.Row
        await _db.execute("PRAGMA journal_mode=WAL")
        await _db.execute("PRAGMA foreign_keys=ON")
        logger.info(f"数据库连接已建立: {abs_path}")
    return _db


async def init_db():
    """初始化数据库表结构"""
    db = await get_db()

    sql = """
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL DEFAULT '',
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

    # 迁移：确保 messages 表包含必要列
    try:
        cursor = await db.execute("PRAGMA table_info(messages)")
        existing_cols = {row[1] for row in await cursor.fetchall()}
    except Exception:
        existing_cols = set()

    needed = {
        "round_number": "INTEGER NOT NULL DEFAULT 0",
        "vector_embedding": "TEXT",
    }
    for col_name, col_def in needed.items():
        if col_name not in existing_cols:
            try:
                await db.execute(f"ALTER TABLE messages ADD COLUMN {col_name} {col_def}")
                await db.commit()
                logger.info(f"数据库迁移: 添加 messages.{col_name}")
            except Exception as e:
                # SQLite 不支持 ALTER 某些操作，回退到重建表
                logger.warning(f"ALTER 失败，尝试重建 messages 表: {e}")
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS messages_new (
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
                    )
                """)
                # 复制旧数据
                old_cols = ", ".join(existing_cols)
                await db.execute(f"INSERT INTO messages_new ({old_cols}) SELECT {old_cols} FROM messages")
                await db.execute("DROP TABLE messages")
                await db.execute("ALTER TABLE messages_new RENAME TO messages")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
                await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id)")
                await db.commit()
                logger.info("messages 表已重建，数据已保留")

    # 迁移：移除 users.email 的 UNIQUE 约束（注册不再需要邮箱）
    try:
        cursor = await db.execute("PRAGMA index_list(users)")
        indexes = await cursor.fetchall()
        email_unique_index = None
        for idx in indexes:
            if idx[2] == 1:  # unique=1
                # 检查该唯一索引是否包含 email 列
                ci = await db.execute(f"PRAGMA index_info({idx[1]})")
                cols = await ci.fetchall()
                col_names = [c[2] for c in cols]
                if "email" in col_names:
                    email_unique_index = idx[1]
                    break
        if email_unique_index:
            logger.info(f"检测到 users.email 仍有 UNIQUE 约束（索引: {email_unique_index}），迁移中...")
            await db.execute("PRAGMA foreign_keys=OFF")
            await db.execute("""
                CREATE TABLE users_new (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT NOT NULL DEFAULT '',
                    password_hash TEXT NOT NULL,
                    avatar TEXT,
                    profile_data TEXT DEFAULT '{}',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            await db.execute("INSERT INTO users_new SELECT id, username, email, password_hash, avatar, profile_data, is_active, created_at, updated_at FROM users")
            await db.execute("DROP TABLE users")
            await db.execute("ALTER TABLE users_new RENAME TO users")
            await db.execute("PRAGMA foreign_keys=ON")
            await db.commit()
            logger.info("users 表已重建，email UNIQUE 约束已移除")
    except Exception as e:
        logger.warning(f"users 表迁移失败（可忽略）: {e}")

    logger.info("数据库表初始化完成")


async def close_db():
    global _db
    if _db:
        await _db.close()
        _db = None
        logger.info("数据库连接已关闭")
