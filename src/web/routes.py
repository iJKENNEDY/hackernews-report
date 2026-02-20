from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, Response, current_app

from src.models import Category, SearchQuery
from src.tags import TagSystem
from src.report_service import ReportFormat

# Local imports
from .db import get_db
from .services import get_search_service, get_report_service, get_tag_statistics

bp = Blueprint('web', __name__)

@bp.route('/')
def index():
    """Main page showing all posts."""
    category_filter = request.args.get('category', None)
    tag_filter = request.args.get('tag', None)
    ai_filter = request.args.get('ai_filter', 'on')  # Default on
    selected_models = request.args.getlist('models')
    
    db = get_db()
    
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

    # Filter by selected AI models (if any)
    if selected_models:
        # build mapping model -> keywords
        model_kw_map = TagSystem.get_model_keyword_map()
        def matches_models(post):
            title = (post.title or '').lower()
            tags = [t.lower() for t in (post.tags or [])]
            for sel in selected_models:
                kws = model_kw_map.get(sel, [])
                for kw in kws:
                    if kw in title or any(kw in t for t in tags):
                        return True
            return False
        posts = [p for p in posts if matches_models(p)]
        
    # Apply AI Filter (Highlighting)
    if ai_filter == 'on':
        search_service = get_search_service(db)
        priority_keywords = []
        for tag in TagSystem.PRIORITY_TAGS:
            priority_keywords.extend(TagSystem.get_tag_keywords(tag))
            
        highlighted_posts = []
        for post in posts:
            new_title = search_service.highlight_terms(post.title, priority_keywords)
            # Create dict copy or use replace if it was dataclass, but db returns Post objects
            from dataclasses import replace
            highlighted_posts.append(replace(post, title=new_title))
        posts = highlighted_posts
    
    # Get category statistics
    stats = db.get_category_counts()
    
    # Get tag statistics
    tag_stats = get_tag_statistics(posts)
    
    # Get all available tags
    all_tags = TagSystem.get_all_tags()
    # AI model filter options and selected models for UI
    model_filter_options = TagSystem.get_model_filter_options()
    
    # render_template looks in configured template folder
    return render_template(
        'index.html',
        posts=posts,
        stats=stats,
        tag_stats=tag_stats,
        all_tags=all_tags,
        current_category=category_filter or 'all',
        current_tag=tag_filter,
        ai_filter=ai_filter
        , model_filter_options=model_filter_options, selected_models=selected_models
    )


@bp.route('/search')
def search():
    """Search results page."""
    query_text = request.args.get('q', '')
    tag_filter = request.args.get('tag', '')
    author_filter = request.args.get('author', '')
    ai_filter = request.args.get('ai_filter', 'on')
    selected_models = request.args.getlist('models')
    
    if not query_text and not tag_filter and not author_filter:
        return index()

    db = get_db()
    search_service = get_search_service(db)
    
    # Build search query
    tags = [tag_filter] if tag_filter else None
    
    try:
        search_query = SearchQuery(
            text=query_text,
            author=author_filter,
            tags=tags,
            page_size=50  # Larger page size for web UI
        )
        
        # Execute search
        result = search_service.search_posts(search_query)
        posts = result.posts
        # Filter by selected AI models (if any)
        if selected_models:
            model_kw_map = TagSystem.get_model_keyword_map()
            def matches_models(post):
                title = (post.title or '').lower()
                tags = [t.lower() for t in (post.tags or [])]
                for sel in selected_models:
                    kws = model_kw_map.get(sel, [])
                    for kw in kws:
                        if kw in title or any(kw in t for t in tags):
                            return True
                return False
            posts = [p for p in posts if matches_models(p)]
        
        # Apply highlighting for search terms (manual/pre-processing)
        if query_text:
            search_terms = query_text.split()
            # This is already done?? No, search_service.search returns posts. 
            # SearchEngine doesn't highlight. CLI does display logic highlights.
            # So we define highlighting here.
            highlighted_posts = []
            for post in posts:
                new_title = search_service.highlight_terms(post.title, search_terms)
                from dataclasses import replace
                highlighted_posts.append(replace(post, title=new_title))
            posts = highlighted_posts

        # Apply AI Filter Highlighting (on top of search highlights?)
        if ai_filter == 'on':
            priority_keywords = []
            for tag in TagSystem.PRIORITY_TAGS:
                 priority_keywords.extend(TagSystem.get_tag_keywords(tag))
            
            highlighted_posts_2 = []
            for post in posts:
                # highlight_terms handles existing ** markers nicely
                new_title = search_service.highlight_terms(post.title, priority_keywords)
                from dataclasses import replace
                highlighted_posts_2.append(replace(post, title=new_title))
            posts = highlighted_posts_2

    except ValueError as e:
        posts = []
        # TODO: flash error
    
    # Get stats for sidebar
    stats = db.get_category_counts()
    # Tag stats from search results
    tag_stats = get_tag_statistics(posts)
    all_tags = TagSystem.get_all_tags()
    
    return render_template(
        'index.html',
        posts=posts,
        stats=stats,
        tag_stats=tag_stats,
        all_tags=all_tags,
        current_category='search',
        search_query=query_text,
        current_tag=tag_filter,
        ai_filter=ai_filter
        , model_filter_options=TagSystem.get_model_filter_options(), selected_models=selected_models
    )


