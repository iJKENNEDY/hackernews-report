"""Report generation service."""

import csv
import io
import json
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter

from src.models import Post
from src.tags import TagSystem
from src.search_service import SearchService


class ReportFormat(Enum):
    """Supported report formats."""
    MARKDOWN = "markdown"
    HTML = "html"
    CSV = "csv"
    TXT = "txt"
    JSON = "json"


class ReportService:
    """
    Service for generating reports from a list of posts.
    
    Supports multiple output formats and includes summary statistics.
    Integrates with SearchService for highlighting.
    """
    
    def __init__(self, search_service: Optional[SearchService] = None):
        """
        Initialize the ReportService.
        
        Args:
            search_service: Optional SearchService for highlighting terms.
        """
        self.search_service = search_service

    def generate_report(self, posts: List[Post], output_format: ReportFormat, title: str = "Hacker News Report") -> str:
        """
        Generate a report for the given posts in the specified format.
        
        Args:
            posts: List of posts to include in the report.
            output_format: The format to generate the report in.
            title: Title of the report.
            
        Returns:
            The report content as a string.
        """
        if not posts:
            return "No posts to report."

        stats = self._calculate_statistics(posts)
        
        if output_format == ReportFormat.MARKDOWN:
            return self._generate_markdown(posts, stats, title)
        elif output_format == ReportFormat.HTML:
            return self._generate_html(posts, stats, title)
        elif output_format == ReportFormat.CSV:
            return self._generate_csv(posts)
        elif output_format == ReportFormat.TXT:
            return self._generate_txt(posts, stats, title)
        elif output_format == ReportFormat.JSON:
            return self._generate_json(posts, stats, title)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _calculate_statistics(self, posts: List[Post]) -> Dict[str, Any]:
        """Calculate summary statistics for the posts."""
        total_posts = len(posts)
        total_score = sum(p.score for p in posts)
        avg_score = total_score / total_posts if total_posts > 0 else 0
        
        # Tag statistics
        tag_counter = Counter()
        for post in posts:
            for tag in post.tags:
                tag_counter[tag] += 1
        
        # Category statistics
        category_counter = Counter(p.category.value for p in posts)
        
        # Top authors
        author_counter = Counter(p.author for p in posts)
        
        return {
            "total_posts": total_posts,
            "total_score": total_score,
            "avg_score": avg_score,
            "top_tags": tag_counter.most_common(5),
            "categories": dict(category_counter),
            "top_authors": author_counter.most_common(5),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _format_date(self, timestamp: int) -> str:
        """Format timestamp to readable string."""
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def _highlight_title(self, title: str) -> str:
        """Apply highlighting to title if search service is available."""
        if not self.search_service:
            return title
            
        # Highlight priority tags
        priority_keywords = []
        for tag in TagSystem.PRIORITY_TAGS:
            priority_keywords.extend(TagSystem.get_tag_keywords(tag))
            
        return self.search_service.highlight_terms(title, priority_keywords)

    def _generate_markdown(self, posts: List[Post], stats: Dict[str, Any], title: str) -> str:
        """Generate Markdown report."""
        lines = []
        lines.append(f"# {title}")
        lines.append(f"Generated at: {stats['generated_at']}")
        lines.append("")
        
        lines.append("## 📊 Summary Statistics")
        lines.append(f"- **Total Posts:** {stats['total_posts']}")
        lines.append(f"- **Total Score:** {stats['total_score']}")
        lines.append(f"- **Average Score:** {stats['avg_score']:.1f}")
        lines.append("")
        
        lines.append("### Top Tags")
        for tag, count in stats['top_tags']:
            lines.append(f"- {tag}: {count}")
        lines.append("")
        
        lines.append("## 📎 Selected Posts")
        lines.append("| Title | Author | Score | Date | Tags |")
        lines.append("|---|---|---|---|---|")
        
        for post in posts:
            highlighted_title = self._highlight_title(post.title)
            date_str = self._format_date(post.created_at)
            tags_str = ", ".join(post.tags) if post.tags else "-"
            # Escape pipes in title for markdown table
            safe_title = highlighted_title.replace("|", "&#124;")
            url_md = f"[{safe_title}]({post.url})" if post.url else safe_title
            
            lines.append(f"| {url_md} | {post.author} | {post.score} | {date_str} | {tags_str} |")
            
        return "\n".join(lines)

    def _generate_html(self, posts: List[Post], stats: Dict[str, Any], title: str) -> str:
        """Generate HTML report."""
        # Simple HTML template
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{title}</title>",
            "<style>",
            "body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            ".ai-highlight { background-color: #fffde7; color: #e65100; font-weight: bold; padding: 0 4px; border-radius: 3px; border-bottom: 2px solid #ffcc80; }",
            ".stats { background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{title}</h1>",
            f"<p>Generated at: {stats['generated_at']}</p>",
            "<div class='stats'>",
            "<h2>📊 Summary Statistics</h2>",
            "<ul>",
            f"<li><strong>Total Posts:</strong> {stats['total_posts']}</li>",
            f"<li><strong>Total Score:</strong> {stats['total_score']}</li>",
            f"<li><strong>Average Score:</strong> {stats['avg_score']:.1f}</li>",
            "</ul>",
            "<h3>Top Tags</h3>",
            "<ul>"
        ]
        
        for tag, count in stats['top_tags']:
            html.append(f"<li>{tag}: {count}</li>")
        
        html.extend([
            "</ul>",
            "</div>",
            "<h2>📎 Selected Posts</h2>",
            "<table>",
            "<thead><tr><th>Title</th><th>Author</th><th>Score</th><th>Date</th><th>Tags</th></tr></thead>",
            "<tbody>"
        ])
        
        for post in posts:
            highlighted_title = self._highlight_title(post.title)
            # Convert markdown highlight to HTML span
            highlighted_title = highlighted_title.replace("**", '<span class="ai-highlight">', 1)
            while "**" in highlighted_title:
                highlighted_title = highlighted_title.replace("**", '</span>', 1)
                if "**" in highlighted_title:
                   highlighted_title = highlighted_title.replace("**", '<span class="ai-highlight">', 1)
            
            date_str = self._format_date(post.created_at)
            tags_str = ", ".join(post.tags) if post.tags else "-"
            
            title_cell = f'<a href="{post.url}">{highlighted_title}</a>' if post.url else highlighted_title
            
            html.append(f"<tr><td>{title_cell}</td><td>{post.author}</td><td>{post.score}</td><td>{date_str}</td><td>{tags_str}</td></tr>")
            
        html.extend([
            "</tbody>",
            "</table>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html)

    def _generate_csv(self, posts: List[Post]) -> str:
        """Generate CSV report."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["ID", "Title", "URL", "Author", "Score", "Date", "Category", "Tags"])
        
        for post in posts:
            date_str = self._format_date(post.created_at)
            tags_str = ", ".join(post.tags)
            writer.writerow([
                post.id,
                post.title,
                post.url,
                post.author,
                post.score,
                date_str,
                post.category.value,
                tags_str
            ])
            
        return output.getvalue()

    def _generate_txt(self, posts: List[Post], stats: Dict[str, Any], title: str) -> str:
        """Generate Plain Text report."""
        lines = []
        lines.append("=" * 60)
        lines.append(f" {title.upper()} ")
        lines.append(f" Generated at: {stats['generated_at']}")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append("SUMMARY STATISTICS")
        lines.append("-" * 20)
        lines.append(f"Total Posts: {stats['total_posts']}")
        lines.append(f"Total Score: {stats['total_score']}")
        lines.append(f"Average Score: {stats['avg_score']:.1f}")
        lines.append("")
        lines.append("Top Tags:")
        for tag, count in stats['top_tags']:
            lines.append(f"  - {tag}: {count}")
        lines.append("")
        
        lines.append("SELECTED POSTS")
        lines.append("-" * 20)
        
        for i, post in enumerate(posts, 1):
            date_str = self._format_date(post.created_at)
            tags_str = ", ".join(post.tags) if post.tags else "None"
            
            lines.append(f"{i}. {post.title}")
            lines.append(f"   URL: {post.url or 'N/A'}")
            lines.append(f"   Author: {post.author} | Score: {post.score} | Date: {date_str}")
            lines.append(f"   Tags: {tags_str}")
            lines.append("")
            
        return "\n".join(lines)
        
    def _generate_json(self, posts: List[Post], stats: Dict[str, Any], title: str) -> str:
        """Generate JSON report."""
        data = {
            "title": title,
            "statistics": stats,
            "posts": [p.to_dict() for p in posts]
        }
        return json.dumps(data, indent=2)
