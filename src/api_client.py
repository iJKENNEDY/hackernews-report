"""Hacker News API client for fetching posts."""

import requests
import logging
import time
from typing import Optional, List, Dict, Any
from functools import wraps

from src.models import Post


# Configure logging
logger = logging.getLogger(__name__)


class RetryStrategy:
    """
    Strategy for handling retries with exponential backoff.
    """
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
        """
        Initialize retry strategy.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds for exponential backoff
            max_delay: Maximum delay in seconds
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt using exponential backoff.
        
        Args:
            attempt: The attempt number (0-indexed)
            
        Returns:
            Delay in seconds (1s, 2s, 4s for attempts 0, 1, 2)
        """
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)


def retry(func):
    """
    Decorator to add retry logic with exponential backoff to API methods.
    
    Retries on network errors, timeouts, and HTTP errors.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        strategy = RetryStrategy(max_attempts=self.max_retries)
        last_exception = None
        
        for attempt in range(strategy.max_attempts):
            try:
                return func(self, *args, **kwargs)
            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < strategy.max_attempts - 1:
                    delay = strategy.calculate_delay(attempt)
                    logger.warning(
                        f"Request timeout (attempt {attempt + 1}/{strategy.max_attempts}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Request timed out after {strategy.max_attempts} attempts: {e}"
                    )
            except requests.exceptions.HTTPError as e:
                last_exception = e
                # Don't retry on 4xx client errors (except 429 rate limit)
                if e.response is not None and 400 <= e.response.status_code < 500:
                    if e.response.status_code == 429:
                        # Rate limit - retry with backoff
                        if attempt < strategy.max_attempts - 1:
                            delay = strategy.calculate_delay(attempt)
                            logger.warning(
                                f"Rate limit hit (attempt {attempt + 1}/{strategy.max_attempts}). "
                                f"Retrying in {delay}s..."
                            )
                            time.sleep(delay)
                        else:
                            logger.error(f"Rate limit exceeded after {strategy.max_attempts} attempts")
                            raise
                    else:
                        # Other 4xx errors - don't retry
                        logger.error(f"HTTP client error {e.response.status_code}: {e}")
                        raise
                else:
                    # 5xx server errors - retry
                    if attempt < strategy.max_attempts - 1:
                        delay = strategy.calculate_delay(attempt)
                        logger.warning(
                            f"HTTP error {e.response.status_code if e.response else 'unknown'} "
                            f"(attempt {attempt + 1}/{strategy.max_attempts}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"HTTP error after {strategy.max_attempts} attempts: {e}"
                        )
            except requests.exceptions.JSONDecodeError as e:
                last_exception = e
                logger.error(f"Invalid JSON response: {e}")
                # Don't retry on JSON errors - likely a persistent issue
                raise
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < strategy.max_attempts - 1:
                    delay = strategy.calculate_delay(attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{strategy.max_attempts}): {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"Request failed after {strategy.max_attempts} attempts: {e}"
                    )
        
        # If all retries failed, raise the last exception
        raise last_exception
    
    return wrapper


class HNApiClient:
    """
    Client for interacting with the Hacker News API.
    
    Attributes:
        base_url: Base URL for the Hacker News API
        max_retries: Maximum number of retry attempts for failed requests
        timeout: Request timeout in seconds
    """
    
    BASE_URL = "https://hacker-news.firebaseio.com/v0/"
    TIMEOUT = 10
    MAX_RETRIES = 3
    
    def __init__(
        self, 
        base_url: str = BASE_URL, 
        max_retries: int = MAX_RETRIES,
        timeout: int = TIMEOUT
    ):
        """
        Initialize the Hacker News API client.
        
        Args:
            base_url: Base URL for the API (default: official HN API)
            max_retries: Maximum retry attempts (default: 3)
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url.rstrip('/')
        self.max_retries = max_retries
        self.timeout = timeout
    
    @retry
    def get_top_stories(self, limit: int = 30) -> List[int]:
        """
        Get the IDs of top stories from Hacker News.
        
        Args:
            limit: Maximum number of story IDs to return (default: 30)
            
        Returns:
            List of story IDs
            
        Raises:
            requests.exceptions.RequestException: On network errors
        """
        url = f"{self.base_url}/topstories.json"
        logger.debug(f"Fetching top stories from {url}")
        
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        story_ids = response.json()
        
        # Validate response is a list
        if not isinstance(story_ids, list):
            logger.error(f"Invalid response format: expected list, got {type(story_ids)}")
            return []
        
        # Return up to 'limit' story IDs
        return story_ids[:limit]
    
    @retry
    def get_item(self, item_id: int) -> Optional[Post]:
        """
        Get a single item (post) by its ID.
        
        Args:
            item_id: The ID of the item to fetch
            
        Returns:
            Post object if successful and valid, None otherwise
            
        Raises:
            requests.exceptions.RequestException: On network errors
        """
        url = f"{self.base_url}/item/{item_id}.json"
        logger.debug(f"Fetching item {item_id} from {url}")
        
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        
        # Handle null response (deleted/dead items)
        if data is None:
            logger.warning(f"Item {item_id} returned null (deleted or dead)")
            return None
        
        # Validate data is a dictionary
        if not isinstance(data, dict):
            logger.error(f"Invalid response format for item {item_id}: expected dict, got {type(data)}")
            return None
        
        # Validate required fields are present
        required_fields = ["id", "type"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.warning(f"Item {item_id} missing required fields: {missing_fields}")
            return None
        
        # Additional validation for post-specific fields
        if "title" not in data or not data["title"]:
            logger.warning(f"Item {item_id} missing or empty title")
            return None
        
        if "by" not in data or not data["by"]:
            logger.warning(f"Item {item_id} missing or empty author")
            return None
        
        if "time" not in data:
            logger.warning(f"Item {item_id} missing timestamp")
            return None
        
        try:
            # Create Post from API response
            post = Post.from_api_response(data)
            
            # Validate the created post
            if not post.is_valid():
                logger.warning(f"Item {item_id} failed validation after creation")
                return None
            
            return post
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to create Post from item {item_id}: {e}")
            return None
    
    def get_items_batch(self, item_ids: List[int]) -> List[Post]:
        """
        Get multiple items in batch.
        
        Args:
            item_ids: List of item IDs to fetch
            
        Returns:
            List of valid Post objects (invalid/failed items are omitted)
        """
        posts = []
        
        for item_id in item_ids:
            try:
                post = self.get_item(item_id)
                if post is not None:
                    posts.append(post)
            except Exception as e:
                # Log error but continue processing other items
                logger.error(f"Failed to fetch item {item_id}: {e}")
                continue
        
        logger.info(f"Successfully fetched {len(posts)} out of {len(item_ids)} items")
        return posts

