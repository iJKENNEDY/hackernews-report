"""Configuration settings for Hackernews Report application."""

import os
from pathlib import Path


# Database configuration
DB_PATH = os.environ.get(
    "HN_DB_PATH",
    str(Path.home() / ".hackernews_report" / "posts.db")
)

# API configuration
API_BASE_URL = os.environ.get(
    "HN_API_BASE_URL",
    "https://hacker-news.firebaseio.com/v0/"
)

# Default fetch limit
DEFAULT_LIMIT = int(os.environ.get("HN_DEFAULT_LIMIT", "30"))

# Logging configuration
LOG_LEVEL = os.environ.get("HN_LOG_LEVEL", "INFO")
