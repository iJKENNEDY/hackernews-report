"""Tests for the Hacker News API client."""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings
import time

from src.api_client import HNApiClient, RetryStrategy
from src.models import Post, Category


# Hypothesis strategies for generating test data
@st.composite
def valid_api_response(draw):
    """Generate a valid API response with all required fields."""
    return {
        "id": draw(st.integers(min_value=1, max_value=1000000)),
        "title": draw(st.text(min_size=1, max_size=200)),
        "by": draw(st.text(min_size=1, max_size=50)),
        "score": draw(st.integers(min_value=0, max_value=10000)),
        "url": draw(st.one_of(st.none(), st.text(min_size=1, max_size=200))),
        "time": draw(st.integers(min_value=1, max_value=2000000000)),
        "type": draw(st.sampled_from(["story", "job", "ask", "poll", "comment"])),
    }


@st.composite
def incomplete_api_response(draw):
    """Generate an API response with missing required fields."""
    # Start with a valid response
    response = {
        "id": draw(st.integers(min_value=1, max_value=1000000)),
        "title": draw(st.text(min_size=1, max_size=200)),
        "by": draw(st.text(min_size=1, max_size=50)),
        "score": draw(st.integers(min_value=0, max_value=10000)),
        "url": draw(st.one_of(st.none(), st.text(min_size=1, max_size=200))),
        "time": draw(st.integers(min_value=1, max_value=2000000000)),
        "type": draw(st.sampled_from(["story", "job", "ask", "poll"])),
    }
    
    # Remove at least one required field
    required_fields = ["id", "title", "by", "time", "type"]
    field_to_remove = draw(st.sampled_from(required_fields))
    del response[field_to_remove]
    
    return response


class TestRetryStrategy:
    """Tests for RetryStrategy class."""
    
    def test_calculate_delay_exponential(self):
        """Test that delays follow exponential backoff pattern."""
        strategy = RetryStrategy(max_attempts=3, base_delay=1.0, max_delay=10.0)
        
        assert strategy.calculate_delay(0) == 1.0  # 1 * 2^0
        assert strategy.calculate_delay(1) == 2.0  # 1 * 2^1
        assert strategy.calculate_delay(2) == 4.0  # 1 * 2^2
    
    def test_calculate_delay_respects_max(self):
        """Test that delay doesn't exceed max_delay."""
        strategy = RetryStrategy(max_attempts=5, base_delay=1.0, max_delay=5.0)
        
        assert strategy.calculate_delay(10) == 5.0  # Would be 1024, capped at 5


class TestHNApiClient:
    """Tests for HNApiClient class."""
    
    def test_initialization(self):
        """Test client initialization with default and custom values."""
        # Default initialization
        client = HNApiClient()
        assert client.base_url == "https://hacker-news.firebaseio.com/v0"
        assert client.max_retries == 3
        assert client.timeout == 10
        
        # Custom initialization
        client = HNApiClient(
            base_url="https://custom.api.com/",
            max_retries=5,
            timeout=20
        )
        assert client.base_url == "https://custom.api.com"
        assert client.max_retries == 5
        assert client.timeout == 20


# Feature: hackernews-report, Property 1: Validación de campos completos
# Validates: Requirements 1.2, 1.5
@settings(max_examples=100)
@given(api_data=valid_api_response())
def test_property_complete_field_validation(api_data):
    """
    Property 1: For any post obtained from the API, the system must validate
    that it contains all required fields before processing it.
    
    This test verifies that when given complete API data, the client
    successfully creates a valid Post object.
    """
    client = HNApiClient()
    
    # Mock the requests.get to return our test data
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = api_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Get the item
        post = client.get_item(api_data["id"])
        
        # If the post was created, it must be valid
        if post is not None:
            assert post.is_valid(), "Post created from complete API data must be valid"
            assert post.id == api_data["id"]
            assert post.title == api_data["title"]
            assert post.author == api_data["by"]
            assert post.score == api_data["score"]
            assert post.url == api_data.get("url")
            assert post.created_at == api_data["time"]
            assert post.type == api_data["type"]


# Feature: hackernews-report, Property 1: Validación de campos completos (incomplete data)
# Validates: Requirements 1.2, 1.5
@settings(max_examples=100)
@given(api_data=incomplete_api_response())
def test_property_incomplete_field_rejection(api_data):
    """
    Property 1 (negative case): For any post with incomplete data from the API,
    the system must reject it and return None.
    
    This test verifies that incomplete API responses are properly rejected.
    """
    client = HNApiClient()
    
    # Mock the requests.get to return our incomplete test data
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = api_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Get the item - should return None for incomplete data
        post = client.get_item(api_data.get("id", 1))
        
        # Incomplete data should result in None
        assert post is None, "Post with incomplete data must be rejected (return None)"



