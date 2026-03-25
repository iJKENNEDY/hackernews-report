import math
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, Response, current_app

from src.models import Category, SearchQuery, Post
from src.tags import TagSystem
from src.report_service import ReportFormat
from src.favorites import FavoritesManager
from src.personal_posts import PersonalPostsManager

# Local imports
from .db import get_db
from .services import get_search_service, get_report_service, get_tag_statistics, get_hn_service

bp = Blueprint('web', __name__)

POSTS_PER_PAGE = 20
PER_PAGE_OPTIONS = (20, 50, 100)


def _normalize_per_page(raw_value: int) -> int:
    """Normalize pagination size to supported efficient options."""
    try:
        val = int(raw_value)
    except (TypeError, ValueError):
        return POSTS_PER_PAGE
    if val in PER_PAGE_OPTIONS:
        return val
    return POSTS_PER_PAGE


def _personal_to_search_post(personal_post, fallback_search_text: str = ""):
    """Convert PersonalPost to Post-like object for unified search UI rendering."""
    lower_blob = " ".join([
        personal_post.title or "",
        personal_post.description or "",
        personal_post.url or "",
        " ".join(personal_post.tags or []),
    ]).lower()
    guessed_category = Category.OTHER
    if any(k in lower_blob for k in ("ask", "question", "pregunta")):
        guessed_category = Category.ASK
    elif any(k in lower_blob for k in ("job", "hiring", "vacante")):
        guessed_category = Category.JOB

    # Offset id to avoid collisions with HN ids in mixed search results.
    synthetic_id = 1_000_000_000 + int(personal_post.id)

    return Post(
        id=synthetic_id,
        title=personal_post.title,
        author="personal",
        score=0,
        url=personal_post.url or "/personal",
        created_at=personal_post.date_added,
        type="personal",
        category=guessed_category,
        fetched_at=personal_post.updated_at,
        tags=personal_post.tags or [],
    )


def _get_favorites_manager():
    """Get a FavoritesManager using the same DB path as the main database."""
    from flask import g
    if 'fav_mgr' not in g:
        from src.config import DB_PATH
        import os
        db_path = os.getenv('DB_PATH', DB_PATH)
        g.fav_mgr = FavoritesManager(db_path)
    return g.fav_mgr


@bp.teardown_app_request
def _close_fav_mgr(exc=None):
    from flask import g
    mgr = g.pop('fav_mgr', None)
    if mgr is not None:
        mgr.close()


@bp.route('/')
def index():
    """Main page showing all posts."""
    category_filter = request.args.get('category', None)
    tag_filter = request.args.get('tag', None)
    ai_filter = request.args.get('ai_filter', 'on')  # Default on
    pdf_filter = request.args.get('pdf_filter', 'off')  # Default off
    selected_models = request.args.getlist('models')
    page = request.args.get('page', 1, type=int)
    per_page = _normalize_per_page(request.args.get('per_page', POSTS_PER_PAGE, type=int))
    
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

    # Filter by PDF URLs
    if pdf_filter == 'on':
        posts = [p for p in posts if p.url and p.url.lower().endswith('.pdf')]
        
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
    
    # Pagination
    total_posts = len(posts)
    total_pages = max(1, math.ceil(total_posts / per_page))
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_posts = posts[start:end]
    
    # Get category statistics
    stats = db.get_category_counts()
    
    # Get tag statistics
    tag_stats = get_tag_statistics(posts)
    
    # Get all available tags
    all_tags = TagSystem.get_all_tags()
    # AI model filter options and selected models for UI
    model_filter_options = TagSystem.get_model_filter_options()

    # Get favorites info for sidebar
    fav_mgr = _get_favorites_manager()
    favorite_ids = set(fav_mgr.get_all_favorite_post_ids())
    fav_groups = fav_mgr.get_groups()
    fav_default_count = fav_mgr.get_default_count()
    fav_total_count = fav_mgr.get_total_count()
    
    # render_template looks in configured template folder
    return render_template(
        'index.html',
        posts=paginated_posts,
        stats=stats,
        tag_stats=tag_stats,
        all_tags=all_tags,
        current_category=category_filter or 'all',
        current_tag=tag_filter,
        ai_filter=ai_filter,
        pdf_filter=pdf_filter,
        model_filter_options=model_filter_options,
        selected_models=selected_models,
        page=page,
        total_pages=total_pages,
        total_posts=total_posts,
        per_page=per_page,
        per_page_options=PER_PAGE_OPTIONS,
        favorite_ids=favorite_ids,
        fav_groups=fav_groups,
        fav_default_count=fav_default_count,
        fav_total_count=fav_total_count,
    )


