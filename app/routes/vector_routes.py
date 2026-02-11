"""
Vector Database Routes for DocEX
Handles vector database operations via web interface
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from ..database_modules.vector_db_manager import DocEXVectorManager
from ..embedding.document_embedder import DocumentEmbedder
from ..config.vector_config import VectorConfig
import logging
import os

logger = logging.getLogger(__name__)

vector_bp = Blueprint('vector', __name__, url_prefix='/vector')

@vector_bp.route('/setup')
def setup_vector_database():
    """Initialize vector database collections"""
    try:
        config = VectorConfig.get_vector_config()
        vector_manager = DocEXVectorManager(config)
        
        # Health check first
        health = vector_manager.health_check()
        if health['status'] != 'healthy':
            flash(f"Vector database not available: {health.get('error', 'Unknown error')}")
            return redirect(url_for('main.root'))
        
        # Setup collections
        vector_manager.setup_collections()
        flash("Vector database collections initialized successfully")
        logger.info("Vector database setup completed")
        
        return redirect(url_for('vector.vector_status'))
        
    except Exception as e:
        logger.error(f"Error setting up vector database: {e}")
        flash(f"Error setting up vector database: {str(e)}")
        return redirect(url_for('main.root'))

@vector_bp.route('/embed_existing')
def embed_existing_documents():
    """Process existing JSON-LD documents into embeddings"""
    try:
        config = VectorConfig.get_vector_config()
        vector_manager = DocEXVectorManager(config)
        embedder = DocumentEmbedder(vector_manager)
        
        # Process existing documents
        results = embedder.embed_existing_jsonld_documents()
        
        flash(f"Embedding complete: {results['processed']} processed, {results['errors']} errors")
        logger.info(f"Batch embedding results: {results}")
        
        return redirect(url_for('vector.vector_status'))
        
    except Exception as e:
        logger.error(f"Error in batch embedding: {e}")
        flash(f"Error processing embeddings: {str(e)}")
        return redirect(url_for('main.root'))

@vector_bp.route('/status')
def vector_status():
    """Display vector database status"""
    try:
        config = VectorConfig.get_vector_config()
        vector_manager = DocEXVectorManager(config)
        
        health = vector_manager.health_check()
        
        return render_template('vector_status.html', 
                             health=health,
                             config=config)
        
    except Exception as e:
        logger.error(f"Error checking vector status: {e}")
        flash(f"Error checking vector database status: {str(e)}")
        return redirect(url_for('main.root'))

@vector_bp.route('/api/health')
def api_health():
    """API endpoint for vector database health check"""
    try:
        config = VectorConfig.get_vector_config()
        vector_manager = DocEXVectorManager(config)
        health = vector_manager.health_check()
        return jsonify(health)
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@vector_bp.route('/api/similar/<doc_id>')
def api_find_similar(doc_id):
    """API endpoint to find similar documents"""
    try:
        config = VectorConfig.get_vector_config()
        vector_manager = DocEXVectorManager(config)
        
        limit = request.args.get('limit', 5, type=int)
        threshold = request.args.get('threshold', 0.7, type=float)
        
        similar_docs = vector_manager.find_similar_documents(doc_id, limit, threshold)
        
        return jsonify({
            'doc_id': doc_id,
            'similar_documents': similar_docs,
            'count': len(similar_docs)
        })
        
    except Exception as e:
        logger.error(f"Error finding similar documents for {doc_id}: {e}")
        return jsonify({'error': str(e)}), 500

print("📦 Vector routes module loaded with vector_bp")