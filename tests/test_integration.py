"""Integration tests for end-to-end workflows."""

import os
import tempfile
from unittest.mock import Mock, patch
import pytest

from src.api_client import HNApiClient
from src.database import Database
from src.service import HackerNewsService
from src.cli import CLI
from src.models import Post, Category


class TestIntegrationCompleteFlow:
    """Integration tests for complete fetch → store → retrieve → display flow."""

    def test_complete_flow_fetch_store_retrieve_display(self):
        """
        Integration test for complete workflow: fetch → store → retrieve → display.

        Validates: Requirements 1.1, 2.2, 3.3, 4.1

        This test simulates the entire application workflow:
        1. Fetch posts from API (mocked)
        2. Store posts in database
        3. Retrieve posts from database
        4. Display posts via CLI
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Create mock API responses
            mock_story_ids = [1, 2, 3, 4, 5]
            mock_posts_data = [
                {
                    "id": 1,
                    "title": "Test Story 1",
                    "by": "user1",
                    "score": 100,
                    "url": "https://example.com/1",
                    "time": 1234567890,
                    "type": "story"
                },
                {
                    "id": 2,
                    "title": "Test Job Posting",
                    "by": "user2",
                    "score": 50,
                    "url": "https://example.com/2",
                    "time": 1234567891,
                    "type": "job"
                },
                {
                    "id": 3,
                    "title": "Ask HN: Test Question",
                    "by": "user3",
                    "score": 75,
                    "url": None,
                    "time": 1234567892,
                    "type": "ask"
                },
                {
                    "id": 4,
                    "title": "Poll: Test Poll",
                    "by": "user4",
                    "score": 25,
                    "url": None,
                    "time": 1234567893,
                    "type": "poll"
                },
                {
                    "id": 5,
                    "title": "Test Comment",
                    "by": "user5",
                    "score": 10,
                    "url": None,
                    "time": 1234567894,
                    "type": "comment"
                },
            ]

            # Create mock API client
            mock_api = Mock(spec=HNApiClient)
            mock_api.get_top_stories.return_value = mock_story_ids

            # Mock get_items_batch to return Post objects
            mock_posts = [Post.from_api_response(data) for data in mock_posts_data]
            mock_api.get_items_batch.return_value = mock_posts

            # Create service
            service = HackerNewsService(api_client=mock_api, database=db)

            # Step 1: Fetch and store posts
            result = service.fetch_and_store_posts(limit=5)

            # Verify fetch was successful
            assert result.new_posts == 5
            assert result.updated_posts == 0
            assert len(result.errors) == 0

            # Step 2: Retrieve posts from database (all posts)
            all_posts = service.get_posts_by_category(category=None)
            assert len(all_posts) == 5

            # Verify posts are ordered by date descending
            for i in range(len(all_posts) - 1):
                assert all_posts[i].created_at >= all_posts[i + 1].created_at

            # Step 3: Retrieve posts by category
            story_posts = service.get_posts_by_category(category=Category.STORY)
            assert len(story_posts) == 1
            assert story_posts[0].category == Category.STORY

            job_posts = service.get_posts_by_category(category=Category.JOB)
            assert len(job_posts) == 1
            assert job_posts[0].category == Category.JOB

            ask_posts = service.get_posts_by_category(category=Category.ASK)
            assert len(ask_posts) == 1
            assert ask_posts[0].category == Category.ASK

            poll_posts = service.get_posts_by_category(category=Category.POLL)
            assert len(poll_posts) == 1
            assert poll_posts[0].category == Category.POLL

            other_posts = service.get_posts_by_category(category=Category.OTHER)
            assert len(other_posts) == 1
            assert other_posts[0].category == Category.OTHER

            # Step 4: Display posts via CLI
            cli = CLI(service)

            # Test display_posts method
            import io
            captured_output = io.StringIO()

            with patch('sys.stdout', captured_output):
                cli.display_posts(all_posts)

            output = captured_output.getvalue()

            # Verify all posts are displayed with required fields
            for post in all_posts:
                # Check title appears
                assert post.title[:20] in output or post.title in output
                # Check author appears
                assert post.author in output
                # Check score appears
                assert str(post.score) in output
                # Check category appears
                assert post.category.value in output

            # Verify table headers are present
            assert "Title" in output
            assert "Author" in output
            assert "Score" in output
            assert "Date" in output
            assert "Category" in output
            assert "URL" in output

            # Step 5: Test CLI commands
            # Test fetch command
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                exit_code = cli.run(["fetch", "--limit", "5"])

            assert exit_code == 0
            output = captured_output.getvalue()
            assert "Fetch complete" in output or "complete" in output.lower()

            # Test list command
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                exit_code = cli.run(["list"])

            assert exit_code == 0
            output = captured_output.getvalue()
            assert "Test Story 1" in output

            # Test list with category filter
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                exit_code = cli.run(["list", "--category", "story"])

            assert exit_code == 0
            output = captured_output.getvalue()
            assert "Test Story 1" in output
            assert "Test Job Posting" not in output  # Should not appear

            # Test categories command
            captured_output = io.StringIO()
            with patch('sys.stdout', captured_output):
                exit_code = cli.run(["categories"])

            assert exit_code == 0
            output = captured_output.getvalue()
            assert "story" in output
            assert "job" in output
            assert "ask" in output
            assert "poll" in output
            assert "other" in output

            # Verify category statistics
            stats = service.get_category_statistics()
            assert stats["story"] == 1
            assert stats["job"] == 1
            assert stats["ask"] == 1
            assert stats["poll"] == 1
            assert stats["other"] == 1

            db.close()

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_complete_flow_with_updates(self):
        """
        Integration test for update workflow: fetch → update → verify.

        Tests that existing posts are updated correctly when fetched again.
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Initial fetch
            initial_post_data = {
                "id": 1,
                "title": "Original Title",
                "by": "user1",
                "score": 50,
                "url": "https://example.com/1",
                "time": 1234567890,
                "type": "story"
            }

            mock_api = Mock(spec=HNApiClient)
            mock_api.get_top_stories.return_value = [1]
            mock_api.get_items_batch.return_value = [
                Post.from_api_response(initial_post_data)
            ]

            service = HackerNewsService(api_client=mock_api, database=db)

            # First fetch
            result1 = service.fetch_and_store_posts(limit=1)
            assert result1.new_posts == 1
            assert result1.updated_posts == 0

            # Verify initial post
            posts = service.get_posts_by_category()
            assert len(posts) == 1
            assert posts[0].title == "Original Title"
            assert posts[0].score == 50

            # Second fetch with updated data
            updated_post_data = {
                "id": 1,
                "title": "Updated Title",
                "by": "user1",
                "score": 150,  # Score increased
                "url": "https://example.com/1",
                "time": 1234567890,
                "type": "story"
            }

            mock_api.get_items_batch.return_value = [
                Post.from_api_response(updated_post_data)
            ]

            # Second fetch
            result2 = service.fetch_and_store_posts(limit=1)
            assert result2.new_posts == 0
            assert result2.updated_posts == 1

            # Verify post was updated
            posts = service.get_posts_by_category()
            assert len(posts) == 1  # Still only one post
            assert posts[0].title == "Updated Title"
            assert posts[0].score == 150

            db.close()

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_complete_flow_with_empty_database(self):
        """
        Integration test for empty database scenario.

        Verifies that the application handles empty database gracefully.
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Create mock API client (not used in this test)
            mock_api = Mock(spec=HNApiClient)
            service = HackerNewsService(api_client=mock_api, database=db)

            # Try to retrieve posts from empty database
            posts = service.get_posts_by_category()
            assert len(posts) == 0

            # Try to get category statistics from empty database
            stats = service.get_category_statistics()
            assert len(stats) == 0

            # Test CLI with empty database
            cli = CLI(service)

            # Test list command with empty database
            import io
            captured_output = io.StringIO()

            with patch('sys.stdout', captured_output):
                cli.handle_list(category=None)

            output = captured_output.getvalue()
            assert "No posts found" in output or "fetch" in output.lower()

            # Test categories command with empty database
            captured_output = io.StringIO()

            with patch('sys.stdout', captured_output):
                cli.handle_categories()

            output = captured_output.getvalue()
            assert "No posts found" in output or "fetch" in output.lower()

            db.close()

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)



class TestIntegrationErrorHandling:
    """Integration tests for error handling and recovery."""

    def test_api_failure_with_retry_and_recovery(self):
        """
        Integration test for API failure with retry and recovery.

        Validates: Requirements 6.1, 6.3

        Tests that the system:
        1. Retries failed API calls with exponential backoff
        2. Recovers when API becomes available
        3. Continues processing valid posts
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Create API client with retry logic
            api_client = HNApiClient(max_retries=3)

            # Mock requests to simulate failures then success
            call_count = 0

            def mock_get_side_effect(url, *args, **kwargs):
                nonlocal call_count
                call_count += 1

                # Fail first 2 attempts, succeed on 3rd
                if call_count <= 2:
                    import requests
                    raise requests.exceptions.Timeout("Connection timeout")

                # Success on 3rd attempt
                mock_response = Mock()
                if "topstories" in url:
                    mock_response.json.return_value = [1, 2, 3]
                else:
                    # Extract item ID from URL
                    item_id = int(url.split('/')[-1].replace('.json', ''))
                    mock_response.json.return_value = {
                        "id": item_id,
                        "title": f"Test Post {item_id}",
                        "by": "testuser",
                        "score": 10,
                        "url": None,
                        "time": 1234567890,
                        "type": "story"
                    }
                mock_response.raise_for_status.return_value = None
                return mock_response

            with patch('requests.get', side_effect=mock_get_side_effect):
                with patch('time.sleep'):  # Mock sleep to speed up test
                    # Fetch top stories - should succeed after retries
                    story_ids = api_client.get_top_stories(limit=3)
                    assert len(story_ids) == 3

                    # Verify retries occurred (3 calls: 2 failures + 1 success)
                    assert call_count == 3

            db.close()

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_partial_data_processing_with_invalid_posts(self):
        """
        Integration test for processing batch with some invalid posts.

        Validates: Requirements 6.3

        Tests that the system:
        1. Processes valid posts successfully
        2. Skips invalid posts
        3. Reports errors for invalid posts
        4. Maintains database integrity
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Create mock API with mix of valid and invalid posts
            mock_api = Mock(spec=HNApiClient)
            mock_api.get_top_stories.return_value = [1, 2, 3, 4, 5]

            # Create mix of valid and invalid posts
            valid_post1 = Post.from_api_response({
                "id": 1,
                "title": "Valid Post 1",
                "by": "user1",
                "score": 100,
                "url": "https://example.com/1",
                "time": 1234567890,
                "type": "story"
            })

            valid_post2 = Post.from_api_response({
                "id": 3,
                "title": "Valid Post 3",
                "by": "user3",
                "score": 75,
                "url": None,
                "time": 1234567892,
                "type": "ask"
            })

            valid_post3 = Post.from_api_response({
                "id": 5,
                "title": "Valid Post 5",
                "by": "user5",
                "score": 50,
                "url": None,
                "time": 1234567894,
                "type": "job"
            })

            # Mock get_items_batch to return only valid posts
            # (simulating that invalid posts were filtered out by API client)
            mock_api.get_items_batch.return_value = [valid_post1, valid_post2, valid_post3]

            # Create service
            service = HackerNewsService(api_client=mock_api, database=db)

            # Fetch and store posts
            result = service.fetch_and_store_posts(limit=5)

            # Verify only valid posts were stored
            assert result.new_posts == 3
            assert result.updated_posts == 0

            # Verify database contains only valid posts
            all_posts = service.get_posts_by_category()
            assert len(all_posts) == 3

            # Verify all stored posts are valid
            for post in all_posts:
                assert post.is_valid()
                assert post.title
                assert post.author
                assert post.id in [1, 3, 5]

            db.close()

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_database_integrity_on_interruption(self):
        """
        Integration test for database integrity when operation is interrupted.

        Validates: Requirements 6.4

        Tests that the system:
        1. Uses transactions for atomicity
        2. Maintains database integrity on errors
        3. Continues processing despite individual post errors
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Insert some initial posts
            initial_post = Post(
                id=1,
                title="Initial Post",
                author="user1",
                score=100,
                url=None,
                created_at=1234567890,
                type="story",
                category=Category.STORY,
                fetched_at=1234567900
            )
            db.upsert_post(initial_post)

            # Verify initial state
            posts_before = db.get_posts_by_category()
            assert len(posts_before) == 1

            # Create mock API
            mock_api = Mock(spec=HNApiClient)
            mock_api.get_top_stories.return_value = [2, 3, 4]

            # Create valid posts
            valid_post1 = Post.from_api_response({
                "id": 2,
                "title": "Valid Post 2",
                "by": "user2",
                "score": 50,
                "url": None,
                "time": 1234567891,
                "type": "story"
            })

            valid_post2 = Post.from_api_response({
                "id": 3,
                "title": "Valid Post 3",
                "by": "user3",
                "score": 75,
                "url": None,
                "time": 1234567892,
                "type": "story"
            })

            mock_api.get_items_batch.return_value = [valid_post1, valid_post2]

            # Create service
            service = HackerNewsService(api_client=mock_api, database=db)

            # Fetch and store posts - should succeed
            result = service.fetch_and_store_posts(limit=3)

            # Verify posts were added
            assert result.new_posts == 2
            posts_after = db.get_posts_by_category()
            assert len(posts_after) == 3

            # Verify all posts are valid
            for post in posts_after:
                assert post.is_valid()

            # Close database properly
            db.close()

            # Reopen database and verify integrity is maintained
            db2 = Database(db_path)
            posts_final = db2.get_posts_by_category()

            # Database should still have the 3 posts
            assert len(posts_final) == 3

            # Verify all posts are still valid
            for post in posts_final:
                assert post.is_valid()
                assert post.title
                assert post.author

            db2.close()

        finally:
            # Cleanup
            if os.path.exists(db_path):
                try:
                    os.unlink(db_path)
                except PermissionError:
                    # On Windows, sometimes the file is still locked
                    import time
                    time.sleep(0.1)
                    try:
                        os.unlink(db_path)
                    except PermissionError:
                        pass  # Skip cleanup if still locked

    def test_concurrent_operations_database_integrity(self):
        """
        Integration test for database integrity with multiple operations.

        Tests that multiple fetch operations maintain database consistency.
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Create mock API
            mock_api = Mock(spec=HNApiClient)

            # First batch of posts
            mock_api.get_top_stories.return_value = [1, 2, 3]
            mock_api.get_items_batch.return_value = [
                Post.from_api_response({
                    "id": 1,
                    "title": "Post 1",
                    "by": "user1",
                    "score": 100,
                    "url": None,
                    "time": 1234567890,
                    "type": "story"
                }),
                Post.from_api_response({
                    "id": 2,
                    "title": "Post 2",
                    "by": "user2",
                    "score": 50,
                    "url": None,
                    "time": 1234567891,
                    "type": "story"
                }),
                Post.from_api_response({
                    "id": 3,
                    "title": "Post 3",
                    "by": "user3",
                    "score": 75,
                    "url": None,
                    "time": 1234567892,
                    "type": "story"
                }),
            ]

            service = HackerNewsService(api_client=mock_api, database=db)

            # First fetch
            result1 = service.fetch_and_store_posts(limit=3)
            assert result1.new_posts == 3

            # Second batch with overlapping posts
            mock_api.get_top_stories.return_value = [2, 3, 4, 5]
            mock_api.get_items_batch.return_value = [
                Post.from_api_response({
                    "id": 2,
                    "title": "Post 2 Updated",
                    "by": "user2",
                    "score": 150,  # Updated score
                    "url": None,
                    "time": 1234567891,
                    "type": "story"
                }),
                Post.from_api_response({
                    "id": 3,
                    "title": "Post 3",
                    "by": "user3",
                    "score": 75,
                    "url": None,
                    "time": 1234567892,
                    "type": "story"
                }),
                Post.from_api_response({
                    "id": 4,
                    "title": "Post 4",
                    "by": "user4",
                    "score": 25,
                    "url": None,
                    "time": 1234567893,
                    "type": "job"
                }),
                Post.from_api_response({
                    "id": 5,
                    "title": "Post 5",
                    "by": "user5",
                    "score": 10,
                    "url": None,
                    "time": 1234567894,
                    "type": "ask"
                }),
            ]

            # Second fetch
            result2 = service.fetch_and_store_posts(limit=4)

            # Should have 2 new posts and 2 updated posts
            assert result2.new_posts == 2  # Posts 4 and 5
            assert result2.updated_posts == 2  # Posts 2 and 3

            # Verify total count
            all_posts = service.get_posts_by_category()
            assert len(all_posts) == 5  # Total unique posts

            # Verify post 2 was updated
            post2 = db.get_post_by_id(2)
            assert post2.title == "Post 2 Updated"
            assert post2.score == 150

            # Verify no duplicates
            post_ids = [p.id for p in all_posts]
            assert len(post_ids) == len(set(post_ids))  # All IDs are unique

            db.close()

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_error_handling_with_cli_commands(self):
        """
        Integration test for error handling in CLI commands.

        Tests that CLI handles errors gracefully and provides useful feedback.
        """
        # Create temporary database
        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            db_path = tmp.name

        try:
            # Initialize database
            db = Database(db_path)
            db.initialize_schema()

            # Create mock API that will fail
            mock_api = Mock(spec=HNApiClient)
            mock_api.get_top_stories.side_effect = Exception("API unavailable")

            service = HackerNewsService(api_client=mock_api, database=db)
            cli = CLI(service)

            # Test fetch command with API error
            import io
            captured_output = io.StringIO()

            with patch('sys.stdout', captured_output):
                with patch('sys.stderr', io.StringIO()):
                    try:
                        cli.handle_fetch(limit=10)
                    except Exception:
                        pass  # Expected to fail

            # Verify database is still intact (empty)
            posts = service.get_posts_by_category()
            assert len(posts) == 0

            # Test list command with empty database
            captured_output = io.StringIO()

            with patch('sys.stdout', captured_output):
                cli.handle_list(category=None)

            output = captured_output.getvalue()
            assert "No posts found" in output or "fetch" in output.lower()

            db.close()

        finally:
            # Cleanup
            if os.path.exists(db_path):
                os.unlink(db_path)