@bp.route('/report')
def generate_report():
    """Generate and download a report based on current filters."""
    query_text = request.args.get('q', '')
    tag_filter = request.args.get('tag', '')
    author_filter = request.args.get('author', '')
    category_filter = request.args.get('category', '')
    output_format_str = request.args.get('format', 'markdown')
    
    try:
        output_format = ReportFormat(output_format_str)
    except ValueError:
        return "Invalid format", 400
        
    db = get_db()
    
    # Determine how to fetch posts (Reuse logic from index/search)
    if query_text or author_filter:
        # Search mode
        search_service = get_search_service(db)
        tags = [tag_filter] if tag_filter else None
        
        try:
            search_query = SearchQuery(
                text=query_text,
                author=author_filter,
                tags=tags,
                page_size=1000  # Fetch many for report
            )
            result = search_service.search_posts(search_query)
            posts = result.posts
        except ValueError:
            posts = []
    else:
        # Browse mode
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
            
    # Generate Report
    report_service = get_report_service(db)
    report_content = report_service.generate_report(posts, output_format)
    
    # Set correct MIME type and filename
    mime_types = {
        ReportFormat.MARKDOWN: 'text/markdown',
        ReportFormat.HTML: 'text/html',
        ReportFormat.CSV: 'text/csv',
        ReportFormat.TXT: 'text/plain',
        ReportFormat.JSON: 'application/json'
    }
    
    extensions = {
        ReportFormat.MARKDOWN: 'md',
        ReportFormat.HTML: 'html',
        ReportFormat.CSV: 'csv',
        ReportFormat.TXT: 'txt',
        ReportFormat.JSON: 'json'
    }
    
    mime_type = mime_types.get(output_format, 'text/plain')
    ext = extensions.get(output_format, 'txt')
    filename = f"hackernews_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    
    return Response(
        report_content,
        mimetype=mime_type,
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


@bp.route('/api/posts')
def api_posts():
    """API endpoint to get posts as JSON."""
    category_filter = request.args.get('category', None)
    tag_filter = request.args.get('tag', None)
    limit = request.args.get('limit', 100, type=int)
    
    db = get_db()
    
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
    
    # Convert to dict
    posts_data = [post.to_dict() for post in posts]
    
    return jsonify({
        'posts': posts_data,
        'count': len(posts_data)
    })


@bp.route('/api/tags')
def api_tags():
    """API endpoint to get tag statistics."""
    db = get_db()
    posts = db.get_posts_by_category(order_by='created_desc')
    tag_stats = get_tag_statistics(posts)
    
    return jsonify(tag_stats)


@bp.route('/api/stats')
def api_stats():
    """API endpoint to get category statistics."""
    db = get_db()
    stats = db.get_category_counts()
    
    return jsonify(stats)


@bp.route('/post/<int:post_id>')
def post_detail(post_id):
    """Detail page for a single post."""
    db = get_db()
    post = db.get_post_by_id(post_id)
    
    if post is None:
        return render_template('404.html'), 404
    
    return render_template('post_detail.html', post=post)
