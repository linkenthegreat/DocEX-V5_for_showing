from flask import Blueprint, jsonify, request
from ..database_modules.vector_db_manager import DocEXVectorManager
from ..config.vector_config import VectorConfig
import logging

logger = logging.getLogger(__name__)

debug_bp = Blueprint('vector_debug', __name__, url_prefix='/vector/debug')

@debug_bp.route('/list_documents')
def list_documents():
    """List all documents in vector database"""
    try:
        config = VectorConfig.get_vector_config()
        vector_manager = DocEXVectorManager(config)
        
        # Get all documents from collection
        results = vector_manager.qdrant_client.scroll(
            collection_name='document_metadata',
            limit=100  # Adjust as needed
        )
        
        documents = []
        for point in results[0]:
            documents.append({
                'id': point.id,
                'doc_id': point.payload.get('doc_id'),
                'title': point.payload.get('title'),
                'format': point.payload.get('format'),
                'paragraph_count': point.payload.get('paragraph_count'),
                'processing_stage': point.payload.get('processing_stage')
            })
        
        return jsonify({
            'total_documents': len(documents),
            'documents': documents
        })
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({'error': str(e)}), 500