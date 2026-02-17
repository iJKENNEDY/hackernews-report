"""Database layer for Hackernews Report application."""

import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Tuple
from pathlib import Path

from src.models import Post, Category


class Database:
    """
    SQLite database manager for storing and retrieving Hacker News posts.
    
    Attributes:
        db_path: Path to the SQLite database file
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the Database with a path to the SQLite database file.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get or create a database connection.
        
        Returns:
            SQLite connection object
        """
        if self._connection is None:
            # Ensure parent directory exists
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)
            
            self._connection = sqlite3.connect(self.db_path)
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
            
        return self._connection
    
    def initialize_schema(self) -> None:
        """
        Create the database schema with tables and indices if they don't exist.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                url TEXT,
                created_at INTEGER NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                fetched_at INTEGER NOT NULL,
                tags TEXT DEFAULT ''
            )
        """)
        
        # Create indices for optimized queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_type 
            ON posts(type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_category 
            ON posts(category)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_created_at 
            ON posts(created_at DESC)
        """)
        
        # Create search indices for optimized search queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_title_lower 
            ON posts(LOWER(title))
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_author_lower 
            ON posts(LOWER(author))
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_tags 
            ON posts(tags)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_score 
            ON posts(score)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_score_created 
            ON posts(score DESC, created_at DESC)
        """)
        
        conn.commit()
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        
        Provides automatic commit on success and rollback on error.
        
        Yields:
            SQLite connection object
            
        Example:
            with db.transaction() as conn:
                conn.execute("INSERT INTO posts ...")
        """
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def close(self) -> None:
        """Close the database connection if open."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes connection."""
        self.close()

    def insert_post(self, post: Post) -> bool:
        """
        Insert a new post into the database.
        
        Args:
            post: Post object to insert
            
        Returns:
            True if insertion was successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Convert tags list to comma-separated string
            tags_str = ','.join(post.tags) if post.tags else ''
            
            cursor.execute("""
                INSERT INTO posts (id, title, author, score, url, created_at, type, category, fetched_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post.id,
                post.title,
                post.author,
                post.score,
                post.url,
                post.created_at,
                post.type,
                post.category.value,
                post.fetched_at,
                tags_str,
            ))
            
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Post with this ID already exists
            return False
        except Exception:
            return False
    
    def update_post(self, post: Post) -> bool:
        """
        Update an existing post in the database.
        
        Args:
            post: Post object with updated data
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Convert tags list to comma-separated string
            tags_str = ','.join(post.tags) if post.tags else ''
            
            cursor.execute("""
                UPDATE posts
                SET title = ?, author = ?, score = ?, url = ?, 
                    created_at = ?, type = ?, category = ?, fetched_at = ?, tags = ?
                WHERE id = ?
            """, (
                post.title,
                post.author,
                post.score,
                post.url,
                post.created_at,
                post.type,
                post.category.value,
                post.fetched_at,
                tags_str,
                post.id,
            ))
            
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
    
    def upsert_post(self, post: Post) -> bool:
        """
        Insert a post or update it if it already exists (by ID).
        
        Args:
            post: Post object to insert or update
            
        Returns:
            True if operation was successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO posts (id, title, author, score, url, created_at, type, category, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    author = excluded.author,
                    score = excluded.score,
                    url = excluded.url,
                    created_at = excluded.created_at,
                    type = excluded.type,
                    category = excluded.category,
                    fetched_at = excluded.fetched_at
            """, (
                post.id,
                post.title,
                post.author,
                post.score,
                post.url,
                post.created_at,
                post.type,
                post.category.value,
                post.fetched_at,
            ))
            
            conn.commit()
            return True
        except Exception:
            return False
    
    def get_post_by_id(self, post_id: int) -> Optional[Post]:
        """
        Retrieve a post by its ID.
        
        Args:
            post_id: The ID of the post to retrieve
            
        Returns:
            Post object if found, None otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, author, score, url, created_at, type, category, fetched_at
                FROM posts
                WHERE id = ?
            """, (post_id,))
            
            row = cursor.fetchone()
            if row:
                return Post.from_db_row(row)
            return None
        except Exception:
            return None
    
    def post_exists(self, post_id: int) -> bool:
        """
        Check if a post with the given ID exists in the database.
        
        Args:
            post_id: The ID of the post to check
            
        Returns:
            True if the post exists, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 1 FROM posts WHERE id = ? LIMIT 1
            """, (post_id,))
            
            return cursor.fetchone() is not None
        except Exception:
            return False

    def get_posts_by_category(
        self, 
        category: Optional[Category] = None, 
        order_by: str = "created_desc"
    ) -> List[Post]:
        """
        Retrieve posts, optionally filtered by category.
        
        Args:
            category: Optional category to filter by. If None, returns all posts.
            order_by: Ordering method. Options: "created_desc" (default), "created_asc", "score_desc"
            
        Returns:
            List of Post objects matching the criteria
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build query based on filter
            if category is not None:
                query = """
                    SELECT id, title, author, score, url, created_at, type, category, fetched_at
                    FROM posts
                    WHERE category = ?
                """
                params = (category.value,)
            else:
                query = """
                    SELECT id, title, author, score, url, created_at, type, category, fetched_at
                    FROM posts
                """
                params = ()
            
            # Add ordering
            if order_by == "created_asc":
                query += " ORDER BY created_at ASC"
            elif order_by == "score_desc":
                query += " ORDER BY score DESC"
            else:  # created_desc (default)
                query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [Post.from_db_row(row) for row in rows]
        except Exception:
            return []
    
    def get_category_counts(self) -> Dict[str, int]:
        """
        Get the count of posts for each category.
        
        Returns:
            Dictionary mapping category names to post counts
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT category, COUNT(*) as count
                FROM posts
                GROUP BY category
            """)
            
            rows = cursor.fetchall()
            return {category: count for category, count in rows}
        except Exception:
            return {}
