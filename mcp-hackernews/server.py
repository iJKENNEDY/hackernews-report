import os
import sys
import logging

# Add parent directory to sys.path so we can import 'src' module
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from typing import Optional

from mcp.server.fastmcp import FastMCP

from src.config import DB_PATH, API_BASE_URL
from src.database import Database
from src.api_client import HNApiClient
from src.service import HackerNewsService
from src.search_engine import SearchEngine
from src.tags import TagSystem
from src.search_service import SearchService
from src.models import Category, SearchQuery

# Initialize FastMCP Server
mcp = FastMCP("Hackernews Report MCP")

def init_db():
    db_file = os.path.join(project_root, DB_PATH) if not os.path.isabs(DB_PATH) else DB_PATH
    db = Database(db_path=db_file)
    db.initialize_schema()
    return db

def init_search_service(db):
    tag_system = TagSystem()
    search_engine = SearchEngine(database=db)
    search_engine.create_search_indices()
    return SearchService(search_engine=search_engine, tag_system=tag_system)

@mcp.tool()
def fetch_posts(limit: int = 30) -> str:
    """Fetch new posts from Hacker News API."""
    db = init_db()
    api_client = HNApiClient(base_url=API_BASE_URL)
    service = HackerNewsService(api_client=api_client, database=db)
    result = service.fetch_and_store_posts(limit=limit)
    
    db.close()
    
    if result.errors:
        error_msg = "\n".join(result.errors[:5])
        return f"Fetch completed with some errors.\nNew: {result.new_posts}, Updated: {result.updated_posts}\nErrors:\n{error_msg}"
        
    return f"Fetch complete. Retrieved {result.new_posts} new posts and updated {result.updated_posts} posts."

@mcp.tool()
def list_posts(category: str = None) -> str:
    """List posts from the local database. Optionally filter by category (story, job, ask, poll, other)."""
    db = init_db()
    api_client = HNApiClient(base_url=API_BASE_URL)
    service = HackerNewsService(api_client=api_client, database=db)
    
    cat_enum = None
    if category:
        try:
            cat_enum = Category(category)
        except ValueError:
            db.close()
            return "Invalid category. Must be one of: [story, job, ask, poll, other]"
            
    posts = service.get_posts_by_category(category=cat_enum)
    db.close()
    
    if not posts:
        return "No posts found. Try running fetch_posts first."
        
    output = [f"Found {len(posts)} posts:"]
    for p in posts[:20]: # limit to prevent huge payload
        output.append(f"- [{p.score}] {p.title} by {p.author} ({p.url})")
        
    if len(posts) > 20:
        output.append(f"... and {len(posts) - 20} more.")
        
    return "\n".join(output)

@mcp.tool()
def get_categories() -> str:
    """Get the statistics for each post category stored in the database."""
    db = init_db()
    api_client = HNApiClient(base_url=API_BASE_URL)
    service = HackerNewsService(api_client=api_client, database=db)
    stats = service.get_category_statistics()
    
    db.close()
    
    if not stats:
        return "No posts found in database."
        
    output = ["Category Statistics:"]
    for cat, count in stats.items():
        output.append(f"- {cat}: {count}")
    return "\n".join(output)

@mcp.tool()
def search_posts(text: str = None, author: str = None, tags: str = None) -> str:
    """Search stored posts by text, author, or tags (comma-separated)."""
    db = init_db()
    search_service = init_search_service(db)
    
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    
    query = SearchQuery(
        text=text,
        author=author,
        tags=tag_list,
        page_size=20
    )
    
    result = search_service.search_posts(query)
    db.close()
    
    if not result.posts:
        return "No results found."
        
    output = [f"Found {result.total_results} results:"]
    for p in result.posts:
        output.append(f"- [{p.score}] {p.title} by {p.author} ({p.url})")
    
    return "\n".join(output)

@mcp.tool()
def get_available_tags() -> str:
    """List all available tags for searching."""
    db = init_db()
    search_service = init_search_service(db)
    tags = search_service.get_available_tags()
    db.close()
    
    if not tags:
        return "No tags found."
    return "Available tags:\n" + ", ".join(tags)

def main():
    mcp.run()

if __name__ == "__main__":
    main()
