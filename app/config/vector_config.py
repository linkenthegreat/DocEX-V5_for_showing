"""
Vector Database Configuration for DocEX
"""
import os

class VectorConfig:
    """Vector database specific configuration"""
    
    # Qdrant Configuration
    QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
    QDRANT_COLLECTION_PREFIX = os.getenv('QDRANT_COLLECTION_PREFIX', 'docex_')
    
    # Embedding Configuration
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2') 
    VECTOR_SEARCH_LIMIT = int(os.getenv('VECTOR_SEARCH_LIMIT', '5'))
    CONTEXT_THRESHOLD = float(os.getenv('CONTEXT_THRESHOLD', '0.7'))
    
    # Performance Settings
    BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', '10'))
    CACHE_EMBEDDINGS = os.getenv('CACHE_EMBEDDINGS', 'true').lower() == 'true'
    
    @classmethod
    def get_vector_config(cls) -> dict:
        """Get vector database configuration as dictionary"""
        return {
            'QDRANT_URL': cls.QDRANT_URL,
            'EMBEDDING_MODEL': cls.EMBEDDING_MODEL,
            'JSONLD_DIR': os.getenv('JSONLD_DIR', 'database/jsonld'),
            'VECTOR_SEARCH_LIMIT': cls.VECTOR_SEARCH_LIMIT,
            'CONTEXT_THRESHOLD': cls.CONTEXT_THRESHOLD
        }