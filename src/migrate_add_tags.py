"""Migration script to add tags column to posts table."""

import sqlite3
import sys
from pathlib import Path

from src.config import DB_PATH
from src.tags import TagSystem


def migrate_add_tags_column(db_path: str = DB_PATH):
    """
    Add tags column to posts table and populate it for existing posts.
    
    Args:
        db_path: Path to the SQLite database
    """
    print(f"Migrating database at: {db_path}")
    
    # Check if database exists
    if not Path(db_path).exists():
        print("Database doesn't exist yet. No migration needed.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if tags column already exists
        cursor.execute("PRAGMA table_info(posts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'tags' in columns:
            print("Tags column already exists. Migration not needed.")
            return
        
        print("Adding tags column to posts table...")
        
        # Add tags column
        cursor.execute("""
            ALTER TABLE posts 
            ADD COLUMN tags TEXT DEFAULT ''
        """)
        
        print("Tags column added successfully.")
        
        # Populate tags for existing posts
        print("Populating tags for existing posts...")
        
        cursor.execute("SELECT id, title FROM posts")
        posts = cursor.fetchall()
        
        updated_count = 0
        for post_id, title in posts:
            # Extract tags from title
            tags = TagSystem.extract_tags(title)
            tags_str = ','.join(tags) if tags else ''
            
            # Update post with tags
            cursor.execute(
                "UPDATE posts SET tags = ? WHERE id = ?",
                (tags_str, post_id)
            )
            updated_count += 1
        
        conn.commit()
        print(f"Successfully updated {updated_count} posts with tags.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        sys.exit(1)
    finally:
        conn.close()
    
    print("Migration completed successfully!")


if __name__ == "__main__":
    migrate_add_tags_column()
