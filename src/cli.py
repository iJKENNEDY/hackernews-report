"""Command-line interface for Hackernews Report application."""

import argparse
import sys
import logging
from typing import List, Optional
from datetime import datetime
from src.report_service import ReportService, ReportFormat
from src.search_service import SearchService
from src.service import HackerNewsService
from src.models import Category, Post, SearchQuery
from src.tags import TagSystem


# Configure logging
logger = logging.getLogger(__name__)


class CLI:
    """
    Command-line interface for interacting with Hackernews Report.
    
    Provides commands for fetching posts, listing posts, searching, viewing category statistics, and generating reports.
    
    Attributes:
        service: HackerNewsService instance for business logic operations
        search_service: SearchService instance for search operations
        report_service: ReportService instance for report generation
    """
    
    def __init__(self, service: HackerNewsService, search_service: Optional[SearchService] = None, report_service: Optional[ReportService] = None):
        """
        Initialize the CLI with service instances.
        
        Args:
            service: Configured HackerNewsService instance
            search_service: Configured SearchService instance (optional)
            report_service: Configured ReportService instance (optional)
        """
        self.service = service
        self.search_service = search_service
        self.report_service = report_service
    
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
        list_parser.add_argument(
            "--no-ai-filter",
            action="store_true",
            help="Disable highlighting of AI priority terms"
        )
        
        # Categories command
        categories_parser = subparsers.add_parser(
            "categories",
            help="Show statistics for each category"
        )

        # Search command
        search_parser = subparsers.add_parser(
            "search",
            help="Search posts by text, author, tags, score, or date"
        )
        self._add_search_arguments(search_parser)

        # Report command
        report_parser = subparsers.add_parser(
            "report",
            help="Generate a report from posts"
        )
        self._add_search_arguments(report_parser)
        report_parser.add_argument(
            "--ids",
            help="Comma-separated list of post IDs to include in report"
        )
        report_parser.add_argument(
            "--format",
            choices=[f.value for f in ReportFormat],
            default="markdown",
            help="Output format (default: markdown)"
        )
        report_parser.add_argument(
            "--output",
            help="Output file path (default: print to stdout)"
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
                self.handle_list(category, parsed_args.no_ai_filter)
                return 0
            elif parsed_args.command == "categories":
                self.handle_categories()
                return 0
            elif parsed_args.command == "search":
                if not self.search_service:
                    print("Error: Search service not initialized.", file=sys.stderr)
                    return 1
                self.handle_search(parsed_args)
                return 0
            elif parsed_args.command == "report":
                if not self.report_service:
                    print("Error: Report service not initialized.", file=sys.stderr)
                    return 1
                self.handle_report(parsed_args)
                return 0
            else:
                print(f"Unknown command: {parsed_args.command}", file=sys.stderr)
                return 1
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _add_search_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add search arguments to an argument parser."""
        parser.add_argument(
            "--text", 
            help="Text to search in titles"
        )
        parser.add_argument(
            "--author", 
            help="Filter by author name"
        )
        parser.add_argument(
            "--tags", 
            help="Filter by tags (comma-separated, e.g. 'python,ai')"
        )
        parser.add_argument(
            "--min-score", 
            type=int,
            help="Minimum score"
        )
        parser.add_argument(
            "--max-score", 
            type=int,
            help="Maximum score"
        )
        parser.add_argument(
            "--start-date", 
            help="Start date (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--end-date", 
            help="End date (YYYY-MM-DD)"
        )
        parser.add_argument(
            "--order-by", 
            choices=["relevance", "date_desc", "date_asc", "score_desc", "score_asc"],
            default="relevance",
            help="Sort order (default: relevance)"
        )
        parser.add_argument(
            "--page", 
            type=int,
            default=1,
            help="Page number (default: 1)"
        )
        parser.add_argument(
            "--page_size", 
            type=int,
            default=20,
            help="Results per page (default: 20)"
        )
        parser.add_argument(
            "--list-tags",
            action="store_true",
            help="List all available tags"
        )
    
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
            print(f"\n[+] Fetch complete!")
            print(f"  New posts: {result.new_posts}")
            print(f"  Updated posts: {result.updated_posts}")
            
            if result.errors:
                print(f"\n[!] Encountered {len(result.errors)} errors:")
                for error in result.errors[:5]:  # Show first 5 errors
                    print(f"  - {error}")
                if len(result.errors) > 5:
                    print(f"  ... and {len(result.errors) - 5} more errors")
            
            if result.new_posts == 0 and result.updated_posts == 0:
                print("\nNo posts were fetched. Check the errors above for details.")
            
        except Exception as e:
            logger.error(f"Fetch operation failed: {e}")
            print(f"\n[!] Error: Failed to fetch posts - {e}", file=sys.stderr)
            raise
    
    def handle_list(self, category: Optional[Category], no_ai_filter: bool = False) -> None:
        """
        Handle the list command - display posts from the database.
        
        Args:
            category: Optional category filter
            no_ai_filter: If True, disable AI priority highlighting
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
            self.display_posts(posts, highlight_priority=not no_ai_filter)
            
        except Exception as e:
            logger.error(f"List operation failed: {e}")
            print(f"\n[!] Error: Failed to list posts - {e}", file=sys.stderr)
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
            print(f"\n[!] Error: Failed to retrieve category statistics - {e}", file=sys.stderr)
            raise

    def handle_search(self, args) -> None:
        """
        Handle the search command - execute search and display results.

        Args:
            args: Parsed command-line arguments
        """
        # Handle list-tags option
        if args.list_tags:
            self.display_available_tags()
            return

        try:
            query = self._build_search_query(args)

            # Execute search
            result = self.search_service.search_posts(query)

            # Display results
            self.display_search_results(result)

        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
        except Exception as e:
            logger.error(f"Search operation failed: {e}")
            print(f"Error: Failed to execute search - {e}", file=sys.stderr)

    def handle_report(self, args) -> None:
        """
        Handle the report command - generate and export reports.
        
        Args:
            args: Parsed command-line arguments
        """
        try:
            posts = []
            
            # 1. Fetch by IDs if provided
            if args.ids:
                ids = [int(i.strip()) for i in args.ids.split(",") if i.strip().isdigit()]
                for post_id in ids:
                    post = self.service.database.get_post_by_id(post_id)
                    if post:
                        posts.append(post)
            # 2. Fetch by search criteria if provided (and no IDs, or combined?)
            # Usually strict separation or combination is design choice. 
            # If IDs are provided, they usually take precedence or add to results.
            # Let's assume if IDs are NOT provided, we look at search args.
            elif self._has_search_criteria(args):
                # Build initial query
                query = self._build_search_query(args)
                
                # For reports, we want ALL results.
                # We fetch page by page until done.
                current_page = 1
                page_size = 100
                
                while True:
                    # Create query for current page
                    page_query = SearchQuery(
                        text=query.text, author=query.author, tags=query.tags, 
                        min_score=query.min_score, max_score=query.max_score,
                        start_date=query.start_date, end_date=query.end_date,
                        order_by=query.order_by,
                        page=current_page, 
                        page_size=page_size
                    )
                    
                    result = self.search_service.search_posts(page_query)
                    if not result.posts:
                        break
                        
                    posts.extend(result.posts)
                    
                    if not result.has_more_pages():
                        break
                        
                    current_page += 1
            
            if not posts:
                print("No posts found matching criteria for report.", file=sys.stderr)
                return

            # Generate report
            fmt = ReportFormat(args.format)
            report_content = self.report_service.generate_report(posts, fmt)
            
            # Output
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                print(f"Report generated: {args.output}")
            else:
                print(report_content)
                
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            print(f"Error: Failed to generate report - {e}", file=sys.stderr)

    def _has_search_criteria(self, args) -> bool:
        """Check if any search arguments are provided."""
        return any([
            args.text, args.author, args.tags, 
            args.min_score, args.max_score, 
            args.start_date, args.end_date
        ])

    def _build_search_query(self, args) -> SearchQuery:
        """Build a SearchQuery object from arguments."""
        # Parse dates if provided
        start_date = None
        if args.start_date:
            try:
                start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("start-date must be in YYYY-MM-DD format")

        end_date = None
        if args.end_date:
            try:
                end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("end-date must be in YYYY-MM-DD format")

        # Parse tags
        tags = None
        if args.tags:
            tags = [t.strip() for t in args.tags.split(",") if t.strip()]

        # Build query
        return SearchQuery(
            text=args.text,
            author=args.author,
            tags=tags,
            min_score=args.min_score,
            max_score=args.max_score,
            start_date=start_date,
            end_date=end_date,
            order_by=args.order_by,
            page=args.page,
            page_size=args.page_size
        )

    def display_available_tags(self) -> None:
        """Display all available tags in the system."""
        tags = self.search_service.get_available_tags()
        print("\nAvailable Tags:\n")
        
        # Print in columns
        col_width = 25
        num_cols = 3
        
        for i, tag in enumerate(tags):
            print(f"{tag:<{col_width}}", end="")
            if (i + 1) % num_cols == 0:
                print()
        print("\n")
    
    def display_posts(self, posts: List[Post], highlight_priority: bool = True) -> None:
        """
        Display a list of posts in a formatted table.
        
        Includes: title, author, score, date, category, and URL.
        Posts are displayed in descending order by creation date.
        
        Args:
            posts: List of Post objects to display
            highlight_priority: Whether to highlight priority AI terms (default: True)
        """
        if not posts:
            return
        
        # Prepare priority keywords if highlighting is enabled and service is available
        priority_keywords = []
        if highlight_priority and self.search_service:
            for tag in TagSystem.PRIORITY_TAGS:
                priority_keywords.extend(TagSystem.get_tag_keywords(tag))
        
        # Table formatting
        # Calculate column widths
        max_title_width = 80  # Increased for highlighted terms
        max_author_width = 15
        
        # Print table header
        print(f"{'Title':<{max_title_width}} {'Author':<{max_author_width}} {'Score':>6} {'Date':<12} {'Category':<8} {'URL'}")
        print("-" * (max_title_width + max_author_width + 6 + 12 + 8 + 50))
        
        # Print each post
        for post in posts:
            title = post.title
            
            # Apply priority highlighting
            if priority_keywords and self.search_service:
                title = self.search_service.highlight_terms(title, priority_keywords)
            
            # Truncate title if too long
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
    def display_search_results(self, result, highlight: bool = True) -> None:
        """
        Display search results in a formatted table with pagination info.

        Reuses the same table format as the list command for consistency.
        Optionally applies term highlighting to titles when text search is used.
        Shows pagination information and handles empty results gracefully.

        Args:
            result: SearchResult object containing posts and pagination metadata
            highlight: Whether to apply term highlighting (default: True)
        """
        # Handle empty results
        if not result.posts:
            print("\nNo posts found matching your search criteria.")
            if result.query.tags:
                print(f"Try using --list-tags to see available tags.")
            return

        # Display header with result count
        print(f"\nSearch Results ({result.total_results} total):\n")

        # Prepare posts for display with optional highlighting
        posts_to_display = result.posts

        # Apply highlighting if text search is present and highlighting is enabled
        if highlight and result.query.has_text_search():
            # Extract search terms from query text
            search_terms = result.query.text.split() if result.query.text else []

            # Highlight terms in each post title
            highlighted_posts = []
            for post in posts_to_display:
                # Create a copy of the post with highlighted title
                highlighted_title = self.search_service.highlight_terms(post.title, search_terms)
                # Create a new Post object with the highlighted title
                from dataclasses import replace
                highlighted_post = replace(post, title=highlighted_title)
                highlighted_posts.append(highlighted_post)

            posts_to_display = highlighted_posts

        # Display posts using the existing display_posts method
        self.display_posts(posts_to_display)

        # Display pagination information
        print()
        print(result.get_page_info())

        # Show navigation hints if there are multiple pages
        if result.total_pages > 1:
            hints = []
            if result.has_previous_page():
                hints.append(f"previous page: --page {result.page - 1}")
            if result.has_more_pages():
                hints.append(f"next page: --page {result.page + 1}")

            if hints:
                print(f"Navigation: {' | '.join(hints)}")

