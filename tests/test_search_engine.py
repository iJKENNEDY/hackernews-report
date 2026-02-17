"""Unit tests for SearchEngine with basic text search."""

import os
import tempfile

from src.database import Database
from src.search_engine import SearchEngine
from src.models import Post, Category, SearchQuery


class TestSearchEngineBasicTextSearch:
    """Unit tests for basic text search functionality."""

    def test_text_search_finds_matching_posts(self):
        """Test that text search finds posts with matching titles."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Create test posts
            posts = [
                Post(
                    id=1,
                    title="Python 3.11 released",
                    author="user1",
                    score=100,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=["Python"]
                ),
                Post(
                    id=2,
                    title="Learning Rust programming",
                    author="user2",
                    score=50,
                    url="http://example.com/2",
                    created_at=1234567891,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=["Rust"]
                ),
                Post(
                    id=3,
                    title="Advanced Python techniques",
                    author="user3",
                    score=75,
                    url="http://example.com/3",
                    created_at=1234567892,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=["Python"]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            # Create search engine
            engine = SearchEngine(db)

            # Search for "python"
            query = SearchQuery(text="python")
            result = engine.search(query)

            # Verify results
            assert result.total_results == 2
            assert len(result.posts) == 2
            assert all("python" in post.title.lower() for post in result.posts)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_text_search_case_insensitive(self):
        """Test that text search is case-insensitive."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            post = Post(
                id=1,
                title="Python Programming",
                author="user1",
                score=100,
                url="http://example.com/1",
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
                tags=[]
            )
            db.insert_post(post)

            engine = SearchEngine(db)

            # Search with different cases
            for search_term in ["python", "PYTHON", "Python", "pYtHoN"]:
                query = SearchQuery(text=search_term)
                result = engine.search(query)
                assert result.total_results == 1
                assert len(result.posts) == 1

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_text_search_partial_matching(self):
        """Test that text search supports partial (substring) matching."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            post = Post(
                id=1,
                title="Understanding JavaScript closures",
                author="user1",
                score=100,
                url="http://example.com/1",
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
                tags=[]
            )
            db.insert_post(post)

            engine = SearchEngine(db)

            # Search with partial terms
            for search_term in ["java", "script", "closure", "stand"]:
                query = SearchQuery(text=search_term)
                result = engine.search(query)
                assert result.total_results == 1
                assert len(result.posts) == 1

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_text_search_multi_word_and_operation(self):
        """Test that multi-word search uses AND operation."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Machine learning with Python",
                    author="user1",
                    score=100,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Machine learning basics",
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
                    title="Python programming guide",
                    author="user3",
                    score=75,
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

            # Search for "machine python" - should only find post 1
            query = SearchQuery(text="machine python")
            result = engine.search(query)

            assert result.total_results == 1
            assert len(result.posts) == 1
            assert result.posts[0].id == 1
            assert "machine" in result.posts[0].title.lower()
            assert "python" in result.posts[0].title.lower()

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_text_search_no_results(self):
        """Test that search returns empty result when no matches found."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            post = Post(
                id=1,
                title="Python programming",
                author="user1",
                score=100,
                url="http://example.com/1",
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
                tags=[]
            )
            db.insert_post(post)

            engine = SearchEngine(db)

            # Search for term that doesn't exist
            query = SearchQuery(text="javascript")
            result = engine.search(query)

            assert result.total_results == 0
            assert len(result.posts) == 0
            assert result.total_pages == 0

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_pagination_basic(self):
        """Test basic pagination functionality."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            # Create 25 posts with "test" in title
            for i in range(25):
                post = Post(
                    id=i + 1,
                    title=f"Test post {i + 1}",
                    author=f"user{i}",
                    score=i * 10,
                    url=f"http://example.com/{i}",
                    created_at=1234567890 + i,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900 + i,
                    tags=[]
                )
                db.insert_post(post)

            engine = SearchEngine(db)

            # Get first page (default page_size=20)
            query = SearchQuery(text="test", page=1)
            result = engine.search(query)

            assert result.total_results == 25
            assert result.total_pages == 2
            assert len(result.posts) == 20
            assert result.page == 1

            # Get second page
            query = SearchQuery(text="test", page=2)
            result = engine.search(query)

            assert result.total_results == 25
            assert result.total_pages == 2
            assert len(result.posts) == 5
            assert result.page == 2

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_empty_text_search_rejected(self):
        """Test that empty or whitespace-only text search is rejected."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()
            engine = SearchEngine(db)

            # Try empty string
            try:
                query = SearchQuery(text="")
                engine.search(query)
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "empty or whitespace only" in str(e).lower()

            # Try whitespace only
            try:
                query = SearchQuery(text="   ")
                engine.search(query)
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "empty or whitespace only" in str(e).lower()

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestSearchEngineAuthorSearch:
    """Unit tests for author search functionality."""

    def test_author_search_exact_match(self):
        """Test that author search finds posts by exact author name."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="First post",
                    author="johndoe",
                    score=100,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Second post",
                    author="janedoe",
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
                    title="Third post",
                    author="johndoe",
                    score=75,
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

            # Search for "johndoe"
            query = SearchQuery(author="johndoe")
            result = engine.search(query)

            assert result.total_results == 2
            assert len(result.posts) == 2
            assert all(post.author == "johndoe" for post in result.posts)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_author_search_case_insensitive(self):
        """Test that author search is case-insensitive."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            post = Post(
                id=1,
                title="Test post",
                author="JohnDoe",
                score=100,
                url="http://example.com/1",
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
                tags=[]
            )
            db.insert_post(post)

            engine = SearchEngine(db)

            # Search with different cases
            for search_author in ["johndoe", "JOHNDOE", "JohnDoe", "jOhNdOe"]:
                query = SearchQuery(author=search_author)
                result = engine.search(query)
                assert result.total_results == 1
                assert len(result.posts) == 1
                assert result.posts[0].author == "JohnDoe"

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_author_search_partial_matching(self):
        """Test that author search supports partial (substring) matching."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            post = Post(
                id=1,
                title="Test post",
                author="johnsmith",
                score=100,
                url="http://example.com/1",
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
                tags=[]
            )
            db.insert_post(post)

            engine = SearchEngine(db)

            # Search with partial author names
            for search_author in ["john", "smith", "ohns", "nsmith"]:
                query = SearchQuery(author=search_author)
                result = engine.search(query)
                assert result.total_results == 1
                assert len(result.posts) == 1
                assert result.posts[0].author == "johnsmith"

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_author_search_no_results(self):
        """Test that author search returns empty result when author not found."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            post = Post(
                id=1,
                title="Test post",
                author="johndoe",
                score=100,
                url="http://example.com/1",
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
                tags=[]
            )
            db.insert_post(post)

            engine = SearchEngine(db)

            # Search for non-existent author
            query = SearchQuery(author="janedoe")
            result = engine.search(query)

            assert result.total_results == 0
            assert len(result.posts) == 0
            assert result.total_pages == 0

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_combined_text_and_author_search(self):
        """Test combining text and author search criteria (AND operation)."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Python programming guide",
                    author="johndoe",
                    score=100,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=[]
                ),
                Post(
                    id=2,
                    title="Python tutorial",
                    author="janedoe",
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
                    title="JavaScript basics",
                    author="johndoe",
                    score=75,
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

            # Search for "python" by "johndoe" - should only find post 1
            query = SearchQuery(text="python", author="johndoe")
            result = engine.search(query)

            assert result.total_results == 1
            assert len(result.posts) == 1
            assert result.posts[0].id == 1
            assert "python" in result.posts[0].title.lower()
            assert result.posts[0].author == "johndoe"

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)



