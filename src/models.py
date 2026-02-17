"""Data models for Hackernews Report application."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, Tuple, List
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
        tags: List of topic tags (AI, Python, Science, etc.)
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
    tags: List[str] = field(default_factory=list)
    
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
            "tags": self.tags,
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
        from src.tags import TagSystem
        
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
        
        # Extract tags from title
        tags = TagSystem.extract_tags(title)
        
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
            tags=tags,
        )
    
    @staticmethod
    def from_db_row(row: Tuple) -> "Post":
        """
        Create a Post instance from a database row tuple.
        
        Args:
            row: Tuple containing database row values in order:
                 (id, title, author, score, url, created_at, type, category, fetched_at, tags)
                 
        Returns:
            Post instance created from the database row
        """
        # Unpack the row tuple (handle both old and new schema)
        if len(row) == 9:
            # Old schema without tags
            (post_id, title, author, score, url, created_at, 
             post_type, category_str, fetched_at) = row
            tags = []
        else:
            # New schema with tags
            (post_id, title, author, score, url, created_at, 
             post_type, category_str, fetched_at, tags_str) = row
            # Parse tags from comma-separated string
            tags = tags_str.split(',') if tags_str else []
        
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
            tags=tags,
        )



@dataclass(frozen=True)
class SearchQuery:
    """
    Immutable search query with validation.
    
    Encapsulates all search criteria and presentation options for searching posts.
    All validation is performed in the validate() method.
    
    Attributes:
        text: Optional text to search in post titles
        author: Optional author name to filter by
        tags: Optional list of tags to filter by (OR operation)
        min_score: Optional minimum score threshold
        max_score: Optional maximum score threshold
        start_date: Optional start date for filtering (datetime.date)
        end_date: Optional end date for filtering (datetime.date)
        order_by: Sort order (relevance, date_desc, date_asc, score_desc, score_asc)
        page: Page number (1-indexed)
        page_size: Number of results per page
    """
    text: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    start_date: Optional[Any] = None  # datetime.date
    end_date: Optional[Any] = None    # datetime.date
    order_by: str = "relevance"
    page: int = 1
    page_size: int = 20
    
    def validate(self) -> List[str]:
        """
        Validate the query and return list of validation errors.
        
        Returns:
            List of error messages. Empty list if query is valid.
        """
        errors = []
        
        # At least one criterion must be present
        if not self.has_any_criteria():
            errors.append("At least one search criterion must be provided")
        
        # Validate score ranges
        if self.min_score is not None and self.min_score < 0:
            errors.append("min_score must be non-negative")
        if self.max_score is not None and self.max_score < 0:
            errors.append("max_score must be non-negative")
        if (self.min_score is not None and self.max_score is not None 
            and self.min_score > self.max_score):
            errors.append("min_score must be <= max_score")
        
        # Validate date ranges
        if (self.start_date is not None and self.end_date is not None 
            and self.start_date > self.end_date):
            errors.append("start_date must be <= end_date")
        
        # Validate pagination
        if self.page < 1:
            errors.append("page must be >= 1")
        if self.page_size < 1 or self.page_size > 100:
            errors.append("page_size must be between 1 and 100")
        
        # Validate order_by
        valid_orders = ["relevance", "date_desc", "date_asc", "score_desc", "score_asc"]
        if self.order_by not in valid_orders:
            errors.append(f"order_by must be one of: {', '.join(valid_orders)}")
        
        # Validate text is not empty or whitespace only
        if self.text is not None and not self.text.strip():
            errors.append("text search term cannot be empty or whitespace only")
        
        return errors
    
    def has_text_search(self) -> bool:
        """
        Check if the query includes text search.
        
        Returns:
            True if text search is present and non-empty
        """
        return self.text is not None and len(self.text.strip()) > 0
    
    def has_any_criteria(self) -> bool:
        """
        Check if at least one search criterion is present.
        
        Returns:
            True if at least one criterion is specified
        """
        return any([
            self.text,
            self.author,
            self.tags,
            self.min_score is not None,
            self.max_score is not None,
            self.start_date is not None,
            self.end_date is not None,
        ])


@dataclass
class SearchResult:
    """
    Search results with pagination metadata.
    
    Encapsulates the results of a search query along with pagination information.
    
    Attributes:
        posts: List of Post objects matching the search criteria
        total_results: Total number of results across all pages
        page: Current page number (1-indexed)
        page_size: Number of results per page
        total_pages: Total number of pages available
        query: The SearchQuery that produced these results
    """
    posts: List[Post]
    total_results: int
    page: int
    page_size: int
    total_pages: int
    query: SearchQuery
    
    def has_more_pages(self) -> bool:
        """
        Check if there are more pages after the current one.
        
        Returns:
            True if current page is not the last page
        """
        return self.page < self.total_pages
    
    def has_previous_page(self) -> bool:
        """
        Check if there is a previous page before the current one.
        
        Returns:
            True if current page is not the first page
        """
        return self.page > 1
    
    def get_page_info(self) -> str:
        """
        Get a formatted string with pagination information.
        
        Returns:
            String like "Page 2 of 5 (100 total results)"
        """
        return f"Page {self.page} of {self.total_pages} ({self.total_results} total results)"
