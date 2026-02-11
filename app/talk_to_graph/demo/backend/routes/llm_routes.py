from flask import Blueprint, request, jsonify
from services.llm_service import LLMService

llm_bp = Blueprint('llm', __name__)
llm_service = LLMService()

@llm_bp.route('/query', methods=['POST'])
def llm_query():
    """Handle LLM-based vector search queries"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Query using vector search + LLM
        result = llm_service.query_with_vector_search(question)
        
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'sources': result['sources'],
            'context_used': result.get('context_used', 0),
            'execution_time': result.get('execution_time', 0)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@llm_bp.route('/embed', methods=['POST'])
def embed_data():
    """Embed JSON-LD data into vector database"""
    try:
        result = llm_service.embed_all_jsonld()
        
        return jsonify({
            'success': True,
            'message': f'Embedded {result["total_items"]} items',
            'details': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@llm_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get vector database statistics"""
    try:
        stats = llm_service.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500