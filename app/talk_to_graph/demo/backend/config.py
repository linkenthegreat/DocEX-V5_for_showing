import os
from pathlib import Path

class Config:
    """Configuration settings for the application."""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    BACKEND_DIR = Path(__file__).parent
    
    # Database paths (relative to project root)
    PROJECT_ROOT = BASE_DIR.parent.parent.parent
    JSONLD_DIR = PROJECT_ROOT / 'database' / 'jsonld'
    VECTOR_DB_DIR = BASE_DIR / 'data' / 'vector_db'
    
    # LLM Configuration
    LLM_MODEL = os.environ.get('OLLAMA_MODEL', "llama3.1:8b-instruct-q8_0")
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'http://localhost:11434')
    
    # Embedding Configuration
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    EMBEDDING_DIMENSION = 384
    
    # Vector DB Configuration
    COLLECTION_NAME = 'demo_knowledge_graph'
    
    # Demo Port
    DEMO_PORT = int(os.environ.get('DEMO_PORT', 5001))
    
    # Ontology paths
    ONTOLOGY_DIR = PROJECT_ROOT / 'ontology'
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        cls.VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)