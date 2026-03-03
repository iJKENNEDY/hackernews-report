"""Personal Posts manager – CRUD for user-created posts and custom categories."""

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ──────────────────────────────────────────────
# Dataclasses
# ──────────────────────────────────────────────

@dataclass
class PersonalCategory:
    id: int
    name: str
    parent_id: Optional[int]
    emoji: str
    color: str
    created_at: int
    children: List["PersonalCategory"] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "parent_id": self.parent_id,
            "emoji": self.emoji,
            "color": self.color,
            "created_at": self.created_at,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class PersonalPost:
    id: int
    title: str
    url: Optional[str]
    date_added: int          # unix timestamp
    category_id: Optional[int]
    tags: List[str]
    description: str
    source: str              # 'personal' | 'hn' | 'example'
    created_at: int
    updated_at: int
    # Populated by join
    category_name: Optional[str] = None
    category_emoji: Optional[str] = None
    category_color: Optional[str] = None
    category_parent_id: Optional[int] = None
    parent_category_name: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "date_added": self.date_added,
            "category_id": self.category_id,
            "category_name": self.category_name,
            "category_emoji": self.category_emoji,
            "category_color": self.category_color,
            "category_parent_id": self.category_parent_id,
            "parent_category_name": self.parent_category_name,
            "tags": self.tags,
            "description": self.description,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ──────────────────────────────────────────────
# Manager
# ──────────────────────────────────────────────

