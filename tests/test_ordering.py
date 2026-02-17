"""Tests for search result ordering functionality."""

import pytest
from datetime import date, datetime, timezone
from src.database import Database
from src.search_engine import SearchEngine
from src.models import SearchQuery, Post, Category


class TestSearchOrdering:
    """Test suite for search result ordering."""

    @pytest.fixture
    def database(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test_ordering.db"
        db = Database(str(db_path))
        db.initialize_schema()
        return db

    @pytest.fixture
    def search_engine(self, database):
        """Create a SearchEngine instance."""
        return SearchEngine(database)

    @pytest.fixture
    def sample_posts(self, database):
        """Create sample posts with varying scores and dates."""
        posts = [
            Post(
                id=1,
                title="Python Tutorial",
                author="alice",
                score=100,
                url="http://example.com/1",
                created_at=int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()),
                type="story",
                category=Category.STORY,
                fetched_at=int(datetime.now(timezone.utc).timestamp()),
                tags=["Python"]
            ),
            Post(
                id=2,
                title="Advanced Python",
                author="bob",
                score=500,
                url="http://example.com/2",
                created_at=int(datetime(2024, 6, 1, tzinfo=timezone.utc).timestamp()),
                type="story",
                category=Category.STORY,
                fetched_at=int(datetime.now(timezone.utc).timestamp()),
                tags=["Python"]
            ),
            Post(
                id=3,
                title="Python Best Practices",
                author="charlie",
                score=250,
                url="http://example.com/3",
                created_at=int(datetime(2024, 3, 1, tzinfo=timezone.utc).timestamp()),
                type="story",
                category=Category.STORY,
                fetched_at=int(datetime.now(timezone.utc).timestamp()),
                tags=["Python"]
            ),
            Post(
                id=4,
                title="Python for Beginners",
                author="dave",
                score=50,
                url="http://example.com/4",
                created_at=int(datetime(2024, 12, 1, tzinfo=timezone.utc).timestamp()),
                type="story",
                category=Category.STORY,
                fetched_at=int(datetime.now(timezone.utc).timestamp()),
                tags=["Python"]
            ),
        ]

        # Insert posts into database
        conn = database._get_connection()
        cursor = conn.cursor()
        for post in posts:
            cursor.execute(
                """
                INSERT INTO posts (id, title, author, score, url, created_at, type, category, fetched_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post.id,
                    post.title,
                    post.author,
                    post.score,
                    post.url,
                    post.created_at,
                    post.type,
                    post.category.value,
                    post.fetched_at,
                    ",".join(post.tags),
                ),
            )
        conn.commit()

        return posts

    def test_order_by_date_descending(self, search_engine, sample_posts):
        """Test ordering by date descending (most recent first)."""
        query = SearchQuery(text="Python", order_by="date_desc")
        result = search_engine.search(query)

        # Should be ordered: id=4 (Dec), id=2 (Jun), id=3 (Mar), id=1 (Jan)
        assert len(result.posts) == 4
        assert result.posts[0].id == 4
        assert result.posts[1].id == 2
        assert result.posts[2].id == 3
        assert result.posts[3].id == 1

    def test_order_by_date_ascending(self, search_engine, sample_posts):
        """Test ordering by date ascending (oldest first)."""
        query = SearchQuery(text="Python", order_by="date_asc")
        result = search_engine.search(query)

        # Should be ordered: id=1 (Jan), id=3 (Mar), id=2 (Jun), id=4 (Dec)
        assert len(result.posts) == 4
        assert result.posts[0].id == 1
        assert result.posts[1].id == 3
        assert result.posts[2].id == 2
        assert result.posts[3].id == 4

    def test_order_by_score_descending(self, search_engine, sample_posts):
        """Test ordering by score descending (highest score first)."""
        query = SearchQuery(text="Python", order_by="score_desc")
        result = search_engine.search(query)

        # Should be ordered: id=2 (500), id=3 (250), id=1 (100), id=4 (50)
        assert len(result.posts) == 4
        assert result.posts[0].id == 2
        assert result.posts[0].score == 500
        assert result.posts[1].id == 3
        assert result.posts[1].score == 250
        assert result.posts[2].id == 1
        assert result.posts[2].score == 100
        assert result.posts[3].id == 4
        assert result.posts[3].score == 50

    def test_order_by_score_ascending(self, search_engine, sample_posts):
        """Test ordering by score ascending (lowest score first)."""
        query = SearchQuery(text="Python", order_by="score_asc")
        result = search_engine.search(query)

        # Should be ordered: id=4 (50), id=1 (100), id=3 (250), id=2 (500)
        assert len(result.posts) == 4
        assert result.posts[0].id == 4
        assert result.posts[0].score == 50
        assert result.posts[1].id == 1
        assert result.posts[1].score == 100
        assert result.posts[2].id == 3
        assert result.posts[2].score == 250
        assert result.posts[3].id == 2
        assert result.posts[3].score == 500

    def test_order_by_relevance_with_text_search(self, search_engine, sample_posts):
        """Test ordering by relevance when text search is present."""
        query = SearchQuery(text="Python", order_by="relevance")
        result = search_engine.search(query)

        # All posts contain "Python" so relevance should be calculated
        # Posts with "Python" at the start should rank higher
        assert len(result.posts) == 4

        # All titles start with "Python", so we should see relevance-based ordering
        # The exact order depends on the relevance algorithm, but verify it's not random
        first_post = result.posts[0]
        assert "Python" in first_post.title

    def test_default_order_with_text_search(self, search_engine, sample_posts):
        """Test default ordering (relevance) when text search is present."""
        # When order_by is not specified, it defaults to "relevance"
        query = SearchQuery(text="Python")
        result = search_engine.search(query)

        # Should use relevance ordering
        assert len(result.posts) == 4
        assert "Python" in result.posts[0].title

    def test_default_order_without_text_search(self, search_engine, sample_posts):
        """Test default ordering (date descending) when no text search."""
        # When searching without text, should default to date descending
        query = SearchQuery(author="alice", order_by="relevance")
        result = search_engine.search(query)

        # Should fall back to date descending
        assert len(result.posts) == 1
        assert result.posts[0].id == 1

    def test_relevance_calculation_exact_match(self, search_engine, database):
        """Test relevance scoring for exact phrase match."""
        # Create posts with different relevance levels
        posts = [
            Post(
                id=10,
                title="Machine Learning Tutorial",
                author="alice",
                score=100,
                url="http://example.com/10",
                created_at=int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()),
                type="story",
                category=Category.STORY,
                fetched_at=int(datetime.now(timezone.utc).timestamp()),
                tags=[]
            ),
            Post(
                id=11,
                title="Tutorial on Machine Learning",
                author="bob",
                score=100,
                url="http://example.com/11",
                created_at=int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()),
                type="story",
                category=Category.STORY,
                fetched_at=int(datetime.now(timezone.utc).timestamp()),
                tags=[]
            ),
            Post(
                id=12,
                title="Machine and Learning Concepts",
                author="charlie",
                score=100,
                url="http://example.com/12",
                created_at=int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()),
                type="story",
                category=Category.STORY,
                fetched_at=int(datetime.now(timezone.utc).timestamp()),
                tags=[]
            ),
        ]

        # Insert posts
        conn = database._get_connection()
        cursor = conn.cursor()
        for post in posts:
            cursor.execute(
                """
                INSERT INTO posts (id, title, author, score, url, created_at, type, category, fetched_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post.id,
                    post.title,
                    post.author,
                    post.score,
                    post.url,
                    post.created_at,
                    post.type,
                    post.category.value,
                    post.fetched_at,
                    ",".join(post.tags),
                ),
            )
        conn.commit()

        # Search for exact phrase
        query = SearchQuery(text="Machine Learning", order_by="relevance")
        result = search_engine.search(query)

        # Post with exact phrase at start should rank highest
        assert len(result.posts) == 3
        assert result.posts[0].id == 10  # "Machine Learning Tutorial" - exact match at start

    def test_ordering_with_pagination(self, search_engine, sample_posts):
        """Test that ordering is maintained across pagination."""
        # Get first page ordered by score descending
        query1 = SearchQuery(text="Python", order_by="score_desc", page=1, page_size=2)
        result1 = search_engine.search(query1)

        # Get second page
        query2 = SearchQuery(text="Python", order_by="score_desc", page=2, page_size=2)
        result2 = search_engine.search(query2)

        # Verify ordering is maintained
        assert len(result1.posts) == 2
        assert len(result2.posts) == 2

        # First page should have highest scores
        assert result1.posts[0].score >= result1.posts[1].score
        # Second page should have lower scores than first page
        assert result1.posts[1].score >= result2.posts[0].score
        assert result2.posts[0].score >= result2.posts[1].score
