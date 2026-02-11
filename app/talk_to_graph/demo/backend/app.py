from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from routes.sparql_routes import sparql_bp
from routes.llm_routes import llm_bp
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

def create_app():
    # Get paths
    backend_dir = Path(__file__).parent
    demo_dir = backend_dir.parent
    frontend_dir = demo_dir / 'frontend'
    static_dir = frontend_dir / 'static'
    
    print(f"📁 Frontend directory: {frontend_dir}")
    print(f"📁 Static directory: {static_dir}")
    print(f"   Frontend exists: {frontend_dir.exists()}")
    print(f"   Static exists: {static_dir.exists()}")
    
    app = Flask(__name__, 
                static_folder=str(static_dir),
                static_url_path='/static')
    CORS(app)  # Enable CORS for all routes

    # Register blueprints for SPARQL and LLM routes
    app.register_blueprint(sparql_bp, url_prefix='/api/sparql')
    app.register_blueprint(llm_bp, url_prefix='/api/llm')

    # Serve frontend - main page
    @app.route('/')
    def index():
        index_file = frontend_dir / 'index.html'
        print(f"📄 Serving index.html from: {index_file}")
        print(f"   File exists: {index_file.exists()}")
        if not index_file.exists():
            return jsonify({'error': 'index.html not found', 'path': str(index_file)}), 404
        return send_from_directory(str(frontend_dir), 'index.html')
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'message': 'Demo server is running'})
    
    # Debug route to check static files
    @app.route('/debug/files')
    def debug_files():
        css_file = static_dir / 'css' / 'styles.css'
        js_file = static_dir / 'js' / 'app.js'
        return jsonify({
            'frontend_dir': str(frontend_dir),
            'static_dir': str(static_dir),
            'index_exists': (frontend_dir / 'index.html').exists(),
            'css_exists': css_file.exists(),
            'css_path': str(css_file),
            'js_exists': js_file.exists(),
            'js_path': str(js_file),
            'static_files': [str(f) for f in static_dir.rglob('*') if f.is_file()] if static_dir.exists() else []
        })

    return app

if __name__ == '__main__':
    port = int(os.environ.get('DEMO_PORT', 5001))
    app = create_app()
    print(f"\n{'='*60}")
    print(f"🚀 Demo server starting on http://localhost:{port}")
    print(f"📊 SPARQL endpoint: http://localhost:{port}/api/sparql/query")
    print(f"🤖 LLM endpoint: http://localhost:{port}/api/llm/query")
    print(f"🌐 Frontend: http://localhost:{port}/")
    print(f"🔍 Debug: http://localhost:{port}/debug/files")
    print(f"{'='*60}\n")
    app.run(host='0.0.0.0', port=port, debug=True)
