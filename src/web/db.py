import os
from flask import g
from src.database import Database
from src.config import DB_PATH

def get_db():
    if 'db' not in g:
        # Initialize database with path from config
        # Note: Using absolute path resolution if needed, but DB_PATH is usually good
        db_path = os.getenv('DB_PATH', DB_PATH)
        g.db = Database(db_path)
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
