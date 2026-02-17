from datetime import datetime

def register_filters(app):
    
    @app.template_filter('timestamp_to_date')
    def timestamp_to_date(timestamp):
        """Convert Unix timestamp to readable date."""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%B %d, %Y at %I:%M %p')
        except (ValueError, TypeError):
            return 'Unknown date'

    @app.template_filter('highlight_markdown')
    def highlight_markdown(text):
        """
        Convert markdown strong emphasis (**text**) to HTML span with highlight class.
        Assumes **text** format used by SearchService.
        """
        if not text:
            return ""
        parts = text.split('**')
        new_text = ""
        for i, part in enumerate(parts):
            if i % 2 == 0:
                new_text += part
            else:
                new_text += f'<span class="ai-highlight">{part}</span>'
        return new_text
