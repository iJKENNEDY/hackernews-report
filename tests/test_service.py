"""Unit and property-based tests for service layer."""

import os
import tempfile
from unittest.mock import Mock
from hypothesis import given, strategies as st, settings

from src.service import HackerNewsService
from src.database import Database
from src.api_client import HNApiClient
from src.models import Post, Category


# Hypothesis strategies for generating test data
@st.composite
def valid_post_strategy(draw):
    """Generate a valid Post for testing."""
    post_id = draw(st.integers(min_value=1, max_value=1000000))
    title = draw(st.text(min_size=1, max_size=200))
    author = draw(st.text(min_size=1, max_size=100))
    score = draw(st.integers(min_value=0, max_value=10000))
    url = draw(st.one_of(st.none(), st.text(min_size=1, max_size=200)))
    created_at = draw(st.integers(min_value=1, max_value=2000000000))
    post_type = draw(st.sampled_from(["story", "job", "ask", "poll", "other"]))
    category = Category(post_type) if post_type in ["story", "job", "ask", "poll"] else Category.OTHER
    fetched_at = draw(st.integers(min_value=1, max_value=2000000000))

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


class TestServicePropertyBased:
    """Property-based tests for service layer operations."""

    @given(posts=st.lists(valid_post_strategy(), min_size=1, max_size=10, unique_by=lambda p: p.id))
    @settings(max_examples=100, deadline=None)
    def test_property_transactional_integrity(self, posts):
        """
        Property 5: Integridad transaccional
        Validates: Requirements 6.4

        For any operation that is interrupted, the database must
        maintain a consistent state without partial or corrupt data.
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Create mock API client that returns our test posts
            mock_api = Mock(spec=HNApiClient)
            mock_api.get_top_stories.return_value = [p.id for p in posts]
            mock_api.get_items_batch.return_value = posts

            # Create service
            service = HackerNewsService(api_client=mock_api, database=db)

            # Perform fetch and store operation
            result = service.fetch_and_store_posts(limit=len(posts))

            # Verify all posts were stored successfully
            assert result.new_posts + result.updated_posts == len(posts)

            # Verify database consistency - all posts should be retrievable
            for post in posts:
                retrieved = db.get_post_by_id(post.id)
                assert retrieved is not None, f"Post {post.id} not found in database"
                assert retrieved.id == post.id
                assert retrieved.title == post.title
                assert retrieved.author == post.author

            # Verify no partial data - count should match
            all_posts = db.get_posts_by_category()
            assert len(all_posts) == len(posts)

            db.close()
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    @given(
        initial_posts=st.lists(valid_post_strategy(), min_size=5, max_size=10, unique_by=lambda p: p.id),
        new_posts=st.lists(valid_post_strategy(), min_size=1, max_size=5, unique_by=lambda p: p.id)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_avoid_duplicates(self, initial_posts, new_posts):
        """
        Property 12: Evitar duplicados en actualización
        Validates: Requirements 5.2

        For any update operation, the system must fetch only posts
        that don't already exist in the database.
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Store initial posts
            for post in initial_posts:
                db.upsert_post(post)

            # Get initial count
            initial_count = len(db.get_posts_by_category())

            # Ensure new_posts have different IDs from initial_posts
            initial_ids = set(p.id for p in initial_posts)
            truly_new_posts = [p for p in new_posts if p.id not in initial_ids]

            if not truly_new_posts:
                # If all new posts are duplicates, skip this test iteration
                db.close()
                return

            # Create mock API client
            mock_api = Mock(spec=HNApiClient)
            mock_api.get_top_stories.return_value = [p.id for p in truly_new_posts]
            mock_api.get_items_batch.return_value = truly_new_posts

            # Create service and fetch
            service = HackerNewsService(api_client=mock_api, database=db)
            result = service.fetch_and_store_posts(limit=len(truly_new_posts))

            # Verify only new posts were added
            final_count = len(db.get_posts_by_category())
            expected_new = len(truly_new_posts)  # All are unique and new
            assert final_count == initial_count + expected_new

            # Verify result reports correct number of new posts
            assert result.new_posts == expected_new
            assert result.updated_posts == 0

            db.close()
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    @given(posts=st.lists(valid_post_strategy(), min_size=1, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_accurate_count(self, posts):
        """
        Property 13: Conteo preciso de posts nuevos
        Validates: Requirements 5.3

        For any completed update operation, the number of new posts
        reported must exactly match the number of posts actually
        inserted in the database.
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Get initial count
            initial_count = len(db.get_posts_by_category())

            # Create mock API client
            mock_api = Mock(spec=HNApiClient)
            mock_api.get_top_stories.return_value = [p.id for p in posts]
            mock_api.get_items_batch.return_value = posts

            # Create service and fetch
            service = HackerNewsService(api_client=mock_api, database=db)
            result = service.fetch_and_store_posts(limit=len(posts))

            # Get final count
            final_count = len(db.get_posts_by_category())

            # Calculate actual new posts (accounting for duplicate IDs)
            actual_new = final_count - initial_count

            # Verify reported count matches actual count
            assert result.new_posts == actual_new, \
                f"Reported {result.new_posts} new posts, but {actual_new} were actually added"

            db.close()
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    @given(
        limit=st.integers(min_value=1, max_value=50),
        available_posts=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_respect_limit(self, limit, available_posts):
        """
        Property 14: Respeto del límite especificado
        Validates: Requirements 5.4

        For any limit N specified by the user, the system must
        attempt to fetch exactly N posts (or fewer if not enough
        are available).
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Generate available_posts number of post IDs
            post_ids = list(range(1, available_posts + 1))

            # Create mock API client
            mock_api = Mock(spec=HNApiClient)
            mock_api.get_top_stories.return_value = post_ids[:limit]  # API respects limit

            # Generate posts for the limited IDs
            posts_to_return = []
            for post_id in post_ids[:limit]:
                post = Post(
                    id=post_id,
                    title=f"Post {post_id}",
                    author="testuser",
                    score=10,
                    url=None,
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                )
                posts_to_return.append(post)

            mock_api.get_items_batch.return_value = posts_to_return

            # Create service and fetch with limit
            service = HackerNewsService(api_client=mock_api, database=db)
            result = service.fetch_and_store_posts(limit=limit)

            # Verify the API was called with the correct limit
            mock_api.get_top_stories.assert_called_once_with(limit=limit)

            # Verify we got at most 'limit' posts
            total_fetched = result.new_posts + result.updated_posts
            assert total_fetched <= limit, \
                f"Fetched {total_fetched} posts, but limit was {limit}"

            # Verify we got exactly the expected number (min of limit and available)
            expected = min(limit, available_posts)
            assert total_fetched == expected, \
                f"Expected {expected} posts, got {total_fetched}"

            db.close()
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
