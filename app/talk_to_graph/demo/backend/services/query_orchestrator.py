from flask import request
from services.sparql_service import SparqlService
from services.llm_service import LlmService

class QueryOrchestrator:
    def __init__(self):
        self.sparql_service = SparqlService()
        self.llm_service = LlmService()

    def route_query(self, query):
        if self.is_complex_query(query):
            return self.sparql_service.execute_query(query)
        else:
            return self.llm_service.process_query(query)

    def is_complex_query(self, query):
        complex_patterns = [
            r"how many .* are .* and also .*",  # Multi-condition
            r"show .* related to .* through .*",  # Multi-hop
            r"count .* grouped by .*",  # Aggregation
            r"find .* that have both .* and .*"  # Complex filters
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, query.lower()):
                return True
        
        return False