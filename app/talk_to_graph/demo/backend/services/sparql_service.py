from flask import jsonify
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, Namespace, RDF, RDFS
from utils.jsonld_loader import JSONLDLoader
from utils.sparql_generator import SPARQLGenerator
import time

class SPARQLService:  # Make sure it's exactly this name
    """Service for SPARQL-based queries"""
    
    def __init__(self):
        self.loader = JSONLDLoader()
        self.generator = SPARQLGenerator()
        self.graph = None
        self._load_graph()
    
    def _load_graph(self):
        """Load all JSON-LD files into RDF graph"""
        print("📚 Loading JSON-LD files into RDF graph...")
        self.graph = self.loader.load_all_jsonld()
        print(f"✅ Graph loaded: {len(self.graph)} triples")
    
    def query_from_natural_language(self, question: str) -> dict:
        """Convert natural language to SPARQL and execute"""
        start_time = time.time()
        
        # Generate SPARQL query from natural language
        sparql_result = self.generator.generate_sparql(question)
        sparql_query = sparql_result['query']
        thought_process = sparql_result['thought_process']
        
        # Execute SPARQL query
        results = self.execute_sparql(sparql_query)
        
        # Format results as natural language
        answer = self._format_results_as_text(results, question)
        
        execution_time = time.time() - start_time
        
        return {
            'answer': answer,
            'sparql_query': sparql_query,
            'results': results,
            'execution_time': execution_time,
            'thought_process': thought_process
        }
    
    def execute_sparql(self, sparql_query: str) -> list:
        """Execute SPARQL query on the graph"""
        if self.graph is None:
            self._load_graph()
        
        try:
            results = self.graph.query(sparql_query)
            
            # Convert results to list of dicts
            formatted_results = []
            for row in results:
                result_dict = {}
                for var in results.vars:
                    value = row[var]
                    result_dict[str(var)] = str(value) if value else None
                formatted_results.append(result_dict)
            
            return formatted_results
            
        except Exception as e:
            raise Exception(f"SPARQL execution error: {str(e)}")
    
    def _format_results_as_text(self, results: list, question: str) -> str:
        """Format SPARQL results as natural language answer"""
        if not results:
            return "No results found in the knowledge graph for your query."
        
        if len(results) == 1:
            # Single result
            result = results[0]
            if 'name' in result:
                text = f"Found: {result['name']}"
                if 'role' in result:
                    text += f" - {result['role']}"
                if 'organization' in result:
                    text += f" at {result['organization']}"
                return text
        
        # Multiple results
        answer_parts = [f"Found {len(results)} results:\n"]
        for i, result in enumerate(results, 1):
            if 'name' in result:
                line = f"{i}. {result['name']}"
                if 'role' in result:
                    line += f" - {result['role']}"
                if 'stakeholderType' in result:
                    line += f" ({result['stakeholderType']})"
                if 'organization' in result:
                    line += f" at {result['organization']}"
                answer_parts.append(line)
        
        return "\n".join(answer_parts)