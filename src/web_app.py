"""Web UI for Hackernews Report application."""

from flask import Flask, render_template, request, jsonify
from src.database import Database
from src.models import Category
from src.config import DB_PATH
from src.tags import TagSystem
from datetime import datetime
from collections import Counter
import os


app = Flask(__name__, template_folder='../templates', static_folder='../static')


@app.template_filter('timestamp_to_date')
def timestamp_to_date(timestamp):
    """Convert Unix timestamp to readable date."""
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%B %d, %Y at %I:%M %p')
    except (ValueError, TypeError):
        return 'Unknown date'


def get_database():
    """Get database instance."""
    db_path = os.getenv('DB_PATH', DB_PATH)
    db = Database(db_path)
    return db


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


@app.route('/')
def index():
    """Main page showing all posts."""
    category_filter = request.args.get('category', None)
    tag_filter = request.args.get('tag', None)
    
    db = get_database()
    
    # Get posts
    if category_filter and category_filter != 'all':
        try:
            category = Category(category_filter)
            posts = db.get_posts_by_category(category=category, order_by='created_desc')
        except ValueError:
            posts = db.get_posts_by_category(order_by='created_desc')
    else:
        posts = db.get_posts_by_category(order_by='created_desc')
    
    # Filter by tag if specified
    if tag_filter:
        posts = [p for p in posts if tag_filter in p.tags]
    
    # Get category statistics
    stats = db.get_category_counts()
    
    # Get tag statistics
    tag_stats = get_tag_statistics(posts)
    
    # Get all available tags
    all_tags = TagSystem.get_all_tags()
    
    db.close()
    
    return render_template(
        'index.html',
        posts=posts,
        stats=stats,
        tag_stats=tag_stats,
        all_tags=all_tags,
        current_category=category_filter or 'all',
        current_tag=tag_filter
    )


@app.route('/api/posts')
def api_posts():
    """API endpoint to get posts as JSON."""
    category_filter = request.args.get('category', None)
    tag_filter = request.args.get('tag', None)
    limit = request.args.get('limit', 100, type=int)
    
    db = get_database()
    
    # Get posts
    if category_filter and category_filter != 'all':
        try:
            category = Category(category_filter)
            posts = db.get_posts_by_category(category=category, order_by='created_desc')
        except ValueError:
            posts = db.get_posts_by_category(order_by='created_desc')
    else:
        posts = db.get_posts_by_category(order_by='created_desc')
    
    # Filter by tag if specified
    if tag_filter:
        posts = [p for p in posts if tag_filter in p.tags]
    
    # Limit results
    posts = posts[:limit]
    
    db.close()
    
    # Convert to dict
    posts_data = [post.to_dict() for post in posts]
    
    return jsonify({
        'posts': posts_data,
        'count': len(posts_data)
    })


@app.route('/api/tags')
def api_tags():
    """API endpoint to get tag statistics."""
    db = get_database()
    posts = db.get_posts_by_category(order_by='created_desc')
    tag_stats = get_tag_statistics(posts)
    db.close()
    
    return jsonify(tag_stats)


@app.route('/api/stats')
def api_stats():
    """API endpoint to get category statistics."""
    db = get_database()
    stats = db.get_category_counts()
    db.close()
    
    return jsonify(stats)


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    """Detail page for a single post."""
    db = get_database()
    post = db.get_post_by_id(post_id)
    db.close()
    
    if post is None:
        return render_template('404.html'), 404
    
    return render_template('post_detail.html', post=post)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
