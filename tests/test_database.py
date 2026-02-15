"""Unit and property-based tests for database layer."""

import os
import tempfile
from hypothesis import given, strategies as st, settings

from src.database import Database
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


class TestDatabasePropertyBased:
    """Property-based tests for database operations."""

    @given(post=valid_post_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_storage_roundtrip(self, post: Post):
        """
        Property 3: Round-trip de almacenamiento
        Validates: Requirements 2.2, 2.5

        For any valid post, storing it in the database and then
        retrieving it must produce an equivalent object with all
        fields preserved.
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Store the post
            success = db.upsert_post(post)
            assert success, "Failed to store post"

            # Retrieve the post
            retrieved = db.get_post_by_id(post.id)

            # Verify all fields are preserved
            assert retrieved is not None, "Post not found after storage"
            assert retrieved.id == post.id
            assert retrieved.title == post.title
            assert retrieved.author == post.author
            assert retrieved.score == post.score
            assert retrieved.url == post.url
            assert retrieved.created_at == post.created_at
            assert retrieved.type == post.type
            assert retrieved.category == post.category
            assert retrieved.fetched_at == post.fetched_at

            db.close()
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)


    @given(post=valid_post_strategy(), repeat_count=st.integers(min_value=2, max_value=5))
    @settings(max_examples=100, deadline=None)
    def test_property_upsert_idempotence(self, post: Post, repeat_count: int):
        """
        Property 4: Idempotencia de upsert
        Validates: Requirements 2.3

        For any post, inserting it multiple times with the same id
        must result in exactly one entry in the database with the
        most recent data.
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Insert the same post multiple times
            for _ in range(repeat_count):
                success = db.upsert_post(post)
                assert success, "Upsert operation failed"

            # Verify only one entry exists
            retrieved = db.get_post_by_id(post.id)
            assert retrieved is not None, "Post not found after multiple upserts"

            # Verify the data matches the original post
            assert retrieved.id == post.id
            assert retrieved.title == post.title
            assert retrieved.author == post.author
            assert retrieved.score == post.score

            # Count posts with this ID (should be exactly 1)
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts WHERE id = ?", (post.id,))
            count = cursor.fetchone()[0]
            assert count == 1, f"Expected 1 post, found {count}"

            db.close()
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)


    @given(posts=st.lists(valid_post_strategy(), min_size=5, max_size=20))
    @settings(max_examples=100, deadline=None)
    def test_property_category_filtering(self, posts):
        """
        Property 8: Filtrado por categoría
        Validates: Requirements 3.3, 4.3

        For any query filtered by category, all posts returned
        must belong exclusively to that category.
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Store all posts
            for post in posts:
                db.upsert_post(post)

            # Test filtering for each category
            for category in Category:
                filtered_posts = db.get_posts_by_category(category)

                # Verify all returned posts belong to the requested category
                for post in filtered_posts:
                    assert post.category == category, \
                        f"Post {post.id} has category {post.category}, expected {category}"

                # Verify we got all posts of this category
                expected_count = sum(1 for p in posts if p.category == category)
                # Note: We may have fewer due to duplicate IDs being upserted
                assert len(filtered_posts) <= expected_count

            db.close()
        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)



class TestDatabaseEdgeCases:
    """Unit tests for database edge cases."""

    def test_database_creation_when_not_exists(self):
        """Test that database is created when it doesn't exist."""
        # Create a path in a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "subdir", "test.db")

            # Database file should not exist yet
            assert not os.path.exists(db_path)

            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Database file should now exist
            assert os.path.exists(db_path)

            # Verify we can perform operations
            post = Post(
                id=1,
                title="Test",
                author="user",
                score=10,
                url=None,
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
            )

            success = db.insert_post(post)
            assert success

            retrieved = db.get_post_by_id(1)
            assert retrieved is not None
            assert retrieved.id == 1

            db.close()

    def test_validation_before_insertion(self):
        """Test that invalid posts are handled appropriately."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            # Create a post with invalid data (empty title)
            invalid_post = Post(
                id=1,
                title="",
                author="user",
                score=10,
                url=None,
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
            )

            # The database layer doesn't validate - it stores what it's given
            # Validation should happen at a higher layer
            # But we can still insert it
            success = db.insert_post(invalid_post)
            assert success

            # Verify it was stored
            retrieved = db.get_post_by_id(1)
            assert retrieved is not None
            assert retrieved.title == ""

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_get_nonexistent_post(self):
        """Test retrieving a post that doesn't exist."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            # Try to get a post that doesn't exist
            result = db.get_post_by_id(99999)
            assert result is None

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_post_exists_check(self):
        """Test the post_exists method."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            # Check non-existent post
            assert not db.post_exists(1)

            # Insert a post
            post = Post(
                id=1,
                title="Test",
                author="user",
                score=10,
                url=None,
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
            )
            db.insert_post(post)

            # Check existing post
            assert db.post_exists(1)

            # Check another non-existent post
            assert not db.post_exists(2)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_update_nonexistent_post(self):
        """Test updating a post that doesn't exist."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            # Try to update a post that doesn't exist
            post = Post(
                id=999,
                title="Test",
                author="user",
                score=10,
                url=None,
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
            )

            result = db.update_post(post)
            assert result is False

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_get_category_counts_empty_database(self):
        """Test getting category counts from an empty database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            counts = db.get_category_counts()
            assert counts == {}

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_get_posts_by_category_empty_database(self):
        """Test getting posts by category from an empty database."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = db.get_posts_by_category(Category.STORY)
            assert posts == []

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_transaction_context_manager(self):
        """Test the transaction context manager."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            # Use transaction context manager
            with db.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO posts (id, title, author, score, url, created_at, type, category, fetched_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (1, "Test", "user", 10, None, 1234567890, "story", "story", 1234567900))

            # Verify the post was committed
            post = db.get_post_by_id(1)
            assert post is not None
            assert post.title == "Test"

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_transaction_rollback_on_error(self):
        """Test that transactions rollback on error."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            # Insert a post first
            post1 = Post(
                id=1,
                title="First",
                author="user",
                score=10,
                url=None,
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
            )
            db.insert_post(post1)

            # Try to use transaction with an error
            try:
                with db.transaction() as conn:
                    cursor = conn.cursor()
                    # This should succeed
                    cursor.execute("""
                        INSERT INTO posts (id, title, author, score, url, created_at, type, category, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (2, "Second", "user", 20, None, 1234567890, "job", "job", 1234567900))

                    # This should fail (duplicate ID)
                    cursor.execute("""
                        INSERT INTO posts (id, title, author, score, url, created_at, type, category, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (1, "Duplicate", "user", 30, None, 1234567890, "ask", "ask", 1234567900))
            except Exception:
                pass  # Expected to fail

            # Verify post 2 was NOT committed (rollback occurred)
            post2 = db.get_post_by_id(2)
            assert post2 is None

            # Verify post 1 still exists
            post1_check = db.get_post_by_id(1)
            assert post1_check is not None
            assert post1_check.title == "First"

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
