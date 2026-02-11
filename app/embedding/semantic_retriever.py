"""
Semantic Retrieval System for DocEX
Provides context for LLM extraction enhancement
"""
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class DocEXSemanticRetriever:
    """Retrieve contextual information from existing JSON-LD documents"""
    
    def __init__(self, vector_manager):
        self.vector_manager = vector_manager
    
    def find_similar_documents(self, query_doc_jsonld: Dict[str, Any], filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Find documents similar to current document for context"""
        try:
            doc_id = query_doc_jsonld.get('@id', 'unknown')
            
            # Use vector manager to find similar documents
            similar_docs = self.vector_manager.find_similar_documents(
                query_doc_id=doc_id,
                limit=5,
                threshold=0.7
            )
            
            # Apply additional filters if provided
            if filters:
                similar_docs = self._apply_filters(similar_docs, filters)
            
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            return []
    
    def _apply_filters(self, documents: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply additional filters to similar documents"""
        filtered_docs = []
        
        for doc in documents:
            metadata = doc.get('metadata', {})
            include_doc = True
            
            for filter_key, filter_value in filters.items():
                if filter_key in metadata:
                    if metadata[filter_key] != filter_value:
                        include_doc = False
                        break
            
            if include_doc:
                filtered_docs.append(doc)
        
        return filtered_docs
    
    def build_extraction_context(self, similar_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create context for LLM extraction enhancement"""
        context = {
            'similar_documents': similar_docs,
            'context_confidence': self.calculate_context_confidence(similar_docs),
            'document_patterns': self.extract_document_patterns(similar_docs)
        }
        
        return context
    
    def calculate_context_confidence(self, similar_docs: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for retrieved context"""
        if not similar_docs:
            return 0.0
        
        # Average similarity scores
        total_score = sum(doc.get('similarity_score', 0.0) for doc in similar_docs)
        avg_score = total_score / len(similar_docs)
        
        # Factor in number of similar documents found
        count_factor = min(len(similar_docs) / 3.0, 1.0)  # Optimal around 3 docs
        
        return avg_score * count_factor
    
    def extract_document_patterns(self, similar_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract patterns from similar documents"""
        patterns = {
            'common_formats': {},
            'processing_stages': {},
            'validation_status': {}
        }
        
        for doc in similar_docs:
            metadata = doc.get('metadata', {})
            
            # Count formats
            doc_format = metadata.get('format', 'unknown')
            patterns['common_formats'][doc_format] = patterns['common_formats'].get(doc_format, 0) + 1
            
            # Count processing stages  
            stage = metadata.get('processing_stage', 'unknown')
            patterns['processing_stages'][stage] = patterns['processing_stages'].get(stage, 0) + 1
            
            # Count validation status
            validated = metadata.get('human_validated', False)
            patterns['validation_status'][validated] = patterns['validation_status'].get(validated, 0) + 1
        
        return patterns
    
    def explain_context_selection(self, context: Dict[str, Any]) -> str:
        """Provide human-readable explanation of context selection"""
        similar_docs = context.get('similar_documents', [])
        confidence = context.get('context_confidence', 0.0)
        
        if not similar_docs:
            return "No similar documents found for context."
        
        explanation = f"Found {len(similar_docs)} similar documents with {confidence:.2f} confidence. "
        
        # Add pattern information
        patterns = context.get('document_patterns', {})
        if patterns.get('common_formats'):
            top_format = max(patterns['common_formats'].items(), key=lambda x: x[1])
            explanation += f"Most common format: {top_format[0]}. "
        
        return explanation