# Feature: hackernews-report, Property 15: Reintentos con backoff exponencial
# Validates: Requirements 6.1
@settings(max_examples=100)
@given(
    item_id=st.integers(min_value=1, max_value=1000000),
    failure_count=st.integers(min_value=1, max_value=3)
)
def test_property_retry_with_exponential_backoff(item_id, failure_count):
    """
    Property 15: For any API connection failure, the system must perform
    exactly 3 retry attempts with exponential delays (1s, 2s, 4s) before
    reporting the error.
    
    This test verifies the retry mechanism with exponential backoff.
    """
    client = HNApiClient(max_retries=3)
    
    # Track retry attempts and delays
    call_count = 0
    sleep_calls = []
    
    def mock_get_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= failure_count:
            raise requests.exceptions.Timeout("Connection timeout")
        # Success on subsequent attempts
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": item_id,
            "title": "Test",
            "by": "author",
            "score": 10,
            "url": None,
            "time": 1234567890,
            "type": "story"
        }
        mock_response.raise_for_status.return_value = None
        return mock_response
    
    def mock_sleep(seconds):
        sleep_calls.append(seconds)
    
    with patch('requests.get', side_effect=mock_get_side_effect):
        with patch('time.sleep', side_effect=mock_sleep):
            if failure_count < 3:
                # Should succeed after retries
                post = client.get_item(item_id)
                
                # Verify retry attempts
                assert call_count == failure_count + 1, \
                    f"Expected {failure_count + 1} attempts, got {call_count}"
                
                # Verify exponential backoff delays
                expected_delays = [1.0, 2.0, 4.0][:failure_count]
                assert sleep_calls == expected_delays, \
                    f"Expected delays {expected_delays}, got {sleep_calls}"
                
                # Should eventually succeed
                assert post is not None
            else:
                # Should fail after 3 attempts
                with pytest.raises(requests.exceptions.Timeout):
                    client.get_item(item_id)
                
                # Verify exactly 3 attempts were made
                assert call_count == 3, f"Expected 3 attempts, got {call_count}"
                
                # Verify exponential backoff delays (2 delays for 3 attempts)
                expected_delays = [1.0, 2.0]
                assert sleep_calls == expected_delays, \
                    f"Expected delays {expected_delays}, got {sleep_calls}"



# Feature: hackernews-report, Property 16: Procesamiento parcial con datos inválidos
# Validates: Requirements 6.3
@settings(max_examples=100)
@given(
    valid_count=st.integers(min_value=1, max_value=10),
    invalid_count=st.integers(min_value=1, max_value=5)
)
def test_property_partial_processing_with_invalid_data(valid_count, invalid_count):
    """
    Property 16: For any batch of posts that contains some invalid posts,
    the system must successfully process all valid posts and omit only
    the invalid ones.
    
    This test verifies that the batch processing continues even when
    some items are invalid.
    """
    client = HNApiClient()
    
    # Generate unique IDs for valid and invalid items
    valid_ids = list(range(1, valid_count + 1))
    invalid_ids = list(range(1000, 1000 + invalid_count))
    
    # Create valid responses
    valid_items = {
        item_id: {
            "id": item_id,
            "title": f"Valid Title {item_id}",
            "by": f"author{item_id}",
            "score": 10,
            "url": None,
            "time": 1234567890,
            "type": "story"
        }
        for item_id in valid_ids
    }
    
    # Create invalid responses (missing title)
    invalid_items = {
        item_id: {
            "id": item_id,
            "by": f"author{item_id}",
            "score": 10,
            "url": None,
            "time": 1234567890,
            "type": "story"
            # Missing "title" field
        }
        for item_id in invalid_ids
    }
    
    # Combine all items
    all_items = {**valid_items, **invalid_items}
    all_ids = valid_ids + invalid_ids
    
    def mock_get_side_effect(url, *args, **kwargs):
        # Extract item_id from URL
        item_id = int(url.split('/')[-1].replace('.json', ''))
        
        mock_response = Mock()
        mock_response.json.return_value = all_items.get(item_id)
        mock_response.raise_for_status.return_value = None
        return mock_response
    
    with patch('requests.get', side_effect=mock_get_side_effect):
        posts = client.get_items_batch(all_ids)
        
        # Verify that we got exactly the number of valid items
        assert len(posts) == valid_count, \
            f"Expected {valid_count} valid posts, got {len(posts)}"
        
        # Verify all returned posts are valid
        for post in posts:
            assert post.is_valid(), "All returned posts must be valid"
        
        # Verify that valid item IDs are in the results
        result_ids = {post.id for post in posts}
        assert result_ids == set(valid_ids), \
            "Result should contain exactly the valid item IDs"