class PersonalPostsManager:
    """SQLite-backed manager for personal posts and categories."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ── Connection ──────────────────────────────

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    @contextmanager
    def _tx(self):
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Schema ──────────────────────────────────

    def initialize_schema(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS personal_categories (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                parent_id  INTEGER REFERENCES personal_categories(id) ON DELETE CASCADE,
                emoji      TEXT    NOT NULL DEFAULT '📁',
                color      TEXT    NOT NULL DEFAULT '#ff6600',
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS personal_posts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                url         TEXT,
                date_added  INTEGER NOT NULL,
                category_id INTEGER REFERENCES personal_categories(id) ON DELETE SET NULL,
                tags        TEXT    NOT NULL DEFAULT '',
                description TEXT    NOT NULL DEFAULT '',
                source      TEXT    NOT NULL DEFAULT 'personal',
                created_at  INTEGER NOT NULL,
                updated_at  INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_pp_category ON personal_posts(category_id);
            CREATE INDEX IF NOT EXISTS idx_pp_date     ON personal_posts(date_added DESC);
            CREATE INDEX IF NOT EXISTS idx_pc_parent   ON personal_categories(parent_id);
        """)
        conn.commit()

    # ── Categories ──────────────────────────────

    def create_category(self, name: str, emoji: str = "📁", color: str = "#ff6600",
                        parent_id: Optional[int] = None) -> PersonalCategory:
        now = int(time.time())
        with self._tx() as conn:
            cur = conn.execute(
                "INSERT INTO personal_categories (name, parent_id, emoji, color, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (name.strip(), parent_id, emoji, color, now),
            )
            return PersonalCategory(
                id=cur.lastrowid, name=name.strip(), parent_id=parent_id,
                emoji=emoji, color=color, created_at=now,
            )

    def get_categories_flat(self) -> List[PersonalCategory]:
        rows = self._get_conn().execute(
            "SELECT id, name, parent_id, emoji, color, created_at "
            "FROM personal_categories ORDER BY parent_id NULLS FIRST, name"
        ).fetchall()
        return [PersonalCategory(**dict(r)) for r in rows]

    def get_categories_tree(self) -> List[PersonalCategory]:
        """Return root categories with children populated."""
        flat = self.get_categories_flat()
        by_id = {c.id: c for c in flat}
        roots: List[PersonalCategory] = []
        for cat in flat:
            if cat.parent_id is None:
                roots.append(cat)
            else:
                parent = by_id.get(cat.parent_id)
                if parent:
                    parent.children.append(cat)
        return roots

    def get_category_by_id(self, cat_id: int) -> Optional[PersonalCategory]:
        row = self._get_conn().execute(
            "SELECT id, name, parent_id, emoji, color, created_at "
            "FROM personal_categories WHERE id = ?", (cat_id,)
        ).fetchone()
        return PersonalCategory(**dict(row)) if row else None

    def update_category(self, cat_id: int, name: Optional[str] = None,
                        emoji: Optional[str] = None, color: Optional[str] = None,
                        parent_id: Optional[int] = None) -> bool:
        cat = self.get_category_by_id(cat_id)
        if not cat:
            return False
        with self._tx() as conn:
            conn.execute(
                "UPDATE personal_categories SET name=?, emoji=?, color=?, parent_id=? WHERE id=?",
                (
                    name.strip() if name else cat.name,
                    emoji if emoji is not None else cat.emoji,
                    color if color is not None else cat.color,
                    parent_id if parent_id is not None else cat.parent_id,
                    cat_id,
                ),
            )
        return True

    def delete_category(self, cat_id: int) -> bool:
        with self._tx() as conn:
            cur = conn.execute(
                "DELETE FROM personal_categories WHERE id=?", (cat_id,)
            )
        return cur.rowcount > 0

    # ── Posts ────────────────────────────────────

    def _row_to_post(self, row) -> PersonalPost:
        r = dict(row)
        tags_str = r.pop("tags", "") or ""
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        return PersonalPost(tags=tags, **r)

    def create_post(self, title: str, url: Optional[str] = None,
                    category_id: Optional[int] = None, tags: Optional[List[str]] = None,
                    description: str = "", source: str = "personal") -> PersonalPost:
        now = int(time.time())
        tags_str = ",".join(t.strip() for t in (tags or []) if t.strip())
        with self._tx() as conn:
            cur = conn.execute(
                "INSERT INTO personal_posts "
                "(title, url, date_added, category_id, tags, description, source, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (title.strip(), url or None, now, category_id, tags_str,
                 description, source, now, now),
            )
            pid = cur.lastrowid
        return self.get_post_by_id(pid)

    def get_posts(self, category_id: Optional[int] = None,
                  tag: Optional[str] = None,
                  source: Optional[str] = None) -> List[PersonalPost]:
        query = """
            SELECT p.*,
                   c.name  AS category_name,
                   c.emoji AS category_emoji,
                   c.color AS category_color,
                   c.parent_id AS category_parent_id,
                   pc.name AS parent_category_name
            FROM personal_posts p
            LEFT JOIN personal_categories c  ON c.id = p.category_id
            LEFT JOIN personal_categories pc ON pc.id = c.parent_id
            WHERE 1=1
        """
        params: list = []
        if category_id is not None:
            query += " AND p.category_id = ?"
            params.append(category_id)
        if tag:
            query += " AND (',' || p.tags || ',') LIKE ?"
            params.append(f"%,{tag},%")
        if source:
            query += " AND p.source = ?"
            params.append(source)
        query += " ORDER BY p.date_added DESC"
        rows = self._get_conn().execute(query, params).fetchall()
        return [self._row_to_post(r) for r in rows]

    def get_post_by_id(self, post_id: int) -> Optional[PersonalPost]:
        row = self._get_conn().execute(
            """
            SELECT p.*,
                   c.name  AS category_name,
                   c.emoji AS category_emoji,
                   c.color AS category_color,
                   c.parent_id AS category_parent_id,
                   pc.name AS parent_category_name
            FROM personal_posts p
            LEFT JOIN personal_categories c  ON c.id = p.category_id
            LEFT JOIN personal_categories pc ON pc.id = c.parent_id
            WHERE p.id = ?
            """, (post_id,)
        ).fetchone()
        return self._row_to_post(row) if row else None

    def update_post(self, post_id: int, title: Optional[str] = None,
                    url: Optional[str] = None, category_id: Optional[int] = None,
                    tags: Optional[List[str]] = None, description: Optional[str] = None,
                    source: Optional[str] = None) -> bool:
        post = self.get_post_by_id(post_id)
        if not post:
            return False
        now = int(time.time())
        tags_str = ",".join(t.strip() for t in (tags if tags is not None else post.tags) if t.strip())
        with self._tx() as conn:
            conn.execute(
                "UPDATE personal_posts SET title=?, url=?, category_id=?, tags=?, "
                "description=?, source=?, updated_at=? WHERE id=?",
                (
                    title.strip() if title else post.title,
                    url if url is not None else post.url,
                    category_id if category_id is not None else post.category_id,
                    tags_str,
                    description if description is not None else post.description,
                    source if source is not None else post.source,
                    now,
                    post_id,
                ),
            )
        return True

    def delete_post(self, post_id: int) -> bool:
        with self._tx() as conn:
            cur = conn.execute("DELETE FROM personal_posts WHERE id=?", (post_id,))
        return cur.rowcount > 0

    def get_all_tags(self) -> List[str]:
        """Return sorted unique tags used across all personal posts."""
        rows = self._get_conn().execute("SELECT tags FROM personal_posts WHERE tags != ''").fetchall()
        tags: set = set()
        for row in rows:
            for t in row[0].split(","):
                t = t.strip()
                if t:
                    tags.add(t)
        return sorted(tags)
