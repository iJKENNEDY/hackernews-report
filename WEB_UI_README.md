# Web UI for Hackernews Report

This branch (`feature/web-ui`) adds a basic web interface to visualize Hacker News posts stored in the database.

## Features

- 📊 View all posts in a clean, organized interface
- 🏷️ Filter posts by category (Stories, Jobs, Ask HN, Polls, Other)
- 📈 See category statistics in the sidebar
- 🔗 Direct links to original posts and Hacker News discussions
- 📱 Responsive design for mobile and desktop
- 🎨 Clean, modern UI inspired by Hacker News orange theme

## Installation

1. Install the additional web dependencies:
```bash
pip install -r requirements.txt
```

## Running the Web UI

### Option 1: Using Flask directly
```bash
python -m src.web_app
```

### Option 2: Using Flask CLI
```bash
export FLASK_APP=src.web_app
flask run
```

The web interface will be available at: **http://localhost:5000**

## Usage

### 1. Fetch Posts First
Before using the web UI, you need to fetch some posts using the CLI:

```bash
python -m src fetch --limit 50
```

### 2. Browse Posts
- Visit http://localhost:5000 to see all posts
- Click on category filters in the sidebar to filter by type
- Click on post titles to view details or visit external links

### 3. API Endpoints

The web UI also provides JSON API endpoints:

**Get posts:**
```bash
curl http://localhost:5000/api/posts
curl http://localhost:5000/api/posts?category=story
curl http://localhost:5000/api/posts?limit=10
```

**Get statistics:**
```bash
curl http://localhost:5000/api/stats
```

## Project Structure

```
├── src/
│   └── web_app.py          # Flask application
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Main posts list
│   ├── post_detail.html   # Single post view
│   └── 404.html           # Error page
├── static/
│   └── style.css          # CSS styles
└── WEB_UI_README.md       # This file
```

## Screenshots

### Main Page
The main page displays all posts with category filters in the sidebar.

### Post Detail
Click on any post to see detailed information and links to the original source.

## Development

To run in development mode with auto-reload:

```bash
export FLASK_ENV=development
python -m src.web_app
```

## Configuration

The web UI uses the same database configuration as the CLI application. You can override the database path using the `DB_PATH` environment variable:

```bash
export DB_PATH=/path/to/custom/database.db
python -m src.web_app
```

## Future Enhancements

Potential improvements for the web UI:
- [ ] Search functionality
- [ ] Sorting options (by score, date, author)
- [ ] Pagination for large datasets
- [ ] Real-time updates using WebSockets
- [ ] Dark mode toggle
- [ ] Export posts to CSV/JSON
- [ ] User authentication for admin features
- [ ] Inline post fetching from the UI

## Contributing

This is a feature branch. To contribute:

1. Create a sub-branch from `feature/web-ui`
2. Make your changes
3. Submit a pull request to merge into `feature/web-ui`

## License

Same as the main project.
