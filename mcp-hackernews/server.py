import os
import sys
import logging
import webbrowser

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

@mcp.tool()
def get_ai_news(limit: int = 20) -> str:
    """Get the latest posts related to Artificial Intelligence (OpenAI, Anthropic, Gemini, AI, Agents, LLM, etc)."""
    db = init_db()
    api_client = HNApiClient(base_url=API_BASE_URL)
    service = HackerNewsService(api_client=api_client, database=db)
    
    # Obtener posts (por defecto trae recientes)
    posts = service.get_posts_by_category()
    db.close()
    
    if not posts:
        return "No posts found in database. Try running fetch_posts first."
        
    keywords = ["openai", "anthropic", "gemini", " ai ", "ai,", "artificial intelligence", "agent", "llm", "claude", "chatgpt"]
    
    ai_posts = []
    for p in posts:
        title_lower = p.title.lower()
        tags_str = str(p.tags).lower() if p.tags else ""
        text_str = str(p.text).lower() if hasattr(p, 'text') and p.text else ""
        
        # Checking if any keyword is in the text, title or tags
        if any(kw in title_lower for kw in keywords) or any(kw in tags_str for kw in keywords) or any(kw in text_str for kw in keywords):
            ai_posts.append(p)
            if len(ai_posts) >= limit:
                break
                
    if not ai_posts:
        return "No AI related posts found."
        
    output = [f"Found {len(ai_posts)} AI-related posts:"]
    for p in ai_posts:
        output.append(f"- [{p.score}] {p.title} (by {p.author})\n  URL: {p.url}")
        
    output.append("\n💡 Tip: Use the 'open_in_browser' tool passing the URL to read the full article.")
    return "\n".join(output)

@mcp.tool()
def open_in_browser(url: str) -> str:
    """Open a given URL in the default web browser of the host operating system."""
    try:
        success = webbrowser.open(url)
        if success:
            return f"Successfully opened the URL in the browser: {url}"
        else:
            return f"Failed to open the browser for URL: {url}"
    except Exception as e:
        return f"Error opening URL in browser: {str(e)}"

@mcp.tool()
def open_hn_comments(post_id: int) -> str:
    """Open the Hacker News comments page for a specific post in the host's web browser."""
    url = f"https://news.ycombinator.com/item?id={post_id}"
    try:
        success = webbrowser.open(url)
        if success:
            return f"Successfully opened the HN comments page for post {post_id}."
        else:
            return f"Failed to open the browser for post comments."
    except Exception as e:
        return f"Error opening URL in browser: {str(e)}"

@mcp.tool()
def get_post_details(post_id: int) -> str:
    """Get the full details of a specific post from the local database by its ID."""
    db = init_db()
    post = db.get_post_by_id(post_id)
    db.close()
    
    if not post:
        return f"Post with ID {post_id} not found in the local database."
        
    details = [f"--- Post {post_id} ---"]
    details.append(f"Title: {post.title}")
    details.append(f"Author: {post.author}")
    details.append(f"Score: {post.score}")
    details.append(f"URL: {post.url}")
    details.append(f"Category: {post.category.value if hasattr(post.category, 'value') else post.category}")
    details.append(f"Tags: {', '.join(post.tags) if post.tags else 'None'}")
    
    if hasattr(post, 'text') and post.text:
        details.append(f"Text:\n{post.text}")
        
    return "\n".join(details)

@mcp.tool()
def fetch_single_post(post_id: int) -> str:
    """Fetch a specific post directly from the Hacker News API by its ID and store it in the local database."""
    db = init_db()
    api_client = HNApiClient(base_url=API_BASE_URL)
    
    post = api_client.get_item(post_id)
    if not post:
        db.close()
        return f"Failed to fetch post {post_id} from HN API. It may be deleted or invalid."
        
    # Store it directly
    success = db.upsert_post(post)
    db.close()
    
    if success:
        return f"Successfully fetched and stored post {post_id}:\nTitle: {post.title}\nBy: {post.author}\nScore: {post.score}"
    else:
        return f"Fetched post {post_id} but failed to store it in the database."

def main():
    mcp.run()

if __name__ == "__main__":
    main()
