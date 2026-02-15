"""Unit tests for data models."""

import pytest
import time
from src.models import Post, Category, categorize_post


class TestCategory:
    """Tests for Category enum and categorize_post function."""
    
    def test_categorize_known_types(self):
        """Test that known post types map to correct categories."""
        assert categorize_post("story") == Category.STORY
        assert categorize_post("job") == Category.JOB
        assert categorize_post("ask") == Category.ASK
        assert categorize_post("poll") == Category.POLL
    
    def test_categorize_unknown_type(self):
        """Test that unknown types map to OTHER category."""
        assert categorize_post("unknown") == Category.OTHER
        assert categorize_post("comment") == Category.OTHER
        assert categorize_post("") == Category.OTHER


class TestPost:
    """Tests for Post dataclass."""
    
    def test_post_creation(self):
        """Test creating a valid Post instance."""
        post = Post(
            id=1,
            title="Test Post",
            author="testuser",
            score=100,
            url="https://example.com",
            created_at=1234567890,
            type="story",
            category=Category.STORY,
            fetched_at=1234567900,
        )
        
        assert post.id == 1
        assert post.title == "Test Post"
        assert post.author == "testuser"
        assert post.score == 100
        assert post.url == "https://example.com"
        assert post.created_at == 1234567890
        assert post.type == "story"
        assert post.category == Category.STORY
        assert post.fetched_at == 1234567900
    
    def test_is_valid_with_valid_post(self):
        """Test is_valid returns True for a valid post."""
        post = Post(
            id=1,
            title="Test",
            author="user",
            score=10,
            url="https://example.com",
            created_at=1234567890,
            type="story",
            category=Category.STORY,
            fetched_at=1234567900,
        )
        assert post.is_valid() is True
    
    def test_is_valid_with_null_url(self):
        """Test is_valid returns True when URL is None."""
        post = Post(
            id=1,
            title="Test",
            author="user",
            score=10,
            url=None,
            created_at=1234567890,
            type="ask",
            category=Category.ASK,
            fetched_at=1234567900,
        )
        assert post.is_valid() is True
    
    def test_is_valid_with_invalid_id(self):
        """Test is_valid returns False for invalid id."""
        post = Post(
            id=0,
            title="Test",
            author="user",
            score=10,
            url=None,
            created_at=1234567890,
            type="story",
            category=Category.STORY,
            fetched_at=1234567900,
        )
        assert post.is_valid() is False
    
    def test_is_valid_with_empty_title(self):
        """Test is_valid returns False for empty title."""
        post = Post(
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
        assert post.is_valid() is False
    
    def test_is_valid_with_negative_score(self):
        """Test is_valid returns False for negative score."""
        post = Post(
            id=1,
            title="Test",
            author="user",
            score=-1,
            url=None,
            created_at=1234567890,
            type="story",
            category=Category.STORY,
            fetched_at=1234567900,
        )
        assert post.is_valid() is False
    
    def test_to_dict(self):
        """Test converting post to dictionary."""
        post = Post(
            id=1,
            title="Test Post",
            author="testuser",
            score=100,
            url="https://example.com",
            created_at=1234567890,
            type="story",
            category=Category.STORY,
            fetched_at=1234567900,
        )
        
        result = post.to_dict()
        
        assert result["id"] == 1
        assert result["title"] == "Test Post"
        assert result["author"] == "testuser"
        assert result["score"] == 100
        assert result["url"] == "https://example.com"
        assert result["created_at"] == 1234567890
        assert result["type"] == "story"
        assert result["category"] == "story"
        assert result["fetched_at"] == 1234567900
    
    def test_from_api_response(self):
        """Test creating post from API response data."""
        api_data = {
            "id": 12345,
            "title": "API Test Post",
            "by": "apiuser",
            "score": 250,
            "url": "https://api.example.com",
            "time": 1234567890,
            "type": "story",
        }
        
        post = Post.from_api_response(api_data)
        
        assert post.id == 12345
        assert post.title == "API Test Post"
        assert post.author == "apiuser"
        assert post.score == 250
        assert post.url == "https://api.example.com"
        assert post.created_at == 1234567890
        assert post.type == "story"
        assert post.category == Category.STORY
        assert post.fetched_at > 0
    
    def test_from_api_response_with_missing_optional_fields(self):
        """Test creating post from API response with missing optional fields."""
        api_data = {
            "id": 12345,
            "type": "ask",
        }
        
        post = Post.from_api_response(api_data)
        
        assert post.id == 12345
        assert post.title == ""
        assert post.author == ""
        assert post.score == 0
        assert post.url is None
        assert post.created_at == 0
        assert post.type == "ask"
        assert post.category == Category.ASK
    
    def test_from_api_response_categorizes_correctly(self):
        """Test that from_api_response correctly categorizes posts."""
        for post_type, expected_category in [
            ("story", Category.STORY),
            ("job", Category.JOB),
            ("ask", Category.ASK),
            ("poll", Category.POLL),
            ("unknown", Category.OTHER),
        ]:
            api_data = {
                "id": 1,
                "type": post_type,
            }
            post = Post.from_api_response(api_data)
            assert post.category == expected_category
    
    def test_from_db_row(self):
        """Test creating post from database row."""
        db_row = (
            1,
            "DB Test Post",
            "dbuser",
            150,
            "https://db.example.com",
            1234567890,
            "job",
            "job",
            1234567900,
        )
        
        post = Post.from_db_row(db_row)
        
        assert post.id == 1
        assert post.title == "DB Test Post"
        assert post.author == "dbuser"
        assert post.score == 150
        assert post.url == "https://db.example.com"
        assert post.created_at == 1234567890
        assert post.type == "job"
        assert post.category == Category.JOB
        assert post.fetched_at == 1234567900
    
    def test_from_db_row_with_null_url(self):
        """Test creating post from database row with NULL url."""
        db_row = (
            1,
            "DB Test Post",
            "dbuser",
            150,
            None,
            1234567890,
            "ask",
            "ask",
            1234567900,
        )
        
        post = Post.from_db_row(db_row)
        
        assert post.url is None
        assert post.category == Category.ASK
    
    def test_roundtrip_to_dict_consistency(self):
        """Test that to_dict produces consistent output."""
        post = Post(
            id=1,
            title="Test",
            author="user",
            score=10,
            url=None,
            created_at=1234567890,
            type="poll",
            category=Category.POLL,
            fetched_at=1234567900,
        )
        
        dict1 = post.to_dict()
        dict2 = post.to_dict()
        
        assert dict1 == dict2


# Property-Based Tests
from hypothesis import given, strategies as st


class TestCategoryProperties:
    """Property-based tests for category mapping."""

    @given(st.sampled_from(["story", "job", "ask", "poll"]))
    def test_property_known_types_map_correctly(self, post_type: str):
        """
        Property 6: Mapeo correcto de categorías
        Validates: Requirements 3.1, 3.2

        For any post with known type (story, job, ask, poll),
        the system must assign the correct corresponding category.
        """
        category = categorize_post(post_type)

        # Verify the mapping is correct
        expected_mapping = {
            "story": Category.STORY,
            "job": Category.JOB,
            "ask": Category.ASK,
            "poll": Category.POLL,
        }

        assert category == expected_mapping[post_type]
        assert category.value == post_type

    @given(st.text().filter(lambda x: x not in ["story", "job", "ask", "poll"]))
    def test_property_unknown_types_default_to_other(self, post_type: str):
        """
        Property 7: Categoría por defecto para tipos desconocidos
        Validates: Requirements 3.4

        For any post with unrecognized type, the system must
        assign it to the "other" category.
        """
        category = categorize_post(post_type)

        assert category == Category.OTHER
        assert category.value == "other"
