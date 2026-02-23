"""Favorites system for bookmarking Hacker News posts into groups."""

import sqlite3
import time
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class FavoriteGroup:
    """Represents a group/collection for organizing favorite posts."""
    id: int
    name: str
    emoji: str = "📁"
    color: str = "#ff6600"
    created_at: int = 0
    post_count: int = 0

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'emoji': self.emoji,
            'color': self.color,
            'created_at': self.created_at,
            'post_count': self.post_count,
        }


@dataclass
class Favorite:
    """Represents a favorited post entry."""
    post_id: int
    group_id: Optional[int] = None  # None = default group
    added_at: int = 0

    def to_dict(self) -> dict:
        return {
            'post_id': self.post_id,
            'group_id': self.group_id,
            'added_at': self.added_at,
        }


class FavoritesManager:
    """Manages favorites storage in SQLite."""

    # Default group constant
    DEFAULT_GROUP_ID = 0

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _initialize_schema(self) -> None:
        """Create favorites tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Groups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorite_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                emoji TEXT DEFAULT '📁',
                color TEXT DEFAULT '#ff6600',
                created_at INTEGER NOT NULL
            )
        """)

        # Favorites table (post_id + group_id = unique pair)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                group_id INTEGER DEFAULT 0,
                added_at INTEGER NOT NULL,
                UNIQUE(post_id, group_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_favorites_post_id
            ON favorites(post_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_favorites_group_id
            ON favorites(group_id)
        """)

        conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ──────────── Groups CRUD ────────────

    def create_group(self, name: str, emoji: str = "📁", color: str = "#ff6600") -> FavoriteGroup:
        """Create a new favorite group."""
        conn = self._get_connection()
        now = int(time.time())
        try:
            conn.execute(
                "INSERT INTO favorite_groups (name, emoji, color, created_at) VALUES (?, ?, ?, ?)",
                (name.strip(), emoji, color, now)
            )
            conn.commit()
            group_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            return FavoriteGroup(id=group_id, name=name.strip(), emoji=emoji, color=color, created_at=now)
        except sqlite3.IntegrityError:
            raise ValueError(f"Group '{name}' already exists")

    def get_groups(self) -> List[FavoriteGroup]:
        """Get all favorite groups with post counts."""
        conn = self._get_connection()
        rows = conn.execute("""
            SELECT g.id, g.name, g.emoji, g.color, g.created_at,
                   COUNT(f.id) as post_count
            FROM favorite_groups g
            LEFT JOIN favorites f ON f.group_id = g.id
            GROUP BY g.id
            ORDER BY g.created_at DESC
        """).fetchall()

        return [
            FavoriteGroup(
                id=r['id'], name=r['name'], emoji=r['emoji'],
                color=r['color'], created_at=r['created_at'],
                post_count=r['post_count']
            )
            for r in rows
        ]

    def get_group_by_id(self, group_id: int) -> Optional[FavoriteGroup]:
        """Get a single group by ID."""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT id, name, emoji, color, created_at FROM favorite_groups WHERE id = ?",
            (group_id,)
        ).fetchone()
        if row:
            return FavoriteGroup(
                id=row['id'], name=row['name'], emoji=row['emoji'],
                color=row['color'], created_at=row['created_at']
            )
        return None

    def update_group(self, group_id: int, name: str = None, emoji: str = None, color: str = None) -> bool:
        """Update a group's attributes."""
        conn = self._get_connection()
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name.strip())
        if emoji is not None:
            updates.append("emoji = ?")
            params.append(emoji)
        if color is not None:
            updates.append("color = ?")
            params.append(color)

        if not updates:
            return False

        params.append(group_id)
        try:
            conn.execute(
                f"UPDATE favorite_groups SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            raise ValueError(f"Group name already exists")

    def delete_group(self, group_id: int) -> bool:
        """Delete a group and all its favorites."""
        conn = self._get_connection()
        conn.execute("DELETE FROM favorites WHERE group_id = ?", (group_id,))
        result = conn.execute("DELETE FROM favorite_groups WHERE id = ?", (group_id,))
        conn.commit()
        return result.rowcount > 0

    # ──────────── Favorites CRUD ────────────

    def add_favorite(self, post_id: int, group_id: int = 0) -> bool:
        """Add a post to favorites (default group or specific group)."""
        conn = self._get_connection()
        now = int(time.time())
        try:
            conn.execute(
                "INSERT INTO favorites (post_id, group_id, added_at) VALUES (?, ?, ?)",
                (post_id, group_id, now)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Already favorited in this group

    def remove_favorite(self, post_id: int, group_id: int = 0) -> bool:
        """Remove a post from a specific group (or default)."""
        conn = self._get_connection()
        result = conn.execute(
            "DELETE FROM favorites WHERE post_id = ? AND group_id = ?",
            (post_id, group_id)
        )
        conn.commit()
        return result.rowcount > 0

    def remove_favorite_from_all(self, post_id: int) -> int:
        """Remove a post from ALL groups."""
        conn = self._get_connection()
        result = conn.execute(
            "DELETE FROM favorites WHERE post_id = ?",
            (post_id,)
        )
        conn.commit()
        return result.rowcount

    def is_favorite(self, post_id: int, group_id: int = 0) -> bool:
        """Check if a post is favorited in a specific group."""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT 1 FROM favorites WHERE post_id = ? AND group_id = ?",
            (post_id, group_id)
        ).fetchone()
        return row is not None

    def get_favorite_post_ids(self, group_id: Optional[int] = None) -> List[int]:
        """Get all favorite post IDs, optionally filtered by group."""
        conn = self._get_connection()
        if group_id is not None:
            rows = conn.execute(
                "SELECT post_id FROM favorites WHERE group_id = ? ORDER BY added_at DESC",
                (group_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DISTINCT post_id FROM favorites ORDER BY MAX(added_at) DESC"
            ).fetchall()
        return [r['post_id'] for r in rows]

    def get_all_favorite_post_ids(self) -> List[int]:
        """Get all unique favorite post IDs across all groups."""
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT DISTINCT post_id FROM favorites"
        ).fetchall()
        return [r['post_id'] for r in rows]

    def get_favorites_by_group(self, group_id: int = 0) -> List[Favorite]:
        """Get all favorites in a specific group."""
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT post_id, group_id, added_at FROM favorites WHERE group_id = ? ORDER BY added_at DESC",
            (group_id,)
        ).fetchall()
        return [
            Favorite(post_id=r['post_id'], group_id=r['group_id'], added_at=r['added_at'])
            for r in rows
        ]

    def get_post_groups(self, post_id: int) -> List[int]:
        """Get all group IDs that contain this post."""
        conn = self._get_connection()
        rows = conn.execute(
            "SELECT group_id FROM favorites WHERE post_id = ?",
            (post_id,)
        ).fetchall()
        return [r['group_id'] for r in rows]

    def get_default_count(self) -> int:
        """Get count of posts in the default favorites group (group_id=0)."""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM favorites WHERE group_id = 0"
        ).fetchone()
        return row['cnt'] if row else 0

    def get_total_count(self) -> int:
        """Get total unique favorited posts count across all groups."""
        conn = self._get_connection()
        row = conn.execute(
            "SELECT COUNT(DISTINCT post_id) as cnt FROM favorites"
        ).fetchone()
        return row['cnt'] if row else 0

    def move_to_group(self, post_id: int, from_group_id: int, to_group_id: int) -> bool:
        """Move a post from one group to another."""
        conn = self._get_connection()
        try:
            conn.execute(
                "UPDATE favorites SET group_id = ? WHERE post_id = ? AND group_id = ?",
                (to_group_id, post_id, from_group_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Already exists in target group
            # Remove from source instead
            self.remove_favorite(post_id, from_group_id)
            return True