class TestErrorHandling:
    """Unit tests for error handling scenarios."""
    
    def test_api_unavailable_with_logging(self):
        """Test that API unavailability is logged appropriately."""
        client = HNApiClient(max_retries=3)
        
        with patch('requests.get') as mock_get:
            # Simulate connection error
            mock_get.side_effect = requests.exceptions.ConnectionError("API unavailable")
            
            with patch('src.api_client.logger') as mock_logger:
                with pytest.raises(requests.exceptions.ConnectionError):
                    client.get_item(123)
                
                # Verify warning logs for retries
                assert mock_logger.warning.call_count == 2  # 2 retries before final failure
                
                # Verify error log for final failure
                assert mock_logger.error.call_count == 1
                error_call = mock_logger.error.call_args[0][0]
                assert "failed after 3 attempts" in error_call.lower()
    
    def test_rate_limiting(self):
        """Test that rate limiting (429) triggers retry with backoff."""
        client = HNApiClient(max_retries=3)
        
        call_count = 0
        sleep_calls = []
        
        def mock_get_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count < 3:
                # Return 429 for first 2 attempts
                mock_response = Mock()
                mock_response.status_code = 429
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                    response=mock_response
                )
                return mock_response
            else:
                # Success on 3rd attempt
                mock_response = Mock()
                mock_response.json.return_value = {
                    "id": 123,
                    "title": "Test",
                    "by": "author",
                    "score": 10,
                    "url": None,
                    "time": 1234567890,
                    "type": "story"
                }
                mock_response.raise_for_status.return_value = None
                return mock_response
        
        def mock_sleep(seconds):
            sleep_calls.append(seconds)
        
        with patch('requests.get', side_effect=mock_get_side_effect):
            with patch('time.sleep', side_effect=mock_sleep):
                post = client.get_item(123)
                
                # Should succeed after retries
                assert post is not None
                assert post.id == 123
                
                # Verify exponential backoff was used
                assert sleep_calls == [1.0, 2.0]
    
    def test_incomplete_data_handling(self):
        """Test that incomplete data is properly rejected and logged."""
        client = HNApiClient()
        
        incomplete_responses = [
            {},  # Empty response
            {"id": 123},  # Missing all other fields
            {"id": 123, "title": "Test"},  # Missing author, time, type
            {"id": 123, "title": "", "by": "author", "time": 123, "type": "story"},  # Empty title
            {"id": 123, "title": "Test", "by": "", "time": 123, "type": "story"},  # Empty author
        ]
        
        for incomplete_data in incomplete_responses:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.json.return_value = incomplete_data
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                with patch('src.api_client.logger') as mock_logger:
                    post = client.get_item(123)
                    
                    # Should return None for incomplete data
                    assert post is None
                    
                    # Should log a warning
                    assert mock_logger.warning.call_count >= 1
    
    def test_http_client_error_no_retry(self):
        """Test that 4xx client errors (except 429) don't trigger retries."""
        client = HNApiClient(max_retries=3)
        
        for status_code in [400, 401, 403, 404]:
            call_count = 0
            
            def mock_get_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                
                mock_response = Mock()
                mock_response.status_code = status_code
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                    response=mock_response
                )
                return mock_response
            
            with patch('requests.get', side_effect=mock_get_side_effect):
                with pytest.raises(requests.exceptions.HTTPError):
                    client.get_item(123)
                
                # Should only attempt once (no retries for 4xx except 429)
                assert call_count == 1
    
    def test_http_server_error_with_retry(self):
        """Test that 5xx server errors trigger retries."""
        client = HNApiClient(max_retries=3)
        
        call_count = 0
        
        def mock_get_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                response=mock_response
            )
            return mock_response
        
        with patch('requests.get', side_effect=mock_get_side_effect):
            with patch('time.sleep'):  # Mock sleep to speed up test
                with pytest.raises(requests.exceptions.HTTPError):
                    client.get_item(123)
                
                # Should attempt 3 times (initial + 2 retries)
                assert call_count == 3
    
    def test_json_decode_error_no_retry(self):
        """Test that JSON decode errors don't trigger retries."""
        client = HNApiClient(max_retries=3)
        
        call_count = 0
        
        def mock_get_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.JSONDecodeError("Invalid JSON", "", 0)
        
        with patch('requests.get', side_effect=mock_get_side_effect):
            with pytest.raises(requests.exceptions.JSONDecodeError):
                client.get_item(123)
            
            # Should only attempt once (no retries for JSON errors)
            assert call_count == 1
    
    def test_timeout_with_retry(self):
        """Test that timeouts trigger retries with exponential backoff."""
        client = HNApiClient(max_retries=3)
        
        call_count = 0
        sleep_calls = []
        
        def mock_get_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise requests.exceptions.Timeout("Request timeout")
        
        def mock_sleep(seconds):
            sleep_calls.append(seconds)
        
        with patch('requests.get', side_effect=mock_get_side_effect):
            with patch('time.sleep', side_effect=mock_sleep):
                with pytest.raises(requests.exceptions.Timeout):
                    client.get_item(123)
                
                # Should attempt 3 times
                assert call_count == 3
                
                # Should have 2 sleep calls with exponential backoff
                assert sleep_calls == [1.0, 2.0]
    
    def test_null_response_handling(self):
        """Test that null responses (deleted items) are handled gracefully."""
        client = HNApiClient()
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = None  # Deleted/dead item
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with patch('src.api_client.logger') as mock_logger:
                post = client.get_item(123)
                
                # Should return None
                assert post is None
                
                # Should log a warning
                assert mock_logger.warning.call_count == 1
                warning_msg = mock_logger.warning.call_args[0][0]
                assert "null" in warning_msg.lower() or "deleted" in warning_msg.lower()
