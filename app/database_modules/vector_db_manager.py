"""
Vector Database Manager for DocEX
Manages Qdrant vector database operations for semantic document search
"""
import os
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.models import CollectionInfo
from flask import current_app

logger = logging.getLogger(__name__)

class DocEXVectorManager:
    """Vector database management integrated with existing JSON-LD workflow"""
    
    def __init__(self, config=None):
        """Initialize with configuration"""
        if config:
            self.qdrant_url = config.get('QDRANT_URL', 'http://localhost:6333')
            self.embedding_model_name = config.get('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
            self.jsonld_dir = config.get('JSONLD_DIR', 'database/jsonld')
        else:
            # Fallback to environment variables or defaults
            self.qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
            self.embedding_model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
            self.jsonld_dir = os.getenv('JSONLD_DIR', 'database/jsonld')
        
        self.qdrant_client = None
        self.embedding_model = None
        self._initialize_connections()
    
    def _initialize_connections(self):
        """Initialize Qdrant client and embedding model"""
        try:
            self.qdrant_client = QdrantClient(url=self.qdrant_url)
            logger.info(f"Connected to Qdrant at {self.qdrant_url}")
            
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector database connections: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check vector database connectivity and status"""
        try:
            collections = self.qdrant_client.get_collections()
            return {
                'status': 'healthy',
                'qdrant_url': self.qdrant_url,
                'collections_count': len(collections.collections),
                'embedding_model': self.embedding_model_name
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'qdrant_url': self.qdrant_url
            }
    
    def setup_collections(self):
        """Initialize collections optimized for DocEX JSON-LD structure"""
        collections = {
            'document_metadata': {
                'vector_size': 384,
                'distance': Distance.COSINE,
                'description': 'Document-level embeddings for similarity search'
            },
            'document_paragraphs': {
                'vector_size': 384,
                'distance': Distance.COSINE,
                'description': 'Paragraph-level embeddings for granular context'
            }
        }
        
        for collection_name, config in collections.items():
            try:
                # Check if collection exists
                collections_info = self.qdrant_client.get_collections()
                existing = [c.name for c in collections_info.collections]
                
                if collection_name not in existing:
                    self.qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=config['vector_size'],
                            distance=config['distance']
                        )
                    )
                    logger.info(f"Created collection: {collection_name}")
                else:
                    logger.info(f"Collection {collection_name} already exists")
                    
            except Exception as e:
                logger.error(f"Error setting up collection {collection_name}: {e}")
                raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def store_document_embedding(self, doc_id: str, document_jsonld: Dict[str, Any]):
        """Store document-level embedding"""
        try:
            # Create document text for embedding
            title = document_jsonld.get('docex:title', '')
            content_preview = ""
            
            # Extract first few paragraphs for content preview
            if 'docex:hasParagraph' in document_jsonld:
                paragraphs = document_jsonld['docex:hasParagraph']
                if isinstance(paragraphs, list) and len(paragraphs) > 0:
                    first_paras = paragraphs[:3]  # First 3 paragraphs
                    content_preview = " ".join([
                        p.get('docex:paragraphText', '') for p in first_paras
                    ])
            
            # Combine title and content for embedding
            embed_text = f"{title} {content_preview}".strip()
            if not embed_text:
                embed_text = doc_id  # Fallback to doc_id
            
            embedding = self.embed_text(embed_text)
            
            # Prepare metadata
            payload = {
                'doc_id': doc_id,
                'title': title,
                'format': document_jsonld.get('docex:fileFormat', 'unknown'),
                'paragraph_count': len(document_jsonld.get('docex:hasParagraph', [])),
                'processing_stage': 'initial',
                'has_stakeholders': False,  # Will be updated after extraction
                'human_validated': False
            }
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name='document_metadata',
                points=[
                    PointStruct(
                        id=hash(doc_id) % (2**63),  # Convert to positive integer
                        vector=embedding,
                        payload=payload
                    )
                ]
            )
            
            logger.info(f"Stored document embedding for: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing document embedding for {doc_id}: {e}")
            return False
    
    def find_similar_documents(self, query_doc_id: str, limit: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find documents similar to the query document"""
        try:
            # First, get the query document's embedding
            query_results = self.qdrant_client.scroll(
                collection_name='document_metadata',
                scroll_filter={
                    "must": [
                        {
                            "key": "doc_id",
                            "match": {"value": query_doc_id}
                        }
                    ]
                },
                limit=1,
                with_vectors=True  # Important: retrieve vectors
            )
            
            if not query_results[0]:
                logger.warning(f"Query document {query_doc_id} not found in vector database")
                return []
            
            query_point = query_results[0][0]
            query_vector = query_point.vector
            
            # Check if vector exists
            if query_vector is None:
                logger.error(f"No vector found for document {query_doc_id}")
                return []
            
            logger.info(f"Query vector type: {type(query_vector)}, length: {len(query_vector) if hasattr(query_vector, '__len__') else 'N/A'}")
            
            # Search for similar documents
            search_results = self.qdrant_client.search(
                collection_name='document_metadata',
                query_vector=query_vector,
                limit=limit + 1,  # +1 because query doc will be included
                score_threshold=threshold
            )
            
            # Filter out the query document itself and format results
            similar_docs = []
            for result in search_results:
                if result.payload['doc_id'] != query_doc_id:
                    similar_docs.append({
                        'doc_id': result.payload['doc_id'],
                        'title': result.payload.get('title', ''),
                        'similarity_score': result.score,
                        'metadata': result.payload
                    })
            
            logger.info(f"Found {len(similar_docs)} similar documents for {query_doc_id}")
            return similar_docs[:limit]  # Ensure we don't exceed limit
            
        except Exception as e:
            logger.error(f"Error finding similar documents for {query_doc_id}: {e}")
            return []
    
    def update_document_stage(self, doc_id: str, stage: str, **kwargs):
        """Update document processing stage and metadata"""
        try:
            # Get current document point
            results = self.qdrant_client.scroll(
                collection_name='document_metadata',
                scroll_filter={
                    "must": [
                        {
                            "key": "doc_id", 
                            "match": {"value": doc_id}
                        }
                    ]
                },
                limit=1
            )
            
            if not results[0]:
                logger.warning(f"Document {doc_id} not found for stage update")
                return False
            
            point = results[0][0]
            
            # Update payload
            updated_payload = point.payload.copy()
            updated_payload['processing_stage'] = stage
            updated_payload.update(kwargs)
            
            # Update in Qdrant
            self.qdrant_client.upsert(
                collection_name='document_metadata',
                points=[
                    PointStruct(
                        id=point.id,
                        vector=point.vector,
                        payload=updated_payload
                    )
                ]
            )
            
            logger.info(f"Updated document {doc_id} to stage: {stage}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating document stage for {doc_id}: {e}")
            return False