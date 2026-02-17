"""Search engine for querying Hacker News posts."""

from typing import List, Tuple, Any, Optional
import math
import datetime

from src.database import Database
from src.models import SearchQuery, SearchResult, Post


class SearchEngine:
    """
    Search engine for executing queries against the posts database.

    Provides text search, filtering, sorting, and pagination capabilities
    for Hacker News posts stored in SQLite.
    """

    def __init__(self, database: Database):
        """
        Initialize the SearchEngine with a database connection.

        Args:
            database: Database instance for executing queries
        """
        self.database = database

    def search(self, query: SearchQuery) -> SearchResult:
        """
        Execute a search query and return paginated results.

        Args:
            query: SearchQuery object with search criteria

        Returns:
            SearchResult with matching posts and pagination metadata
        """
        # Validate query
        errors = query.validate()
        if errors:
            raise ValueError(f"Invalid search query: {', '.join(errors)}")

        # Count total results
        total_results = self.count_results(query)

        # Calculate pagination
        total_pages = math.ceil(total_results / query.page_size) if total_results > 0 else 0

        # If page is out of range, return empty result
        if query.page > total_pages and total_pages > 0:
            return SearchResult(
                posts=[],
                total_results=total_results,
                page=query.page,
                page_size=query.page_size,
                total_pages=total_pages,
                query=query
            )

        # Build and execute SQL query
        sql, params = self._build_sql_query(query)
        conn = self.database._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Convert rows to Post objects
        posts = [Post.from_db_row(row) for row in rows]

        # Apply relevance sorting if needed
        if query.order_by == "relevance" and query.has_text_search():
            posts = self._sort_by_relevance(posts, query.text)

        return SearchResult(
            posts=posts,
            total_results=total_results,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages,
            query=query
        )

    def count_results(self, query: SearchQuery) -> int:
        """
        Count the total number of results for a query without pagination.

        Args:
            query: SearchQuery object with search criteria

        Returns:
            Total number of matching posts
        """
        conditions = []
        params = []

        # Apply text filter
        if query.has_text_search():
            self._apply_text_filter(conditions, params, query.text)

        # Apply author filter
        if query.author:
            self._apply_author_filter(conditions, params, query.author)

        # Apply tags filter
        if query.tags:
            self._apply_tags_filter(conditions, params, query.tags)

        # Apply score filter
        if query.min_score is not None or query.max_score is not None:
            self._apply_score_filter(conditions, params, query.min_score, query.max_score)

        # Apply date filter
        if query.start_date is not None or query.end_date is not None:
            self._apply_date_filter(conditions, params, query.start_date, query.end_date)

        # Build count query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        sql = f"SELECT COUNT(*) FROM posts WHERE {where_clause}"

        conn = self.database._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchone()

        return result[0] if result else 0

    def create_search_indices(self) -> None:
        """
        Create database indices to optimize search queries.

        Creates indices on:
        - LOWER(title) for text search
        - LOWER(author) for author search
        - tags for tag filtering
        - score for score filtering
        - (score DESC, created_at DESC) composite index for common sorting

        This method is idempotent - it can be called multiple times safely.
        """
        conn = self.database._get_connection()
        cursor = conn.cursor()

        # Index for text search on titles (case-insensitive)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_title_lower 
            ON posts(LOWER(title))
        """)

        # Index for author search (case-insensitive)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_author_lower 
            ON posts(LOWER(author))
        """)

        # Index for tag filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_tags 
            ON posts(tags)
        """)

        # Index for score filtering
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_score 
            ON posts(score)
        """)

        # Composite index for common sorting pattern (score + date)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_posts_score_created 
            ON posts(score DESC, created_at DESC)
        """)

        conn.commit()

    def _build_sql_query(self, query: SearchQuery) -> Tuple[str, List[Any]]:
        """
        Build SQL query string and parameters from SearchQuery.

        Args:
            query: SearchQuery object with search criteria

        Returns:
            Tuple of (SQL query string, parameter list)
        """
        conditions = []
        params = []

        # Apply text filter
        if query.has_text_search():
            self._apply_text_filter(conditions, params, query.text)

        # Apply author filter
        if query.author:
            self._apply_author_filter(conditions, params, query.author)

        # Apply tags filter
        if query.tags:
            self._apply_tags_filter(conditions, params, query.tags)

        # Apply score filter
        if query.min_score is not None or query.max_score is not None:
            self._apply_score_filter(conditions, params, query.min_score, query.max_score)

        # Apply date filter
        if query.start_date is not None or query.end_date is not None:
            self._apply_date_filter(conditions, params, query.start_date, query.end_date)

        # Build WHERE clause
        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Build ORDER BY clause
        order_clause = self._get_order_clause(query.order_by, query.has_text_search())

        # Calculate LIMIT and OFFSET for pagination
        limit = query.page_size
        offset = (query.page - 1) * query.page_size

        # Build complete query
        sql = f"""
            SELECT id, title, author, score, url, created_at, type, category, fetched_at, tags
            FROM posts
            WHERE {where_clause}
            {order_clause}
            LIMIT ? OFFSET ?
        """

        params.extend([limit, offset])

        return sql, params

    def _apply_text_filter(self, conditions: List[str], params: List[Any], text: str) -> None:
        """
        Apply text search filter to query conditions.

        Implements case-insensitive substring matching for multiple words (AND operation).

        Args:
            conditions: List to append SQL conditions to
            params: List to append SQL parameters to
            text: Text to search for in titles
        """
        # Split text into words for multi-word search
        words = text.strip().split()

        # Each word must appear in the title (AND operation)
        for word in words:
            conditions.append("LOWER(title) LIKE ?")
            params.append(f"%{word.lower()}%")

    def _apply_author_filter(self, conditions: List[str], params: List[Any], author: str) -> None:
        """
        Apply author search filter to query conditions.

        Implements case-insensitive substring matching for author names.

        Args:
            conditions: List to append SQL conditions to
            params: List to append SQL parameters to
            author: Author name to search for
        """
        conditions.append("LOWER(author) LIKE ?")
        params.append(f"%{author.lower()}%")

    def _apply_tags_filter(self, conditions: List[str], params: List[Any], tags: List[str]) -> None:
        """
        Apply tags search filter to query conditions.

        Implements OR operation for multiple tags - posts matching any of the tags are returned.

        Args:
            conditions: List to append SQL conditions to
            params: List to append SQL parameters to
            tags: List of tag names to search for
        """
        # Build OR conditions for tags
        tag_conditions = []
        for tag in tags:
            tag_conditions.append("tags LIKE ?")
            params.append(f"%{tag}%")

        # Combine tag conditions with OR and wrap in parentheses
        if tag_conditions:
            conditions.append(f"({' OR '.join(tag_conditions)})")

    def _apply_score_filter(self, conditions: List[str], params: List[Any],
                           min_score: Optional[int], max_score: Optional[int]) -> None:
        """
        Apply score range filter to query conditions.

        Args:
            conditions: List to append SQL conditions to
            params: List to append SQL parameters to
            min_score: Minimum score threshold (inclusive)
            max_score: Maximum score threshold (inclusive)
        """
        if min_score is not None:
            conditions.append("score >= ?")
            params.append(min_score)

        if max_score is not None:
            conditions.append("score <= ?")
            params.append(max_score)

    def _apply_date_filter(self, conditions: List[str], params: List[Any],
                          start_date: Optional[Any], end_date: Optional[Any]) -> None:
        """
        Apply date range filter to query conditions.

        Converts date objects to Unix timestamps for comparison with created_at field.

        Args:
            conditions: List to append SQL conditions to
            params: List to append SQL parameters to
            start_date: Start date (inclusive) as datetime.date object
            end_date: End date (inclusive) as datetime.date object
        """
        if start_date is not None:
            # Convert date to Unix timestamp (start of day in UTC)
            start_timestamp = int(datetime.datetime.combine(
                start_date, datetime.time.min, tzinfo=datetime.timezone.utc
            ).timestamp())
            conditions.append("created_at >= ?")
            params.append(start_timestamp)

        if end_date is not None:
            # Convert date to Unix timestamp (end of day in UTC)
            end_timestamp = int(datetime.datetime.combine(
                end_date, datetime.time.max, tzinfo=datetime.timezone.utc
            ).timestamp())
            conditions.append("created_at <= ?")
            params.append(end_timestamp)

    def _get_order_clause(self, order_by: str, has_text_search: bool) -> str:
        """
        Get SQL ORDER BY clause based on ordering preference.

        Applies default ordering when order_by is "relevance":
        - If text search is present: orders by relevance (handled in post-processing)
        - If no text search: orders by date descending

        Args:
            order_by: Ordering preference (relevance, date_desc, date_asc, score_desc, score_asc)
            has_text_search: Whether the query includes text search

        Returns:
            SQL ORDER BY clause
        """
        if order_by == "date_asc":
            return "ORDER BY created_at ASC"
        if order_by == "date_desc":
            return "ORDER BY created_at DESC"
        if order_by == "score_asc":
            return "ORDER BY score ASC"
        if order_by == "score_desc":
            return "ORDER BY score DESC"
        if order_by == "relevance":
            # Relevance ordering requires post-processing with text matching
            # For now, fetch in date order and we'll sort by relevance after
            if has_text_search:
                # Return empty string - we'll sort by relevance in Python
                return ""
            # No text search, default to date descending
            return "ORDER BY created_at DESC"
        # Default to date descending
        return "ORDER BY created_at DESC"

    def _calculate_relevance_score(self, text: str, title: str) -> float:
        """
        Calculate relevance score for a post title based on search text.

        Scoring algorithm:
        - Exact match of whole phrase: +10 points
        - Each word found at start of title: +5 points per word
        - Each word found anywhere in title: +1 point per word
        - Score normalized by title length to favor shorter, more focused titles

        Args:
            text: Search text (may contain multiple words)
            title: Post title to score

        Returns:
            Relevance score (higher is more relevant)
        """
        text_lower = text.lower().strip()
        title_lower = title.lower()
        
        score = 0.0
        
        # Exact phrase match gets highest score
        if text_lower in title_lower:
            score += 10.0
            
            # Bonus if match is at the start
            if title_lower.startswith(text_lower):
                score += 5.0
        
        # Score individual words
        words = text_lower.split()
        for word in words:
            if word in title_lower:
                # Word found anywhere
                score += 1.0
                
                # Bonus if word is at the start
                if title_lower.startswith(word):
                    score += 5.0
        
        # Normalize by title length (favor shorter, more focused titles)
        # Add 1 to avoid division by zero
        normalized_score = score / (len(title) / 10.0 + 1.0)
        
        return normalized_score

    def _sort_by_relevance(self, posts: List[Post], text: str) -> List[Post]:
        """
        Sort posts by relevance to search text.

        Args:
            posts: List of posts to sort
            text: Search text to calculate relevance against

        Returns:
            Sorted list of posts (highest relevance first)
        """
        # Calculate relevance score for each post and sort
        posts_with_scores = [
            (post, self._calculate_relevance_score(text, post.title))
            for post in posts
        ]
        
        # Sort by score descending (highest relevance first)
        posts_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the posts
        return [post for post, score in posts_with_scores]
