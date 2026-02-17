"""Unit tests for SearchService."""

import os
import tempfile

from src.database import Database
from src.search_engine import SearchEngine
from src.search_service import SearchService
from src.tags import TagSystem
from src.models import SearchQuery, Post, Category


class TestSearchService:
    """Unit tests for SearchService functionality."""

    def setup_method(self):
        """Set up test database and service before each test."""
        # Create temporary database
        self.tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.db_path = self.tmp_file.name
        self.tmp_file.close()

        # Initialize database
        self.db = Database(self.db_path)
        self.db.initialize_schema()

        # Create search engine and service
        self.search_engine = SearchEngine(self.db)
        self.tag_system = TagSystem()
        self.service = SearchService(self.search_engine, self.tag_system)

        # Add some test posts
        self._add_test_posts()

    def teardown_method(self):
        """Clean up after each test."""
        self.db.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def _add_test_posts(self):
        """Add test posts to the database."""
        posts = [
            Post(
                id=1,
                title="Python 3.11 Released",
                author="guido",
                score=500,
                url="https://python.org",
                created_at=1640000000,
                type="story",
                category=Category.STORY,
                fetched_at=1640000100,
                tags=["Python"]
            ),
            Post(
                id=2,
                title="Introduction to Rust",
                author="rustacean",
                score=300,
                url="https://rust-lang.org",
                created_at=1640001000,
                type="story",
                category=Category.STORY,
                fetched_at=1640001100,
                tags=["Rust"]
            ),
            Post(
                id=3,
                title="AI Breakthrough in Machine Learning",
                author="researcher",
                score=800,
                url="https://ai.org",
                created_at=1640002000,
                type="story",
                category=Category.STORY,
                fetched_at=1640002100,
                tags=["AI"]
            ),
        ]

        for post in posts:
            self.db.insert_post(post)

    def test_search_posts_valid_query(self):
        """Test search_posts with a valid query."""
        query = SearchQuery(text="python")
        result = self.service.search_posts(query)

        assert result.total_results == 1
        assert len(result.posts) == 1
        assert result.posts[0].title == "Python 3.11 Released"

    def test_search_posts_invalid_query(self):
        """Test search_posts with an invalid query raises ValueError."""
        # Query with no criteria
        query = SearchQuery()

        try:
            self.service.search_posts(query)
            assert False, "Expected ValueError for invalid query"
        except ValueError as e:
            assert "Invalid search query" in str(e)

    def test_validate_query_valid(self):
        """Test validate_query with a valid query."""
        query = SearchQuery(text="python")
        is_valid, errors = self.service.validate_query(query)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_query_invalid_tag(self):
        """Test validate_query with an invalid tag."""
        query = SearchQuery(tags=["InvalidTag"])
        is_valid, errors = self.service.validate_query(query)

        assert is_valid is False
        assert len(errors) > 0
        assert any("Invalid tag" in error for error in errors)

    def test_validate_query_with_suggestions(self):
        """Test validate_query provides suggestions for similar tags."""
        query = SearchQuery(tags=["Pythn"])  # Typo in "Python"
        is_valid, errors = self.service.validate_query(query)

        assert is_valid is False
        assert len(errors) > 0
        # Should suggest "Python" as a close match
        assert any("Python" in error for error in errors)

    def test_get_available_tags(self):
        """Test get_available_tags returns all tags."""
        tags = self.service.get_available_tags()

        assert isinstance(tags, list)
        assert len(tags) > 0
        assert "Python" in tags
        assert "AI" in tags
        assert "Rust" in tags

    def test_suggest_tags_with_typo(self):
        """Test suggest_tags finds similar tags."""
        suggestions = self.service.suggest_tags("Pythn")

        assert isinstance(suggestions, list)
        assert "Python" in suggestions

    def test_suggest_tags_with_partial(self):
        """Test suggest_tags with partial tag name."""
        suggestions = self.service.suggest_tags("Py")

        assert isinstance(suggestions, list)
        # Should suggest Python-related tags

    def test_suggest_tags_no_match(self):
        """Test suggest_tags with no close matches."""
        suggestions = self.service.suggest_tags("XYZ123")

        assert isinstance(suggestions, list)
        # May be empty or have very distant matches

    def test_highlight_terms_single_word(self):
        """Test highlight_terms with a single search term."""
        text = "Python 3.11 released"
        terms = ["python"]
        result = self.service.highlight_terms(text, terms)

        assert "**Python**" in result
        assert "3.11" in result

    def test_highlight_terms_multiple_words(self):
        """Test highlight_terms with multiple search terms."""
        text = "Python 3.11 released with new features"
        terms = ["python", "features"]
        result = self.service.highlight_terms(text, terms)

        assert "**Python**" in result
        assert "**features**" in result

    def test_highlight_terms_case_insensitive(self):
        """Test highlight_terms is case-insensitive."""
        text = "PYTHON and python and Python"
        terms = ["python"]
        result = self.service.highlight_terms(text, terms)

        # All variations should be highlighted
        assert "**PYTHON**" in result
        assert "**python**" in result or "**Python**" in result

    def test_highlight_terms_no_match(self):
        """Test highlight_terms with no matching terms."""
        text = "Rust programming language"
        terms = ["python"]
        result = self.service.highlight_terms(text, terms)

        # Text should be unchanged
        assert result == text
        assert "**" not in result

    def test_highlight_terms_empty_terms(self):
        """Test highlight_terms with empty terms list."""
        text = "Python 3.11 released"
        terms = []
        result = self.service.highlight_terms(text, terms)

        # Text should be unchanged
        assert result == text

    def test_highlight_terms_empty_text(self):
        """Test highlight_terms with empty text."""
        text = ""
        terms = ["python"]
        result = self.service.highlight_terms(text, terms)

        assert result == ""

    def test_highlight_terms_overlapping_terms(self):
        """Test highlight_terms with overlapping search terms."""
        # When we have overlapping terms like "test" and "testing",
        # the longer term should be highlighted first to avoid partial matches
        text = "Overlapping test testing"
        terms = ["test", "testing"]
        result = self.service.highlight_terms(text, terms)

        # Both terms should be highlighted correctly
        assert "**test**" in result
        assert "**testing**" in result
        # Should not have broken highlighting like **test**ing
        assert "**test**ing" not in result

    def test_search_with_valid_tags(self):
        """Test search with valid tags from TagSystem."""
        query = SearchQuery(tags=["Python"])
        result = self.service.search_posts(query)

        assert result.total_results == 1
        assert result.posts[0].title == "Python 3.11 Released"

    def test_validate_query_multiple_invalid_tags(self):
        """Test validate_query with multiple invalid tags."""
        query = SearchQuery(tags=["InvalidTag1", "InvalidTag2"])
        is_valid, errors = self.service.validate_query(query)

        assert is_valid is False
        assert len(errors) >= 2  # At least one error per invalid tag
