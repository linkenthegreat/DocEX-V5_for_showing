"""
Updated Context-Enhanced LLM Adapter using JSON-LD Bridge
"""
import logging
from typing import Dict, List, Any, Optional
from .jsonld_extraction_bridge import JSONLDExtractionBridge
from ...database_modules.vector_db_manager import DocEXVectorManager
from ...retrieval.semantic_retriever import DocEXSemanticRetriever
from ...config.vector_config import VectorConfig

logger = logging.getLogger(__name__)

class ContextEnhancedLLMAdapter:
    """Context-enhanced adapter using JSON-LD bridge"""
    
    def __init__(self, base_llm_adapter):
        """Initialize with existing text-based LLM adapter"""
        
        # Create bridge for JSON-LD processing
        self.jsonld_bridge = JSONLDExtractionBridge(base_llm_adapter)
        
        # Initialize vector components
        try:
            config = VectorConfig.get_vector_config()
            self.vector_manager = DocEXVectorManager(config)
            self.semantic_retriever = DocEXSemanticRetriever(self.vector_manager)
            self.context_available = True
            logger.info("Context-enhanced adapter with JSON-LD bridge initialized successfully")
        except Exception as e:
            logger.warning(f"Vector database not available, falling back to standard extraction: {e}")
            self.context_available = False
        
        # Configuration
        self.context_enabled = True
        self.similarity_threshold = 0.5
        self.max_similar_docs = 3
    
    async def extract_stakeholders_with_context(
        self, 
        document_jsonld: Dict[str, Any], 
        use_context: bool = True,
        provider: str = None
    ) -> Dict[str, Any]:
        """Extract stakeholders using context-enhanced approach with JSON-LD bridge"""
        
        doc_id = document_jsonld.get('@id', 'unknown')
        
        try:
            # Check if context enhancement is possible and requested
            if use_context and self.context_enabled and self.context_available:
                logger.info(f"Attempting context-enhanced extraction for: {doc_id}")
                
                # Store document embedding for future context (non-blocking)
                try:
                    self.vector_manager.store_document_embedding(doc_id, document_jsonld)
                    logger.debug(f"Stored embedding for future context: {doc_id}")
                except Exception as e:
                    logger.warning(f"Could not store embedding for {doc_id}: {e}")
                
                # Find similar documents for context
                similar_docs = self.semantic_retriever.find_similar_documents(
                    document_jsonld,
                    filters={'has_stakeholders': True}
                )
                
                if similar_docs and len(similar_docs) > 0:
                    logger.info(f"Found {len(similar_docs)} similar documents for context")
                    
                    # Build context and create enhanced JSON-LD
                    context = self.semantic_retriever.build_extraction_context(similar_docs)
                    enhanced_jsonld = self._add_context_to_jsonld(document_jsonld, context)
                    
                    # Extract using enhanced document
                    extraction_result = await self.jsonld_bridge.extract_stakeholders_from_jsonld(
                        enhanced_jsonld, provider
                    )
                    
                    # Add context metadata
                    extraction_result['context_metadata'] = {
                        'similar_documents': [doc['doc_id'] for doc in similar_docs],
                        'context_confidence': context.get('context_confidence', 0.0),
                        'context_used': True,
                        'extraction_method': 'context_enhanced',
                        'similar_count': len(similar_docs)
                    }
                    
                    logger.info(f"Context-enhanced extraction completed for: {doc_id}")
                    return extraction_result
                
                else:
                    logger.info(f"No similar documents found, using standard extraction for: {doc_id}")
            
            # Fallback to standard extraction using bridge
            logger.info(f"Using standard JSON-LD extraction for: {doc_id}")
            extraction_result = await self.jsonld_bridge.extract_stakeholders_from_jsonld(
                document_jsonld, provider
            )
            
            # Add metadata indicating no context was used
            extraction_result['context_metadata'] = {
                'similar_documents': [],
                'context_confidence': 0.0,
                'context_used': False,
                'extraction_method': 'standard',
                'reason': 'no_similar_docs' if self.context_available else 'vector_db_unavailable'
            }
            
            return extraction_result
            
        except Exception as e:
            logger.error(f"Error in context-enhanced extraction for {doc_id}: {e}")
            # Final fallback using bridge
            try:
                return await self.jsonld_bridge.extract_stakeholders_from_jsonld(
                    document_jsonld, provider
                )
            except Exception as fallback_error:
                logger.error(f"Fallback extraction also failed for {doc_id}: {fallback_error}")
                return self.jsonld_bridge._create_error_result(doc_id, str(fallback_error))
    
    def _add_context_to_jsonld(self, document_jsonld: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Add context guidance to JSON-LD document"""
        
        similar_docs = context.get('similar_documents', [])
        confidence = context.get('context_confidence', 0.0)
        
        if not similar_docs:
            return document_jsonld
        
        # Create enhanced document with context guidance
        enhanced_jsonld = document_jsonld.copy()
        
        # Add context as a special paragraph at the beginning
        context_guidance = f"""
CONTEXT GUIDANCE (Based on {len(similar_docs)} similar documents, confidence: {confidence:.2f}):

From analysis of similar documents in this domain, stakeholders typically include:
- Government agencies, departments, and regulatory bodies
- Community organizations and advocacy groups  
- Service providers and support organizations
- Individual participants, clients, and beneficiaries
- Professional associations and industry bodies
- Funding organizations and sponsors

Focus on stakeholders explicitly mentioned in the following document while using this context as guidance.

---
"""
        
        # Add context as first paragraph
        context_para = {
            "docex:paragraphText": context_guidance,
            "docex:paragraphNumber": 0
        }
        
        # Modify paragraphs to include context
        if 'docex:hasParagraph' in enhanced_jsonld:
            existing_paras = enhanced_jsonld['docex:hasParagraph']
            if isinstance(existing_paras, list):
                enhanced_jsonld['docex:hasParagraph'] = [context_para] + existing_paras
            else:
                enhanced_jsonld['docex:hasParagraph'] = [context_para, existing_paras]
        else:
            enhanced_jsonld['docex:hasParagraph'] = [context_para]
        
        return enhanced_jsonld
    
    def get_context_explanation(self, extraction_result: Dict[str, Any]) -> str:
        """Generate explanation of context usage"""
        
        context_meta = extraction_result.get('context_metadata', {})
        
        if context_meta.get('context_used', False):
            similar_count = context_meta.get('similar_count', 0)
            confidence = context_meta.get('context_confidence', 0.0)
            similar_docs = context_meta.get('similar_documents', [])
            
            explanation = f"""Context-Enhanced Extraction Used:
- Found {similar_count} similar documents for guidance
- Context confidence: {confidence:.2f}
- Similar document patterns helped inform stakeholder identification
- Extraction focused on explicitly mentioned stakeholders in current document
- Similar documents: {', '.join(similar_docs)}"""
            
            return explanation
        else:
            reason = context_meta.get('reason', 'unknown')
            if reason == 'no_similar_docs':
                return "Standard extraction used: No similar documents found for context guidance."
            elif reason == 'vector_db_unavailable':
                return "Standard extraction used: Vector database not available."
            else:
                return "Standard extraction used."