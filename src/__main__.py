"""Main entry point for Hackernews Report application."""

import sys
import logging

from src.config import DB_PATH, API_BASE_URL, LOG_LEVEL
from src.database import Database
from src.api_client import HNApiClient
from src.service import HackerNewsService
from src.search_engine import SearchEngine
from src.tags import TagSystem
from src.search_service import SearchService
from src.report_service import ReportService
from src.cli import CLI


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def main() -> int:
    """
    Main entry point for the application.
    
    Initializes all components and runs the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # Setup logging
        setup_logging(LOG_LEVEL)
        logger = logging.getLogger(__name__)
        
        logger.info("Starting Hackernews Report application")
        
        # Initialize database
        database = Database(db_path=DB_PATH)
        database.initialize_schema()
        logger.info(f"Database initialized at {DB_PATH}")
        
        # Initialize search components
        search_engine = SearchEngine(database=database)
        search_engine.create_search_indices()
        logger.info("Search indices created")
        
        tag_system = TagSystem()
        search_service = SearchService(search_engine=search_engine, tag_system=tag_system)
        logger.info("Search service initialized")
        
        # Initialize Report Service
        report_service = ReportService(search_service=search_service)
        logger.info("Report service initialized")
        
        # Initialize API client
        api_client = HNApiClient(base_url=API_BASE_URL)
        logger.info(f"API client initialized with base URL: {API_BASE_URL}")
        
        # Initialize service
        service = HackerNewsService(api_client=api_client, database=database)
        logger.info("Service layer initialized")
        
        # Initialize and run CLI
        cli = CLI(service=service, search_service=search_service, report_service=report_service)
        exit_code = cli.run(sys.argv[1:])
        
        # Cleanup
        database.close()
        logger.info("Application shutdown complete")
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user", file=sys.stderr)
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        # Catch any uncaught exceptions
        logger = logging.getLogger(__name__)
        logger.critical(f"Uncaught exception: {e}", exc_info=True)
        print(f"\nFatal error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
