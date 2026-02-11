from flask import Blueprint, request, jsonify
from services.sparql_service import SPARQLService  # Make sure it's SPARQLService, not SparqlService

sparql_bp = Blueprint('sparql', __name__)
sparql_service = SPARQLService()

@sparql_bp.route('/query', methods=['POST'])
def sparql_query():
    """Handle SPARQL queries"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Generate and execute SPARQL query
        result = sparql_service.query_from_natural_language(question)
        
        return jsonify({
            'success': True,
            'answer': result['answer'],
            'sparql_query': result['sparql_query'],
            'results': result['results'],
            'execution_time': result.get('execution_time', 0),
            'thought_process': result.get('thought_process', [])
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sparql_bp.route('/direct', methods=['POST'])
def sparql_direct():
    """Execute direct SPARQL query"""
    try:
        data = request.get_json()
        sparql_query = data.get('query', '')
        
        if not sparql_query:
            return jsonify({'error': 'No SPARQL query provided'}), 400
        
        result = sparql_service.execute_sparql(sparql_query)
        
        return jsonify({
            'success': True,
            'results': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500