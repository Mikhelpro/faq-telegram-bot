import aiosqlite
from dataclasses import dataclass
from datetime import datetime
from config import config


@dataclass
class Faq:
    id: int
    question: str
    answer: str
    category: str
    keywords: str
    hits: int


SCHEMA = """
CREATE TABLE IF NOT EXISTS faqs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    keywords TEXT DEFAULT '',
    hits INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS unanswered (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    question TEXT NOT NULL,
    resolved INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
    last_seen TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(SCHEMA)
            await db.commit()

    # ---------- FAQ management ----------

    async def add_faq(self, question: str, answer: str, category: str = "general", keywords: str = "") -> int:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "INSERT INTO faqs (question, answer, category, keywords) VALUES (?, ?, ?, ?)",
                (question.strip(), answer.strip(), category.strip() or "general", keywords.strip()),
            )
            await db.commit()
            return cur.lastrowid

    async def delete_faq(self, faq_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("DELETE FROM faqs WHERE id = ?", (faq_id,))
            await db.commit()
            return cur.rowcount > 0

    async def edit_faq(self, faq_id: int, question: str = None, answer: str = None) -> bool:
        fields, values = [], []
        if question is not None:
            fields.append("question = ?")
            values.append(question.strip())
        if answer is not None:
            fields.append("answer = ?")
            values.append(answer.strip())
        if not fields:
            return False
        values.append(faq_id)
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(f"UPDATE faqs SET {', '.join(fields)} WHERE id = ?", values)
            await db.commit()
            return cur.rowcount > 0

    async def list_faqs(self, category: str = None) -> list[Faq]:
        query = "SELECT id, question, answer, category, keywords, hits FROM faqs"
        params = ()
        if category:
            query += " WHERE category = ?"
            params = (category,)
        query += " ORDER BY category, id"
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(query, params)
            rows = await cur.fetchall()
            return [Faq(*row) for row in rows]

    async def get_faq(self, faq_id: int) -> Faq | None:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT id, question, answer, category, keywords, hits FROM faqs WHERE id = ?",
                (faq_id,),
            )
            row = await cur.fetchone()
            return Faq(*row) if row else None

    async def increment_hits(self, faq_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE faqs SET hits = hits + 1 WHERE id = ?", (faq_id,))
            await db.commit()

    # ---------- Unanswered question logging ----------

    async def log_unanswered(self, user_id: int, username: str, question: str) -> int:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "INSERT INTO unanswered (user_id, username, question) VALUES (?, ?, ?)",
                (user_id, username or "", question),
            )
            await db.commit()
            return cur.lastrowid

    async def list_unanswered(self, only_unresolved: bool = True) -> list[tuple]:
        query = "SELECT id, user_id, username, question, created_at FROM unanswered"
        if only_unresolved:
            query += " WHERE resolved = 0"
        query += " ORDER BY id DESC LIMIT 30"
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(query)
            return await cur.fetchall()

    async def resolve_unanswered(self, entry_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("UPDATE unanswered SET resolved = 1 WHERE id = ?", (entry_id,))
            await db.commit()
            return cur.rowcount > 0

    # ---------- Users / stats ----------

    async def touch_user(self, user_id: int, username: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO users (user_id, username, last_seen) VALUES (?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET username = excluded.username, last_seen = excluded.last_seen""",
                (user_id, username or "", datetime.utcnow().isoformat()),
            )
            await db.commit()

    async def stats(self) -> dict:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT COUNT(*) FROM faqs")
            faq_count = (await cur.fetchone())[0]
            cur = await db.execute("SELECT COUNT(*) FROM users")
            user_count = (await cur.fetchone())[0]
            cur = await db.execute("SELECT COUNT(*) FROM unanswered WHERE resolved = 0")
            unresolved_count = (await cur.fetchone())[0]
            cur = await db.execute("SELECT question, hits FROM faqs ORDER BY hits DESC LIMIT 5")
            top = await cur.fetchall()
            return {
                "faqs": faq_count,
                "users": user_count,
                "unresolved": unresolved_count,
                "top": top,
            }


db = Database(config.db_path)
