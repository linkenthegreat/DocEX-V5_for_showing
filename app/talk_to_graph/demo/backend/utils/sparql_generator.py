"""Generate SPARQL queries from natural language using simple pattern matching"""
import re

class SPARQLGenerator:
    """Generate SPARQL queries from natural language questions"""
    
    def __init__(self):
        self.patterns = {
            'find_stakeholders': {
                'patterns': [
                    r'(find|show|list|who are|get).*(stakeholder|people|person)',
                    r'(accessibility|government|community).*(advocate|coordinator|agency)',
                ],
                'template': '''
PREFIX vocab: <http://example.org/vocab#>
PREFIX sh: <https://example.org/stakeholder#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT DISTINCT ?name ?role ?type ?org
WHERE {{
    ?s a ?stakeholderClass ;
       vocab:name ?name .
    OPTIONAL {{ ?s vocab:role ?role }}
    OPTIONAL {{ ?s vocab:stakeholderType ?type }}
    OPTIONAL {{ ?s vocab:organization ?org }}
    {filter}
}}
LIMIT 10
'''
            },
            'count_stakeholders': {
                'patterns': [
                    r'how many.*(stakeholder|people)',
                    r'count.*(stakeholder|people)'
                ],
                'template': '''
PREFIX vocab: <http://example.org/vocab#>

SELECT (COUNT(DISTINCT ?s) as ?count)
WHERE {{
    ?s a ?type ;
       vocab:name ?name .
    {filter}
}}
'''
            }
        }
    
    def generate_sparql(self, question: str) -> dict:
        """Generate SPARQL query from natural language"""
        question_lower = question.lower()
        
        thought_process = []
        thought_process.append(f"Analyzing question: '{question}'")
        
        # Detect query type
        query_type = self._detect_query_type(question_lower)
        thought_process.append(f"Detected query type: {query_type}")
        
        # Generate appropriate SPARQL
        if query_type == 'find_stakeholders':
            sparql = self._generate_find_stakeholders(question_lower)
            thought_process.append("Generated SPARQL query to find stakeholders")
        elif query_type == 'count_stakeholders':
            sparql = self._generate_count_query(question_lower)
            thought_process.append("Generated SPARQL COUNT query")
        else:
            # Default: find all stakeholders
            sparql = self._generate_default_query()
            thought_process.append("Using default query (list all stakeholders)")
        
        return {
            'query': sparql,
            'thought_process': thought_process
        }
    
    def _detect_query_type(self, question: str) -> str:
        """Detect the type of query from the question"""
        if any(re.search(pattern, question) for pattern in self.patterns['count_stakeholders']['patterns']):
            return 'count_stakeholders'
        
        if any(re.search(pattern, question) for pattern in self.patterns['find_stakeholders']['patterns']):
            return 'find_stakeholders'
        
        return 'find_stakeholders'  # Default
    
    def _generate_find_stakeholders(self, question: str) -> str:
        """Generate SPARQL to find stakeholders"""
        filter_conditions = []
        
        # Look for specific roles/types
        if 'accessibility' in question and 'advocate' in question:
            filter_conditions.append('FILTER(CONTAINS(LCASE(str(?role)), "accessibility"))')
        elif 'government' in question:
            filter_conditions.append('FILTER(CONTAINS(LCASE(str(?type)), "government"))')
        elif 'community' in question:
            filter_conditions.append('FILTER(CONTAINS(LCASE(str(?role)), "community"))')
        elif 'coordinator' in question:
            filter_conditions.append('FILTER(CONTAINS(LCASE(str(?role)), "coordinator"))')
        
        filter_str = '\n    '.join(filter_conditions) if filter_conditions else ''
        
        return self.patterns['find_stakeholders']['template'].format(filter=filter_str)
    
    def _generate_count_query(self, question: str) -> str:
        """Generate SPARQL COUNT query"""
        filter_str = ''
        # Add filters if specific types mentioned
        if 'government' in question:
            filter_str = 'FILTER(CONTAINS(LCASE(str(?type)), "government"))'
        
        return self.patterns['count_stakeholders']['template'].format(filter=filter_str)
    
    def _generate_default_query(self) -> str:
        """Generate default query to list all stakeholders"""
        return self.patterns['find_stakeholders']['template'].format(filter='')