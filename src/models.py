"""Data models for Hackernews Report application."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, Tuple
import time


class Category(Enum):
    """Post categories based on Hacker News post types."""
    STORY = "story"
    JOB = "job"
    ASK = "ask"
    POLL = "poll"
    OTHER = "other"


def categorize_post(post_type: str) -> Category:
    """
    Map a post type string to its corresponding Category.
    
    Args:
        post_type: The type string from Hacker News API
        
    Returns:
        The corresponding Category enum value, or Category.OTHER for unknown types
    """
    TYPE_TO_CATEGORY = {
        "story": Category.STORY,
        "job": Category.JOB,
        "ask": Category.ASK,
        "poll": Category.POLL,
    }
    return TYPE_TO_CATEGORY.get(post_type, Category.OTHER)


@dataclass
class Post:
    """
    Represents a Hacker News post.
    
    Attributes:
        id: Unique identifier for the post
        title: Post title
        author: Username of the post author
        score: Post score/points
        url: Optional URL associated with the post
        created_at: Unix timestamp when the post was created
        type: Post type (story, job, ask, poll, etc.)
        category: Categorized type as Category enum
        fetched_at: Unix timestamp when the post was fetched from API
    """
    id: int
    title: str
    author: str
    score: int
    url: Optional[str]
    created_at: int
    type: str
    category: Category
    fetched_at: int
    
    def is_valid(self) -> bool:
        """
        Validate that the post has all required fields with valid values.
        
        Returns:
            True if the post is valid, False otherwise
        """
        # Check required fields are not None/empty
        if not self.id or self.id <= 0:
            return False
        if not self.title or not isinstance(self.title, str):
            return False
        if not self.author or not isinstance(self.author, str):
            return False
        if not isinstance(self.score, int) or self.score < 0:
            return False
        if not self.type or not isinstance(self.type, str):
            return False
        if not isinstance(self.category, Category):
            return False
        if not isinstance(self.created_at, int) or self.created_at <= 0:
            return False
        if not isinstance(self.fetched_at, int) or self.fetched_at <= 0:
            return False
        # URL can be None, but if present must be a string
        if self.url is not None and not isinstance(self.url, str):
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the post to a dictionary representation.
        
        Returns:
            Dictionary with all post fields
        """
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "score": self.score,
            "url": self.url,
            "created_at": self.created_at,
            "type": self.type,
            "category": self.category.value,
            "fetched_at": self.fetched_at,
        }
    
    @staticmethod
    def from_api_response(data: Dict[str, Any]) -> "Post":
        """
        Create a Post instance from Hacker News API response data.
        
        Args:
            data: Dictionary containing API response fields
            
        Returns:
            Post instance created from the API data
            
        Raises:
            KeyError: If required fields are missing
            ValueError: If data types are invalid
        """
        # Extract required fields
        post_id = data["id"]
        title = data.get("title", "")
        author = data.get("by", "")
        score = data.get("score", 0)
        url = data.get("url")
        created_at = data.get("time", 0)
        post_type = data.get("type", "")
        
        # Categorize the post
        category = categorize_post(post_type)
        
        # Current timestamp for fetched_at
        fetched_at = int(time.time())
        
        return Post(
            id=post_id,
            title=title,
            author=author,
            score=score,
            url=url,
            created_at=created_at,
            type=post_type,
            category=category,
            fetched_at=fetched_at,
        )
    
    @staticmethod
    def from_db_row(row: Tuple) -> "Post":
        """
        Create a Post instance from a database row tuple.
        
        Args:
            row: Tuple containing database row values in order:
                 (id, title, author, score, url, created_at, type, category, fetched_at)
                 
        Returns:
            Post instance created from the database row
        """
        # Unpack the row tuple
        (post_id, title, author, score, url, created_at, 
         post_type, category_str, fetched_at) = row
        
        # Convert category string back to enum
        category = Category(category_str)
        
        return Post(
            id=post_id,
            title=title,
            author=author,
            score=score,
            url=url,
            created_at=created_at,
            type=post_type,
            category=category,
            fetched_at=fetched_at,
        )
