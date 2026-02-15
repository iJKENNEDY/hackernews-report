"""Command-line interface for Hackernews Report application."""

import argparse
import sys
import logging
from typing import List, Optional
from datetime import datetime

from src.service import HackerNewsService
from src.models import Category, Post


# Configure logging
logger = logging.getLogger(__name__)


class CLI:
    """
    Command-line interface for interacting with Hackernews Report.
    
    Provides commands for fetching posts, listing posts, and viewing category statistics.
    
    Attributes:
        service: HackerNewsService instance for business logic operations
    """
    
    def __init__(self, service: HackerNewsService):
        """
        Initialize the CLI with a service instance.
        
        Args:
            service: Configured HackerNewsService instance
        """
        self.service = service
    
    def run(self, args: List[str]) -> int:
        """
        Main entry point for the CLI. Parses arguments and executes commands.
        
        Args:
            args: Command-line arguments (typically sys.argv[1:])
            
        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        parser = argparse.ArgumentParser(
            prog="hackernews-report",
            description="Fetch, store, and view Hacker News posts organized by category"
        )
        
        # Create subparsers for different commands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Fetch command
        fetch_parser = subparsers.add_parser(
            "fetch",
            help="Fetch new posts from Hacker News API"
        )
        fetch_parser.add_argument(
            "--limit",
            type=int,
            default=30,
            help="Maximum number of posts to fetch (default: 30)"
        )
        
        # List command
        list_parser = subparsers.add_parser(
            "list",
            help="List posts from the database"
        )
        list_parser.add_argument(
            "--category",
            type=str,
            choices=["story", "job", "ask", "poll", "other"],
            help="Filter posts by category"
        )
        
        # Categories command
        categories_parser = subparsers.add_parser(
            "categories",
            help="Show statistics for each category"
        )
        
        # Parse arguments
        parsed_args = parser.parse_args(args)
        
        # Handle no command provided
        if not parsed_args.command:
            parser.print_help()
            return 1
        
        # Execute the appropriate command
        try:
            if parsed_args.command == "fetch":
                self.handle_fetch(parsed_args.limit)
                return 0
            elif parsed_args.command == "list":
                category = None
                if parsed_args.category:
                    category = Category(parsed_args.category)
                self.handle_list(category)
                return 0
            elif parsed_args.command == "categories":
                self.handle_categories()
                return 0
            else:
                print(f"Unknown command: {parsed_args.command}", file=sys.stderr)
                return 1
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def handle_fetch(self, limit: int) -> None:
        """
        Handle the fetch command - retrieve posts from Hacker News API.
        
        Args:
            limit: Maximum number of posts to fetch
        """
        print(f"Fetching up to {limit} posts from Hacker News...")
        
        try:
            result = self.service.fetch_and_store_posts(limit=limit)
            
            # Display results
            print(f"\n✓ Fetch complete!")
            print(f"  New posts: {result.new_posts}")
            print(f"  Updated posts: {result.updated_posts}")
            
            if result.errors:
                print(f"\n⚠ Encountered {len(result.errors)} errors:")
                for error in result.errors[:5]:  # Show first 5 errors
                    print(f"  - {error}")
                if len(result.errors) > 5:
                    print(f"  ... and {len(result.errors) - 5} more errors")
            
            if result.new_posts == 0 and result.updated_posts == 0:
                print("\nNo posts were fetched. Check the errors above for details.")
            
        except Exception as e:
            logger.error(f"Fetch operation failed: {e}")
            print(f"\n✗ Error: Failed to fetch posts - {e}", file=sys.stderr)
            raise
    
    def handle_list(self, category: Optional[Category]) -> None:
        """
        Handle the list command - display posts from the database.
        
        Args:
            category: Optional category filter
        """
        try:
            # Fetch posts from database
            posts = self.service.get_posts_by_category(category=category)
            
            if not posts:
                if category:
                    print(f"No posts found in category '{category.value}'")
                else:
                    print("No posts found in database. Try running 'fetch' first.")
                return
            
            # Display header
            if category:
                print(f"\nPosts in category '{category.value}' ({len(posts)} total):\n")
            else:
                print(f"\nAll posts ({len(posts)} total):\n")
            
            # Display posts in table format
            self.display_posts(posts)
            
        except Exception as e:
            logger.error(f"List operation failed: {e}")
            print(f"\n✗ Error: Failed to list posts - {e}", file=sys.stderr)
            raise
    
    def handle_categories(self) -> None:
        """
        Handle the categories command - show category statistics.
        """
        try:
            # Get category statistics from service
            stats = self.service.get_category_statistics()
            
            if not stats:
                print("No posts found in database. Try running 'fetch' first.")
                return
            
            # Display header
            print("\nPost Statistics by Category:\n")
            
            # Calculate total
            total = sum(stats.values())
            
            # Print table header
            print(f"{'Category':<15} {'Count':>8} {'Percentage':>12}")
            print("-" * 40)
            
            # Sort categories by count (descending)
            sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
            
            # Print each category
            for category, count in sorted_stats:
                percentage = (count / total * 100) if total > 0 else 0
                print(f"{category:<15} {count:>8} {percentage:>11.1f}%")
            
            # Print total
            print("-" * 40)
            print(f"{'Total':<15} {total:>8} {100.0:>11.1f}%")
            
        except Exception as e:
            logger.error(f"Categories operation failed: {e}")
            print(f"\n✗ Error: Failed to retrieve category statistics - {e}", file=sys.stderr)
            raise
    
    def display_posts(self, posts: List[Post]) -> None:
        """
        Display a list of posts in a formatted table.
        
        Includes: title, author, score, date, category, and URL.
        Posts are displayed in descending order by creation date.
        
        Args:
            posts: List of Post objects to display
        """
        if not posts:
            return
        
        # Table formatting
        # Calculate column widths
        max_title_width = 60
        max_author_width = 15
        
        # Print table header
        print(f"{'Title':<{max_title_width}} {'Author':<{max_author_width}} {'Score':>6} {'Date':<12} {'Category':<8} {'URL'}")
        print("-" * (max_title_width + max_author_width + 6 + 12 + 8 + 50))
        
        # Print each post
        for post in posts:
            # Truncate title if too long
            title = post.title
            if len(title) > max_title_width:
                title = title[:max_title_width - 3] + "..."
            
            # Truncate author if too long
            author = post.author
            if len(author) > max_author_width:
                author = author[:max_author_width - 3] + "..."
            
            # Format date
            date_str = datetime.fromtimestamp(post.created_at).strftime("%Y-%m-%d")
            
            # Format category
            category_str = post.category.value
            
            # Format URL (make it clickable)
            url_str = post.url if post.url else "(no url)"
            
            # Print row
            print(f"{title:<{max_title_width}} {author:<{max_author_width}} {post.score:>6} {date_str:<12} {category_str:<8} {url_str}")
