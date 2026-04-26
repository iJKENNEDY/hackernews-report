"""Application service layer for Hackernews Report."""

import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

from src.api_client import HNApiClient
from src.database import Database
from src.models import Post, Category


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class FetchResult:
    """
    Result of a fetch and store operation.
    
    Attributes:
        new_posts: Number of new posts inserted
        updated_posts: Number of existing posts updated
        errors: List of error messages encountered during the operation
    """
    new_posts: int
    updated_posts: int
    errors: List[str]
    new_post_ids: List[int]


class HackerNewsService:
    """
    Application service that orchestrates operations between API client and database.
    
    This service coordinates fetching posts from Hacker News API, validating them,
    categorizing them, and storing them in the database.
    
    Attributes:
        api_client: Client for interacting with Hacker News API
        database: Database layer for storing and retrieving posts
    """
    
    def __init__(self, api_client: HNApiClient, database: Database):
        """
        Initialize the HackerNewsService.
        
        Args:
            api_client: Configured HNApiClient instance
            database: Configured Database instance
        """
        self.api_client = api_client
        self.database = database

    def _fetch_story_ids_with_backfill(self, limit: int, source: str = "top") -> List[int]:
        """
        Fetch story IDs with DB-aware backfill to avoid missing new posts.

        If many IDs in the first page are already stored, this keeps reading
        additional IDs from the same source and only returns up to `limit`
        IDs that are not yet present in the database.
        """
        max_scan = max(limit * 20, 500)
        if source == "new":
            all_ids = self.api_client.get_new_stories(limit=max_scan)
        elif source == "top":
            all_ids = self.api_client.get_top_stories(limit=max_scan)
        else:
            top_ids = self.api_client.get_top_stories(limit=max_scan)
            new_ids = self.api_client.get_new_stories(limit=max_scan)
            all_ids = list(dict.fromkeys([*top_ids, *new_ids]))

        if not all_ids:
            return []

        selected_ids: List[int] = []
        selected_set = set()

        # Pass 1: prioritize unseen posts so new items are not skipped
        for story_id in all_ids:
            if not self.database.post_exists(story_id):
                selected_ids.append(story_id)
                selected_set.add(story_id)
                if len(selected_ids) >= limit:
                    break

        # Pass 2: fill with already-known posts to keep the refresh complete
        if len(selected_ids) < limit:
            for story_id in all_ids:
                if story_id not in selected_set:
                    selected_ids.append(story_id)
                    selected_set.add(story_id)
                    if len(selected_ids) >= limit:
                        break

        return selected_ids

    def fetch_and_store_posts(self, limit: int = 30, source: str = "top") -> FetchResult:
        """
        Fetch posts from Hacker News API and store them in the database.
        
        This method:
        1. Fetches top story IDs from the API
        2. Retrieves full post data for each ID
        3. Validates and categorizes each post
        4. Stores posts in the database using transactions for atomicity
        5. Handles errors gracefully, continuing with valid posts
        
        Args:
            limit: Maximum number of posts to fetch (default: 30)
            source: Story source: "top", "new", or "mixed" (default: "top")
            
        Returns:
            FetchResult with counts of new/updated posts and any errors
        """
        new_posts = 0
        updated_posts = 0
        errors = []
        new_post_ids: List[int] = []
        
        try:
            if source not in ("top", "new", "mixed"):
                raise ValueError("source must be 'top', 'new', or 'mixed'")

            # Fetch story IDs with backfill from the selected source
            logger.info(f"Fetching up to {limit} {source} story IDs from Hacker News API")
            story_ids = self._fetch_story_ids_with_backfill(limit=limit, source=source)
            
            if not story_ids:
                error_msg = "No story IDs retrieved from API"
                logger.warning(error_msg)
                errors.append(error_msg)
                return FetchResult(new_posts=0, updated_posts=0, errors=errors, new_post_ids=[])
            
            logger.info(f"Retrieved {len(story_ids)} story IDs")
            
            # Fetch full post data for each ID
            posts = self.api_client.get_items_batch(story_ids)
            
            if not posts:
                error_msg = "No valid posts retrieved from API"
                logger.warning(error_msg)
                errors.append(error_msg)
                return FetchResult(new_posts=0, updated_posts=0, errors=errors, new_post_ids=[])
            
            logger.info(f"Retrieved {len(posts)} valid posts")
            
            # Store posts in database using transaction for atomicity
            with self.database.transaction():
                for post in posts:
                    try:
                        # Validate post before storing
                        if not post.is_valid():
                            error_msg = f"Post {post.id} failed validation"
                            logger.warning(error_msg)
                            errors.append(error_msg)
                            continue
                        
                        # Check if post already exists
                        exists = self.database.post_exists(post.id)
                        
                        # Upsert the post
                        success = self.database.upsert_post(post)
                        
                        if success:
                            if exists:
                                updated_posts += 1
                                logger.debug(f"Updated post {post.id}: {post.title}")
                            else:
                                new_posts += 1
                                new_post_ids.append(post.id)
                                logger.debug(f"Inserted new post {post.id}: {post.title}")
                        else:
                            error_msg = f"Failed to store post {post.id}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                            
                    except Exception as e:
                        # Log error but continue with other posts
                        error_msg = f"Error processing post {post.id}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue
            
            logger.info(
                f"Fetch complete: {new_posts} new posts, {updated_posts} updated posts, "
                f"{len(errors)} errors"
            )
            
        except Exception as e:
            # Catch any unexpected errors at the top level
            error_msg = f"Unexpected error during fetch operation: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return FetchResult(
            new_posts=new_posts,
            updated_posts=updated_posts,
            errors=errors,
            new_post_ids=new_post_ids
        )

    def get_posts_by_category(self, category: Optional[Category] = None) -> List[Post]:
        """
        Retrieve posts from the database, optionally filtered by category.
        
        Posts are returned in descending order by creation date (most recent first).
        
        Args:
            category: Optional category to filter by. If None, returns all posts.
            
        Returns:
            List of Post objects matching the criteria
        """
        logger.debug(f"Retrieving posts for category: {category.value if category else 'all'}")
        posts = self.database.get_posts_by_category(category=category, order_by="created_desc")
        logger.info(f"Retrieved {len(posts)} posts")
        return posts
    
    def get_category_statistics(self) -> Dict[str, int]:
        """
        Get statistics on the number of posts per category.
        
        Returns:
            Dictionary mapping category names to post counts
        """
        logger.debug("Retrieving category statistics")
        stats = self.database.get_category_counts()
        logger.info(f"Category statistics: {stats}")
        return stats
