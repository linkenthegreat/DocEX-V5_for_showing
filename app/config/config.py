import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Configuration
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "ollama")
AVAILABLE_PROVIDERS = ["ollama", "github"]

# Provider-specific configurations
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q8_0")

# Placeholder for new model integration

GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
GITHUB_MODEL = os.getenv("GITHUB_MODEL")
GITHUB_ENDPOINT = os.getenv("GITHUB_ENDPOINT", "https://models.github.ai/inference")
# Vector Database Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "stakeholder_embeddings")

# Embedding Model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# Document Processing Configuration
MAX_CHUNK_SIZE = 8000  # Characters per chunk
CHUNK_OVERLAP = 200

def get_llm_config(provider=None):
    """Get configuration for specified LLM provider"""
    provider = provider or DEFAULT_LLM_PROVIDER
    
    if provider not in AVAILABLE_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    if provider == "ollama":
        # Existing ollama config...
        return {
            "provider": "ollama", 
            "model": OLLAMA_MODEL,
            "base_url": OLLAMA_BASE_URL
        }
    elif provider == "github":
        # Existing github config...
        return {
            "provider": "github",
            "model": GITHUB_MODEL,
            "api_key": GITHUB_API_KEY,
            "endpoint": GITHUB_ENDPOINT
        }


class Config:
    """
    Configuration class for DocEX application.
    Provides centralized access to all configuration settings.
    """
    
    # Simple secret key for PoC - not for production!
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-not-for-production')
    
    def __init__(self):
        # Database paths
        self.DATABASE_PATH = os.getenv("DATABASE_PATH", "database")
        
        # LLM Configuration
        self.DEFAULT_LLM_PROVIDER = DEFAULT_LLM_PROVIDER
        self.AVAILABLE_PROVIDERS = AVAILABLE_PROVIDERS
        
        # Ollama settings
        self.OLLAMA_BASE_URL = OLLAMA_BASE_URL
        self.OLLAMA_MODEL = OLLAMA_MODEL
        
        # GitHub/OpenAI settings
        self.GITHUB_API_KEY = GITHUB_API_KEY
        self.GITHUB_MODEL = GITHUB_MODEL
        self.GITHUB_ENDPOINT = GITHUB_ENDPOINT
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        # Vector Database
        self.QDRANT_URL = QDRANT_URL
        self.QDRANT_COLLECTION = QDRANT_COLLECTION
        
        # Embedding settings
        self.EMBEDDING_MODEL = EMBEDDING_MODEL
        
        # Document processing
        self.MAX_CHUNK_SIZE = MAX_CHUNK_SIZE
        self.CHUNK_OVERLAP = CHUNK_OVERLAP
    
    def get_llm_config(self, provider=None):
        """Get configuration for specified LLM provider"""
        return get_llm_config(provider)

    @staticmethod
    def init_app(app):
        """Initialize application directories"""
        import os
        from pathlib import Path
        
        base_dir = app.config.get('BASE_DIR', os.getcwd())
        directories = [
            app.config.get('DATABASE_DIR', os.path.join(base_dir, 'database')),
            app.config.get('TRIPLES_DIR', os.path.join(base_dir, 'database', 'triples')),
            app.config.get('JSONLD_DIR', os.path.join(base_dir, 'database', 'jsonld'))
        ]
        
        for directory in directories:
            if directory:
                os.makedirs(directory, exist_ok=True)
                print(f"📁 Ensured directory exists: {directory}")