class TestSearchEngineTagSearch:
    """Unit tests for tag search functionality."""

    def test_tag_search_single_tag(self):
        """Test that tag search finds posts with matching tag."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Python programming guide",
                    author="user1",
                    score=100,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=["Python", "Programming"]
                ),
                Post(
                    id=2,
                    title="Rust tutorial",
                    author="user2",
                    score=50,
                    url="http://example.com/2",
                    created_at=1234567891,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=["Rust"]
                ),
                Post(
                    id=3,
                    title="Advanced Python techniques",
                    author="user3",
                    score=75,
                    url="http://example.com/3",
                    created_at=1234567892,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=["Python", "Advanced"]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search for "Python" tag
            query = SearchQuery(tags=["Python"])
            result = engine.search(query)

            assert result.total_results == 2
            assert len(result.posts) == 2
            assert all("Python" in post.tags for post in result.posts)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_tag_search_multiple_tags_or_operation(self):
        """Test that multiple tags use OR operation."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Python programming",
                    author="user1",
                    score=100,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=["Python"]
                ),
                Post(
                    id=2,
                    title="Rust tutorial",
                    author="user2",
                    score=50,
                    url="http://example.com/2",
                    created_at=1234567891,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=["Rust"]
                ),
                Post(
                    id=3,
                    title="JavaScript basics",
                    author="user3",
                    score=75,
                    url="http://example.com/3",
                    created_at=1234567892,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=["JavaScript"]
                ),
                Post(
                    id=4,
                    title="Java programming",
                    author="user4",
                    score=60,
                    url="http://example.com/4",
                    created_at=1234567893,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567903,
                    tags=["Java"]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search for "Python" OR "Rust" tags
            query = SearchQuery(tags=["Python", "Rust"])
            result = engine.search(query)

            assert result.total_results == 2
            assert len(result.posts) == 2
            # Should find posts with either Python or Rust tags
            found_tags = set()
            for post in result.posts:
                found_tags.update(post.tags)
            assert "Python" in found_tags or "Rust" in found_tags

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_tag_search_no_results(self):
        """Test that tag search returns empty result when tag not found."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            post = Post(
                id=1,
                title="Python programming",
                author="user1",
                score=100,
                url="http://example.com/1",
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900,
                tags=["Python"]
            )
            db.insert_post(post)

            engine = SearchEngine(db)

            # Search for non-existent tag
            query = SearchQuery(tags=["Rust"])
            result = engine.search(query)

            assert result.total_results == 0
            assert len(result.posts) == 0
            assert result.total_pages == 0

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_combined_text_and_tags_search(self):
        """Test combining text and tags search criteria (AND operation)."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Python machine learning guide",
                    author="user1",
                    score=100,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=["Python", "AI"]
                ),
                Post(
                    id=2,
                    title="Python web development",
                    author="user2",
                    score=50,
                    url="http://example.com/2",
                    created_at=1234567891,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=["Python", "Web Dev"]
                ),
                Post(
                    id=3,
                    title="Rust machine learning",
                    author="user3",
                    score=75,
                    url="http://example.com/3",
                    created_at=1234567892,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=["Rust", "AI"]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search for "machine" text with "Python" tag - should only find post 1
            query = SearchQuery(text="machine", tags=["Python"])
            result = engine.search(query)

            assert result.total_results == 1
            assert len(result.posts) == 1
            assert result.posts[0].id == 1
            assert "machine" in result.posts[0].title.lower()
            assert "Python" in result.posts[0].tags

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_combined_author_and_tags_search(self):
        """Test combining author and tags search criteria (AND operation)."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            posts = [
                Post(
                    id=1,
                    title="Python guide",
                    author="johndoe",
                    score=100,
                    url="http://example.com/1",
                    created_at=1234567890,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567900,
                    tags=["Python"]
                ),
                Post(
                    id=2,
                    title="Rust tutorial",
                    author="johndoe",
                    score=50,
                    url="http://example.com/2",
                    created_at=1234567891,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567901,
                    tags=["Rust"]
                ),
                Post(
                    id=3,
                    title="Python basics",
                    author="janedoe",
                    score=75,
                    url="http://example.com/3",
                    created_at=1234567892,
                    type="story",
                    category=Category.STORY,
                    fetched_at=1234567902,
                    tags=["Python"]
                ),
            ]

            for post in posts:
                db.insert_post(post)

            engine = SearchEngine(db)

            # Search for "Python" tag by "johndoe" - should only find post 1
            query = SearchQuery(author="johndoe", tags=["Python"])
            result = engine.search(query)

            assert result.total_results == 1
            assert len(result.posts) == 1
            assert result.posts[0].id == 1
            assert result.posts[0].author == "johndoe"
            assert "Python" in result.posts[0].tags

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestSearchEngineIndices:
    """Unit tests for search index creation."""

    def test_create_search_indices(self):
        """Test that all search indices are created correctly."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()
            engine = SearchEngine(db)

            # Create search indices
            engine.create_search_indices()

            # Verify indices exist by querying sqlite_master
            conn = db._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_posts_%'
                ORDER BY name
            """)
            
            indices = [row[0] for row in cursor.fetchall()]
            
            # Verify all expected indices exist
            expected_indices = [
                'idx_posts_author_lower',
                'idx_posts_category',
                'idx_posts_created_at',
                'idx_posts_score',
                'idx_posts_score_created',
                'idx_posts_tags',
                'idx_posts_title_lower',
                'idx_posts_type',
            ]
            
            for expected_index in expected_indices:
                assert expected_index in indices, f"Index {expected_index} not found"

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_indices_created_during_schema_initialization(self):
        """Test that search indices are created during schema initialization."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()

            # Verify search indices exist after schema initialization
            conn = db._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name IN (
                    'idx_posts_title_lower',
                    'idx_posts_author_lower',
                    'idx_posts_tags',
                    'idx_posts_score',
                    'idx_posts_score_created'
                )
                ORDER BY name
            """)
            
            indices = [row[0] for row in cursor.fetchall()]
            
            # Verify all search indices exist
            expected_search_indices = [
                'idx_posts_author_lower',
                'idx_posts_score',
                'idx_posts_score_created',
                'idx_posts_tags',
                'idx_posts_title_lower',
            ]
            
            for expected_index in expected_search_indices:
                assert expected_index in indices, f"Search index {expected_index} not created during schema initialization"

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_create_search_indices_idempotent(self):
        """Test that create_search_indices can be called multiple times safely."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            db = Database(db_path)
            db.initialize_schema()
            engine = SearchEngine(db)

            # Call create_search_indices multiple times
            engine.create_search_indices()
            engine.create_search_indices()
            engine.create_search_indices()

            # Verify indices still exist and no errors occurred
            conn = db._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='index' AND name IN (
                    'idx_posts_title_lower',
                    'idx_posts_author_lower',
                    'idx_posts_tags',
                    'idx_posts_score',
                    'idx_posts_score_created'
                )
            """)
            
            count = cursor.fetchone()[0]
            assert count == 5, "All 5 search indices should exist"

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
