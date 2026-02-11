"""
DocEX Application Factory Module

This module contains the Flask application factory that initializes and configures
the DocEX web application, including blueprints, extensions, and error handlers.
"""

import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Basic stub implementation for testing
__version__ = "0.1.0"

def create_app(config_class=None):
    """
    Application factory function that creates and configures a Flask application.
    """
    # Create Flask application
    app = Flask(__name__)
    
    # Get the app directory
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(app_dir)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    app.config['APP_DIR'] = app_dir
    
    # Add database configuration
    app.config['DATABASE_DIR'] = os.path.join(project_root, 'database')
    app.config['JSONLD_DIR'] = os.path.join(project_root, 'database', 'jsonld')
    app.config['TRIPLES_DIR'] = os.path.join(project_root, 'database', 'triples')
    app.config['UPLOAD_FOLDER'] = os.path.join(project_root, 'uploads')
    
    # Add missing CSV configuration
    app.config['CSV_FILE'] = os.path.join(project_root, 'database', 'System_files_metadata.csv')
    app.config['STORAGE_INDEX'] = os.path.join(project_root, 'database', 'storage_index.json')
    
    # Add vector database configuration
    app.config['VECTOR_DB_PATH'] = os.path.join(project_root, 'database', 'vector_db')
    app.config['EMBEDDINGS_PATH'] = os.path.join(project_root, 'database', 'embeddings')
    
    # Ensure directories exist
    os.makedirs(app.config['DATABASE_DIR'], exist_ok=True)
    os.makedirs(app.config['JSONLD_DIR'], exist_ok=True)
    os.makedirs(app.config['TRIPLES_DIR'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['VECTOR_DB_PATH'], exist_ok=True)
    os.makedirs(app.config['EMBEDDINGS_PATH'], exist_ok=True)
    
    # Create CSV file if it doesn't exist
    if not os.path.exists(app.config['CSV_FILE']):
        import csv
        with open(app.config['CSV_FILE'], 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'file_path', 'file_type', 'upload_date', 'status'])
    
    print("✅ App configuration:")
    print(f"   - APP_DIR: {app.config['APP_DIR']}")
    print(f"   - DATABASE_DIR: {app.config['DATABASE_DIR']}")
    print(f"   - JSONLD_DIR: {app.config['JSONLD_DIR']}")
    print(f"   - TRIPLES_DIR: {app.config['TRIPLES_DIR']}")
    print(f"   - CSV_FILE: {app.config['CSV_FILE']}")
    
    print("🔍 Registering blueprints...")
    
    try:
        # Import blueprints with correct module names
        from app.routes.main import main_bp
        print("✅ main_bp imported successfully")
        
        from app.routes.vector_routes import vector_bp  # Fixed: use vector_routes instead of vector
        print("✅ vector_bp imported successfully")
        
        from app.routes.agent_api import agent_api_bp
        print("✅ agent_api_bp imported successfully")
        
        # Register blueprints
        app.register_blueprint(main_bp)
        print("✅ main_bp registered")
        
        app.register_blueprint(vector_bp)
        print("✅ vector_bp registered")
        
        app.register_blueprint(agent_api_bp)
        print("✅ agent_api_bp registered")
        
        print("✅ All blueprints registered successfully:")
        print(f"   - main_bp: {main_bp.name}")
        print(f"   - vector_bp: {vector_bp.name}")
        print(f"   - agent_api_bp: {agent_api_bp.name}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔍 Available route files:")
        routes_dir = os.path.join(os.path.dirname(__file__), 'routes')
        if os.path.exists(routes_dir):
            for file in os.listdir(routes_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    print(f"   - {file}")
        raise
    
    # Add basic route for testing
    @app.route('/health')
    def health_check():
        return {'status': 'ok', 'version': __version__}
    
    return app