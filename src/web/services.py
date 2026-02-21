from collections import Counter
from src.search_engine import SearchEngine
from src.search_service import SearchService
from src.report_service import ReportService
from src.tags import TagSystem
from src.service import HackerNewsService
from src.api_client import HNApiClient

def get_hn_service(db):
    """Get configured Hacker News service."""
    api_client = HNApiClient()
    return HackerNewsService(api_client=api_client, database=db)

def get_search_service(db):
    """Get configured search service."""
    search_engine = SearchEngine(database=db)
    # Ensure indices exist - this might be redundant to repeat on every request but cheap if they exist
    search_engine.create_search_indices()
    tag_system = TagSystem()
    return SearchService(search_engine=search_engine, tag_system=tag_system)

def get_report_service(db):
    """Get configured report service."""
    search_service = get_search_service(db)
    return ReportService(search_service=search_service)

def get_tag_statistics(posts):
    """
    Get statistics about tags from a list of posts.
    
    Args:
        posts: List of Post objects
        
    Returns:
        Dictionary mapping tag names to counts
    """
    tag_counter = Counter()
    for post in posts:
        for tag in post.tags:
            tag_counter[tag] += 1
    return dict(tag_counter.most_common())