@bp.route('/favorites')
def favorites_page():
    """Page showing favorite posts, optionally filtered by group."""
    group_id = request.args.get('group', None, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = _normalize_per_page(request.args.get('per_page', POSTS_PER_PAGE, type=int))

    db = get_db()
    fav_mgr = _get_favorites_manager()

    # Get favorite post IDs for this group
    if group_id is not None:
        fav_post_ids = fav_mgr.get_favorite_post_ids(group_id)
    else:
        fav_post_ids = fav_mgr.get_favorite_post_ids()  # all

    # Fetch actual post objects
    posts = []
    for pid in fav_post_ids:
        post = db.get_post_by_id(pid)
        if post:
            posts.append(post)

    # Pagination
    total_posts = len(posts)
    total_pages = max(1, math.ceil(total_posts / per_page))
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_posts = posts[start:end]

    # Sidebar data
    stats = db.get_category_counts()
    tag_stats = get_tag_statistics(posts)
    all_tags = TagSystem.get_all_tags()
    model_filter_options = TagSystem.get_model_filter_options()

    favorite_ids = set(fav_mgr.get_all_favorite_post_ids())
    fav_groups = fav_mgr.get_groups()
    fav_default_count = fav_mgr.get_default_count()
    fav_total_count = fav_mgr.get_total_count()

    # Determine current group name for header
    current_group_name = "Todos los Favoritos"
    if group_id == 0:
        current_group_name = "⭐ Favoritos (General)"
    elif group_id is not None:
        grp = fav_mgr.get_group_by_id(group_id)
        if grp:
            current_group_name = f"{grp.emoji} {grp.name}"

    return render_template(
        'index.html',
        posts=paginated_posts,
        stats=stats,
        tag_stats=tag_stats,
        all_tags=all_tags,
        current_category='favorites',
        current_tag=None,
        ai_filter='off',
        pdf_filter='off',
        model_filter_options=model_filter_options,
        selected_models=[],
        page=page,
        total_pages=total_pages,
        total_posts=total_posts,
        per_page=per_page,
        per_page_options=PER_PAGE_OPTIONS,
        favorite_ids=favorite_ids,
        fav_groups=fav_groups,
        fav_default_count=fav_default_count,
        fav_total_count=fav_total_count,
        fav_current_group=group_id,
        fav_current_group_name=current_group_name,
    )


@bp.route('/refresh')
def refresh():
    """Refresh posts from Hacker News."""
    db = get_db()
    hn_service = get_hn_service(db)
    
    # Fetch top 50 posts (can be adjusted)
    result = hn_service.fetch_and_store_posts(limit=50)
    
    return jsonify({
        'status': 'success',
        'new_posts': result.new_posts,
        'updated_posts': result.updated_posts,
        'errors': result.errors
    })


@bp.route('/search')
def search():
    """Search results page."""
    query_text = request.args.get('q', '')
    tag_filter = request.args.get('tag', '')
    author_filter = request.args.get('author', '')
    ai_filter = request.args.get('ai_filter', 'on')
    pdf_filter = request.args.get('pdf_filter', 'off')
    selected_models = request.args.getlist('models')
    page = request.args.get('page', 1, type=int)
    per_page = _normalize_per_page(request.args.get('per_page', POSTS_PER_PAGE, type=int))
    
    if not query_text and not tag_filter and not author_filter:
        return index()

    db = get_db()
    search_service = get_search_service(db)
    personal_mgr = _get_personal_manager()
    
    # Build search query
    tags = [tag_filter] if tag_filter else None
    
    try:
        search_query = SearchQuery(
            text=query_text,
            author=author_filter,
            tags=tags,
            page_size=100  # Must respect SearchQuery validation (<= 100)
        )
        
        # Execute search (HN posts)
        result = search_service.search_posts(search_query)
        posts = result.posts

        # Include personal posts in global search results
        personal_posts = personal_mgr.get_posts(tag=tag_filter or None)
        q_text = (query_text or '').strip().lower()
        a_text = (author_filter or '').strip().lower()

        def matches_personal(pp):
            if a_text and a_text not in (pp.source or '').lower():
                return False
            if q_text:
                haystack = " ".join([
                    pp.title or '',
                    pp.description or '',
                    pp.url or '',
                    ' '.join(pp.tags or []),
                    pp.source or '',
                ]).lower()
                return q_text in haystack
            return True

        matched_personal = [pp for pp in personal_posts if matches_personal(pp)]
        posts.extend([_personal_to_search_post(pp, query_text) for pp in matched_personal])
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

        # Filter by PDF URLs
        if pdf_filter == 'on':
            posts = [p for p in posts if p.url and p.url.lower().endswith('.pdf')]
        
        # Apply highlighting for search terms (manual/pre-processing)
        if query_text:
            search_terms = query_text.split()
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

        # Keep newest first in mixed results
        posts.sort(key=lambda p: p.created_at, reverse=True)

    except ValueError as e:
        posts = []
        # TODO: flash error
    
    # Pagination
    total_posts = len(posts)
    total_pages = max(1, math.ceil(total_posts / per_page))
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_posts = posts[start:end]
    
    # Get stats for sidebar
    stats = db.get_category_counts()
    # Tag stats from search results
    tag_stats = get_tag_statistics(posts)
    all_tags = TagSystem.get_all_tags()

    # Favorites info
    fav_mgr = _get_favorites_manager()
    favorite_ids = set(fav_mgr.get_all_favorite_post_ids())
    fav_groups = fav_mgr.get_groups()
    fav_default_count = fav_mgr.get_default_count()
    fav_total_count = fav_mgr.get_total_count()
    
    return render_template(
        'index.html',
        posts=paginated_posts,
        stats=stats,
        tag_stats=tag_stats,
        all_tags=all_tags,
        current_category='search',
        search_query=query_text,
        current_tag=tag_filter,
        ai_filter=ai_filter,
        pdf_filter=pdf_filter,
        model_filter_options=TagSystem.get_model_filter_options(),
        selected_models=selected_models,
        page=page,
        total_pages=total_pages,
        total_posts=total_posts,
        per_page=per_page,
        per_page_options=PER_PAGE_OPTIONS,
        favorite_ids=favorite_ids,
        fav_groups=fav_groups,
        fav_default_count=fav_default_count,
        fav_total_count=fav_total_count,
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
                page_size=100  # Must respect SearchQuery validation (<= 100)
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


# ──────────── Favorites API ────────────

@bp.route('/api/favorites/toggle', methods=['POST'])
def api_toggle_favorite():
    """Toggle a post as favorite (add/remove from default group)."""
    data = request.get_json()
    if not data or 'post_id' not in data:
        return jsonify({'error': 'post_id required'}), 400

    post_id = int(data['post_id'])
    group_id = int(data.get('group_id', 0))

    fav_mgr = _get_favorites_manager()

    if fav_mgr.is_favorite(post_id, group_id):
        fav_mgr.remove_favorite(post_id, group_id)
        return jsonify({
            'status': 'removed',
            'post_id': post_id,
            'group_id': group_id,
            'is_favorite': False,
            'default_count': fav_mgr.get_default_count(),
            'total_count': fav_mgr.get_total_count(),
        })
    else:
        fav_mgr.add_favorite(post_id, group_id)
        return jsonify({
            'status': 'added',
            'post_id': post_id,
            'group_id': group_id,
            'is_favorite': True,
            'default_count': fav_mgr.get_default_count(),
            'total_count': fav_mgr.get_total_count(),
        })


@bp.route('/api/favorites/add-to-group', methods=['POST'])
def api_add_to_group():
    """Add a post to a specific group."""
    data = request.get_json()
    if not data or 'post_id' not in data or 'group_id' not in data:
        return jsonify({'error': 'post_id and group_id required'}), 400

    post_id = int(data['post_id'])
    group_id = int(data['group_id'])

    fav_mgr = _get_favorites_manager()
    fav_mgr.add_favorite(post_id, group_id)

    return jsonify({
        'status': 'added',
        'post_id': post_id,
        'group_id': group_id,
        'post_groups': fav_mgr.get_post_groups(post_id),
    })


@bp.route('/api/favorites/remove', methods=['POST'])
def api_remove_favorite():
    """Remove a post from all groups."""
    data = request.get_json()
    if not data or 'post_id' not in data:
        return jsonify({'error': 'post_id required'}), 400

    post_id = int(data['post_id'])
    fav_mgr = _get_favorites_manager()
    removed = fav_mgr.remove_favorite_from_all(post_id)

    return jsonify({
        'status': 'removed',
        'post_id': post_id,
        'removed_count': removed,
        'default_count': fav_mgr.get_default_count(),
        'total_count': fav_mgr.get_total_count(),
    })


@bp.route('/api/favorites/list')
def api_favorites_list():
    """Get all favorite post IDs, optionally by group."""
    group_id = request.args.get('group_id', None, type=int)
    fav_mgr = _get_favorites_manager()

    if group_id is not None:
        post_ids = fav_mgr.get_favorite_post_ids(group_id)
    else:
        post_ids = fav_mgr.get_all_favorite_post_ids()

    return jsonify({
        'post_ids': post_ids,
        'count': len(post_ids),
        'default_count': fav_mgr.get_default_count(),
        'total_count': fav_mgr.get_total_count(),
    })


@bp.route('/api/favorites/post-groups/<int:post_id>')
def api_post_groups(post_id):
    """Get all groups that contain a given post."""
    fav_mgr = _get_favorites_manager()
    groups = fav_mgr.get_post_groups(post_id)
    return jsonify({'post_id': post_id, 'group_ids': groups})


# ──────────── Groups API ────────────

@bp.route('/api/groups', methods=['GET'])
def api_get_groups():
    """Get all favorite groups."""
    fav_mgr = _get_favorites_manager()
    groups = fav_mgr.get_groups()
    return jsonify({
        'groups': [g.to_dict() for g in groups],
        'default_count': fav_mgr.get_default_count(),
    })


@bp.route('/api/groups', methods=['POST'])
def api_create_group():
    """Create a new favorite group."""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'name required'}), 400

    name = data['name']
    emoji = data.get('emoji', '📁')
    color = data.get('color', '#ff6600')
    parent_id = data.get('parent_id')
    if parent_id == '':
        parent_id = None
    if parent_id is not None:
        parent_id = int(parent_id)

    fav_mgr = _get_favorites_manager()
    try:
        group = fav_mgr.create_group(name, emoji, color, parent_id=parent_id)
        return jsonify({'status': 'created', 'group': group.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/api/groups/<int:group_id>', methods=['PUT'])
def api_update_group(group_id):
    """Update a group."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    fav_mgr = _get_favorites_manager()
    try:
        parent_id = data.get('parent_id', -1)
        if parent_id == '':
            parent_id = None
        elif parent_id != -1 and parent_id is not None:
            parent_id = int(parent_id)

        fav_mgr.update_group(
            group_id,
            name=data.get('name'),
            emoji=data.get('emoji'),
            color=data.get('color'),
            parent_id=parent_id
        )
        group = fav_mgr.get_group_by_id(group_id)
        return jsonify({'status': 'updated', 'group': group.to_dict() if group else None})
    except ValueError as e:
        return jsonify({'error': str(e)}), 409


@bp.route('/api/groups/<int:group_id>', methods=['DELETE'])
def api_delete_group(group_id):
    """Delete a group and its favorites."""
    fav_mgr = _get_favorites_manager()
    deleted = fav_mgr.delete_group(group_id)

    if deleted:
        return jsonify({'status': 'deleted', 'group_id': group_id})
    else:
        return jsonify({'error': 'Group not found'}), 404


from src.utils.pdf_service import merge_pdfs
import os
import tempfile
import requests


# ──────────── PDF Merging API ────────────

@bp.route('/api/pdf/merge', methods=['POST'])
def api_pdf_merge():
    """Merge multiple PDFs from URLs and return the result."""
    data = request.get_json()
    if not data or 'urls' not in data or len(data['urls']) < 2:
        return jsonify({'error': 'Al menos 2 URLs de PDF son requeridas'}), 400

    urls = data['urls']
    temp_files = []
    
    try:
        # Download PDFs to temporary files
        for url in urls:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                return jsonify({'error': f'Error al descargar {url}'}), 400
            
            temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_pdf.write(response.content)
            temp_pdf.close()
            temp_files.append(temp_pdf.name)
        
        # Merge them
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf').name
        if merge_pdfs(temp_files, output_path):
            with open(output_path, 'rb') as f:
                merged_content = f.read()
            
            # Clean up
            os.remove(output_path)
            for tf in temp_files:
                os.remove(tf)
                
            return Response(
                merged_content,
                mimetype='application/pdf',
                headers={"Content-disposition": "attachment; filename=merged_hn_reports.pdf"}
            )
        else:
            return jsonify({'error': 'Error al procesar la unión de PDFs'}), 500
            
    except Exception as e:
        # Cleanup on error
        for tf in temp_files:
            if os.path.exists(tf): os.remove(tf)
        return jsonify({'error': str(e)}), 500


# ──────────── Personal Posts ────────────

def _get_personal_manager() -> PersonalPostsManager:
    """Get (or create) a PersonalPostsManager stored on Flask g."""
    from flask import g
    if 'personal_mgr' not in g:
        from src.config import DB_PATH
        import os
        db_path = os.getenv('DB_PATH', DB_PATH)
        g.personal_mgr = PersonalPostsManager(db_path)
        g.personal_mgr.initialize_schema()
    return g.personal_mgr


@bp.teardown_app_request
def _close_personal_mgr(exc=None):
    from flask import g
    mgr = g.pop('personal_mgr', None)
    if mgr is not None:
        mgr.close()


@bp.route('/personal')
def personal_posts_page():
    """Page for personal posts management."""
    mgr = _get_personal_manager()
    fav_mgr = _get_favorites_manager()
    db = get_db()

    category_id = request.args.get('category_id', None, type=int)
    tag_filter = request.args.get('tag', None)

    posts = mgr.get_posts(category_id=category_id, tag=tag_filter)
    categories_tree = mgr.get_categories_tree()
    categories_flat = mgr.get_categories_flat()
    all_tags = mgr.get_all_tags()

    # Sidebar data shared with the base template
    stats = db.get_category_counts()
    fav_groups = fav_mgr.get_groups()
    fav_default_count = fav_mgr.get_default_count()
    fav_total_count = fav_mgr.get_total_count()
    favorite_ids = set(fav_mgr.get_all_favorite_post_ids())
    all_hn_tags = TagSystem.get_all_tags()
    model_filter_options = TagSystem.get_model_filter_options()

    return render_template(
        'personal_posts.html',
        personal_posts=posts,
        categories_tree=categories_tree,
        categories_flat=categories_flat,
        all_tags=all_tags,
        current_category_id=category_id,
        current_tag=tag_filter,
        # Shared sidebar
        stats=stats,
        fav_groups=fav_groups,
        fav_default_count=fav_default_count,
        fav_total_count=fav_total_count,
        favorite_ids=favorite_ids,
        all_hn_tags=all_hn_tags,
        model_filter_options=model_filter_options,
        current_category='personal',
        ai_filter='off',
        pdf_filter='off',
        selected_models=[],
    )


# ── Personal Posts API ──────────────────

@bp.route('/api/personal/posts', methods=['GET'])
def api_personal_posts_list():
    mgr = _get_personal_manager()
    category_id = request.args.get('category_id', None, type=int)
    tag = request.args.get('tag', None)
    source = request.args.get('source', None)
    posts = mgr.get_posts(category_id=category_id, tag=tag, source=source)
    return jsonify({'posts': [p.to_dict() for p in posts], 'count': len(posts)})


@bp.route('/api/personal/posts', methods=['POST'])
def api_personal_posts_create():
    data = request.get_json()
    if not data or not data.get('title', '').strip():
        return jsonify({'error': 'title is required'}), 400
    mgr = _get_personal_manager()
    tags = [t.strip() for t in data.get('tags', '').split(',') if t.strip()]
    post = mgr.create_post(
        title=data['title'],
        url=data.get('url') or None,
        category_id=data.get('category_id') or None,
        tags=tags,
        description=data.get('description', ''),
        source=data.get('source', 'personal'),
    )
    return jsonify({'status': 'created', 'post': post.to_dict()}), 201


@bp.route('/api/personal/posts/<int:post_id>', methods=['PUT'])
def api_personal_posts_update(post_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    mgr = _get_personal_manager()
    tags = None
    if 'tags' in data:
        tags = [t.strip() for t in data['tags'].split(',') if t.strip()]
    ok = mgr.update_post(
        post_id,
        title=data.get('title'),
        url=data.get('url'),
        category_id=data.get('category_id'),
        tags=tags,
        description=data.get('description'),
        source=data.get('source'),
    )
    if not ok:
        return jsonify({'error': 'Post not found'}), 404
    post = mgr.get_post_by_id(post_id)
    return jsonify({'status': 'updated', 'post': post.to_dict()})


@bp.route('/api/personal/posts/<int:post_id>', methods=['DELETE'])
def api_personal_posts_delete(post_id):
    mgr = _get_personal_manager()
    if mgr.delete_post(post_id):
        return jsonify({'status': 'deleted', 'post_id': post_id})
    return jsonify({'error': 'Post not found'}), 404


# ── Personal Categories API ─────────────

@bp.route('/api/personal/categories', methods=['GET'])
def api_personal_categories_list():
    mgr = _get_personal_manager()
    tree = mgr.get_categories_tree()
    return jsonify({'categories': [c.to_dict() for c in tree]})


@bp.route('/api/personal/categories', methods=['POST'])
def api_personal_categories_create():
    data = request.get_json()
    if not data or not data.get('name', '').strip():
        return jsonify({'error': 'name is required'}), 400
    mgr = _get_personal_manager()
    cat = mgr.create_category(
        name=data['name'],
        emoji=data.get('emoji', '📁'),
        color=data.get('color', '#ff6600'),
        parent_id=data.get('parent_id') or None,
    )
    return jsonify({'status': 'created', 'category': cat.to_dict()}), 201


@bp.route('/api/personal/categories/<int:cat_id>', methods=['PUT'])
def api_personal_categories_update(cat_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    mgr = _get_personal_manager()
    ok = mgr.update_category(
        cat_id,
        name=data.get('name'),
        emoji=data.get('emoji'),
        color=data.get('color'),
        parent_id=data.get('parent_id'),
    )
    if not ok:
        return jsonify({'error': 'Category not found'}), 404
    cat = mgr.get_category_by_id(cat_id)
    return jsonify({'status': 'updated', 'category': cat.to_dict() if cat else None})


@bp.route('/api/personal/categories/<int:cat_id>', methods=['DELETE'])
def api_personal_categories_delete(cat_id):
    mgr = _get_personal_manager()
    if mgr.delete_category(cat_id):
        return jsonify({'status': 'deleted', 'category_id': cat_id})
    return jsonify({'error': 'Category not found'}), 404
