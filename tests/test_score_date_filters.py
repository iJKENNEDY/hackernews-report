"""Unit tests for score and date filters in SearchEngine."""

import os
import tempfile
from datetime import date, datetime, timezone, time

from src.database import Database
from src.search_engine import SearchEngine
from src.models import Post, Category, SearchQuery


class TestScoreFilters:
    """Unit tests for score filtering functionality."""

    def test_min_score_filter(self):
        """Test that min_score filter returns only posts with score >= min_score."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Low score post",
                    author="user1",
                    score=10,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Medium score post",
                    author="user2",
                    score=50,
                    url="http://example.com/2",
                    created_at=1234567891,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=[]
                ),
                Post(
                    id=3,
                    title="High score post",
                    author="user3",
                    score=100,
                    url="http://example.com/3",
                    created_at=1234567892,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=[]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search with min_score=50
            query = SearchQuery(min_score=50)
            result = engine.search(query)

            assert result.total_results == 2
            assert len(result.posts) == 2
            assert all(post.score >= 50 for post in result.posts)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_max_score_filter(self):
        """Test that max_score filter returns only posts with score <= max_score."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Low score post",
                    author="user1",
                    score=10,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Medium score post",
                    author="user2",
                    score=50,
                    url="http://example.com/2",
                    created_at=1234567891,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=[]
                ),
                Post(
                    id=3,
                    title="High score post",
                    author="user3",
                    score=100,
                    url="http://example.com/3",
                    created_at=1234567892,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=[]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search with max_score=50
            query = SearchQuery(max_score=50)
            result = engine.search(query)

            assert result.total_results == 2
            assert len(result.posts) == 2
            assert all(post.score <= 50 for post in result.posts)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_score_range_filter(self):
        """Test that score range filter returns posts within the range."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Very low score",
                    author="user1",
                    score=5,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Low score",
                    author="user2",
                    score=25,
                    url="http://example.com/2",
                    created_at=1234567891,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=[]
                ),
                Post(
                    id=3,
                    title="Medium score",
                    author="user3",
                    score=50,
                    url="http://example.com/3",
                    created_at=1234567892,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=[]
                ),
                Post(
                    id=4,
                    title="High score",
                    author="user4",
                    score=75,
                    url="http://example.com/4",
                    created_at=1234567893,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567903,
                    tags=[]
                ),
                Post(
                    id=5,
                    title="Very high score",
                    author="user5",
                    score=150,
                    url="http://example.com/5",
                    created_at=1234567894,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567904,
                    tags=[]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search with score range 25-75
            query = SearchQuery(min_score=25, max_score=75)
            result = engine.search(query)

            assert result.total_results == 3
            assert len(result.posts) == 3
            assert all(25 <= post.score <= 75 for post in result.posts)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestDateFilters:
    """Unit tests for date filtering functionality."""

    def test_start_date_filter(self):
        """Test that start_date filter returns only posts created on or after start_date."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            # Create posts with different dates
            # 2024-01-01 00:00:00 UTC = 1704067200
            # 2024-06-01 00:00:00 UTC = 1717200000
            # 2024-12-01 00:00:00 UTC = 1733011200
            posts = [
                Post(
                    id=1,
                    title="Old post",
                    author="user1",
                    score=10,
                    url="http://example.com/1",
                    created_at=1704067200,  # 2024-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Mid post",
                    author="user2",
                    score=50,
                    url="http://example.com/2",
                    created_at=1717200000,  # 2024-06-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=[]
                ),
                Post(
                    id=3,
                    title="Recent post",
                    author="user3",
                    score=100,
                    url="http://example.com/3",
                    created_at=1733011200,  # 2024-12-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=[]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search with start_date=2024-06-01
            query = SearchQuery(start_date=date(2024, 6, 1))
            result = engine.search(query)

            assert result.total_results == 2
            assert len(result.posts) == 2
            # Verify all posts are from June 1st or later
            june_1_timestamp = 1717200000
            assert all(post.created_at >= june_1_timestamp for post in result.posts)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_end_date_filter(self):
        """Test that end_date filter returns only posts created on or before end_date."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Old post",
                    author="user1",
                    score=10,
                    url="http://example.com/1",
                    created_at=1704067200,  # 2024-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Mid post",
                    author="user2",
                    score=50,
                    url="http://example.com/2",
                    created_at=1717200000,  # 2024-06-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=[]
                ),
                Post(
                    id=3,
                    title="Recent post",
                    author="user3",
                    score=100,
                    url="http://example.com/3",
                    created_at=1733011200,  # 2024-12-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=[]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search with end_date=2024-06-01
            query = SearchQuery(end_date=date(2024, 6, 1))
            result = engine.search(query)

            assert result.total_results == 2
            assert len(result.posts) == 2
            # Verify all posts are from June 1st or earlier (end of day)
            june_1_end_timestamp = int(datetime.combine(date(2024, 6, 1), time.max, tzinfo=timezone.utc).timestamp())
            assert all(post.created_at <= june_1_end_timestamp for post in result.posts)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_date_range_filter(self):
        """Test that date range filter returns posts within the date range."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Very old post",
                    author="user1",
                    score=10,
                    url="http://example.com/1",
                    created_at=1672531200,  # 2023-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Start of range",
                    author="user2",
                    score=50,
                    url="http://example.com/2",
                    created_at=1704067200,  # 2024-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=[]
                ),
                Post(
                    id=3,
                    title="Middle of range",
                    author="user3",
                    score=75,
                    url="http://example.com/3",
                    created_at=1717200000,  # 2024-06-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=[]
                ),
                Post(
                    id=4,
                    title="End of range",
                    author="user4",
                    score=100,
                    url="http://example.com/4",
                    created_at=1733011200,  # 2024-12-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567903,
                    tags=[]
                ),
                Post(
                    id=5,
                    title="Future post",
                    author="user5",
                    score=150,
                    url="http://example.com/5",
                    created_at=1767225600,  # 2026-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567904,
                    tags=[]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search with date range 2024-01-01 to 2024-12-31
            query = SearchQuery(start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))
            result = engine.search(query)

            assert result.total_results == 3
            assert len(result.posts) == 3
            # Verify all posts are within 2024
            start_timestamp = int(datetime.combine(date(2024, 1, 1), time.min, tzinfo=timezone.utc).timestamp())
            end_timestamp = int(datetime.combine(date(2024, 12, 31), time.max, tzinfo=timezone.utc).timestamp())
            assert all(start_timestamp <= post.created_at <= end_timestamp for post in result.posts)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestCombinedFilters:
    """Unit tests for combining score and date filters with other criteria."""

    def test_combined_text_score_filters(self):
        """Test combining text search with score filters."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Python tutorial low score",
                    author="user1",
                    score=10,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Python guide high score",
                    author="user2",
                    score=100,
                    url="http://example.com/2",
                    created_at=1234567891,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=[]
                ),
                Post(
                    id=3,
                    title="Rust tutorial high score",
                    author="user3",
                    score=150,
                    url="http://example.com/3",
                    created_at=1234567892,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=[]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search for "python" with min_score=50
            query = SearchQuery(text="python", min_score=50)
            result = engine.search(query)

            assert result.total_results == 1
            assert len(result.posts) == 1
            assert result.posts[0].id == 2
            assert "python" in result.posts[0].title.lower()
            assert result.posts[0].score >= 50

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_combined_author_date_filters(self):
        """Test combining author search with date filters."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Old post by johndoe",
                    author="johndoe",
                    score=10,
                    url="http://example.com/1",
                    created_at=1672531200,  # 2023-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Recent post by johndoe",
                    author="johndoe",
                    score=50,
                    url="http://example.com/2",
                    created_at=1704067200,  # 2024-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=[]
                ),
                Post(
                    id=3,
                    title="Recent post by janedoe",
                    author="janedoe",
                    score=75,
                    url="http://example.com/3",
                    created_at=1704067200,  # 2024-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=[]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search for "johndoe" with start_date=2024-01-01
            query = SearchQuery(author="johndoe", start_date=date(2024, 1, 1))
            result = engine.search(query)

            assert result.total_results == 1
            assert len(result.posts) == 1
            assert result.posts[0].id == 2
            assert result.posts[0].author == "johndoe"
            assert result.posts[0].created_at >= 1704067200

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


    def test_all_criteria_combined(self):
        """Test combining all search criteria simultaneously (text, author, tags, score, date)."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Python machine learning guide",
                    author="johndoe",
                    score=100,
                    url="http://example.com/1",
                    created_at=1704067200,  # 2024-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=["Python", "AI"]
                ),
                Post(
                    id=2,
                    title="Python web development",
                    author="johndoe",
                    score=50,
                    url="http://example.com/2",
                    created_at=1704067200,  # 2024-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=["Python", "Web Dev"]
                ),
                Post(
                    id=3,
                    title="Python machine learning basics",
                    author="janedoe",
                    score=120,
                    url="http://example.com/3",
                    created_at=1704067200,  # 2024-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=["Python", "AI"]
                ),
                Post(
                    id=4,
                    title="Python machine learning advanced",
                    author="johndoe",
                    score=150,
                    url="http://example.com/4",
                    created_at=1672531200,  # 2023-01-01 (too old)
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567903,
                    tags=["Python", "AI"]
                ),
                Post(
                    id=5,
                    title="Rust machine learning",
                    author="johndoe",
                    score=110,
                    url="http://example.com/5",
                    created_at=1704067200,  # 2024-01-01
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567904,
                    tags=["Rust", "AI"]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search with ALL criteria:
            # - text: "python machine learning"
            # - author: "johndoe"
            # - tags: ["AI"]
            # - min_score: 80
            # - start_date: 2024-01-01
            # Should only find post 1 (id=1)
            query = SearchQuery(
                text="python machine learning",
                author="johndoe",
                tags=["AI"],
                min_score=80,
                start_date=date(2024, 1, 1)
            )
            result = engine.search(query)

            assert result.total_results == 1
            assert len(result.posts) == 1
            assert result.posts[0].id == 1
            # Verify all criteria are met
            assert "python" in result.posts[0].title.lower()
            assert "machine" in result.posts[0].title.lower()
            assert "learning" in result.posts[0].title.lower()
            assert result.posts[0].author == "johndoe"
            assert "AI" in result.posts[0].tags
            assert result.posts[0].score >= 80
            assert result.posts[0].created_at >= 1704067200

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_multiple_criteria_no_results(self):
        """Test that combining criteria with no matching posts returns empty result."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Python programming",
                    author="johndoe",
                    score=50,
                    url="http://example.com/1",
                    created_at=1704067200,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=["Python"]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search with criteria that won't match any post
            query = SearchQuery(
                text="python",
                author="johndoe",
                min_score=100  # Post only has score=50
            )
            result = engine.search(query)

            assert result.total_results == 0
            assert len(result.posts) == 0
            assert result.total_pages == 0

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
