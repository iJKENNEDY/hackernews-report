import os
from flask import Flask, g
from src.config import DB_PATH
from src.database import Database

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

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True, template_folder='../../templates', static_folder='../../static')
    
    # Load default config
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=DB_PATH,
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register database teardown
    app.teardown_appcontext(close_db)
    
    # Register blueprints
    from . import routes
    app.register_blueprint(routes.bp)
    
    # Register template filters
    from . import filters
    filters.register_filters(app)

    return app
