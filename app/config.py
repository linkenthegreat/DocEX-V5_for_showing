import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def config_env():
    """Load environment configuration"""
    # Basic environment configuration for testing
    os.environ.setdefault("OLLAMA_MODEL", "llama3.1:8b-instruct-q8_0")
    os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Return environment for testing
    return {
        "ENVIRONMENT": os.environ.get("ENV", "development"),
        "LLM_PROVIDER": os.environ.get("DEFAULT_LLM_PROVIDER", "ollama")
    }

class Config:
    '''Set Flask configuration variables.'''
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')

    # Directory paths
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    CSV_FILE = os.path.join(DATABASE_DIR, 'System_files_metadata.csv')
    TRIPLES_DIR = os.path.join(DATABASE_DIR, 'triples')
    
    # API Keys and endpoints
    GITHUB_API_KEY = os.getenv('GITHUB_API_KEY')
    AZURE_AI_ENDPOINT = os.getenv('AZURE_AI_ENDPOINT')

    #LLM Configuration
    MODEL_NAME = os.getenv('MODEL_NAME')
    LLM_API_KEY = os.getenv('LLM_API_KEY')
    LLM_PROVIDER = os.getenv('anthropic')

    #Vector Database Configuration
    VECTOR_DB_URL = os.getenv('QDRANT_URL')
    VECTOR_DB_COLLECTION = os.getenv('QDRANT_COLLECTION')

    #Embedding Model Configuration
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')
    
    # LLM Configuration
    DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "ollama")

    def get_llm_config(provider=None):
        """Get configuration for specified LLM provider"""
        provider = provider or Config.DEFAULT_LLM_PROVIDER
        
        if provider == "ollama":
            return {
                "provider": "ollama",
                "model": os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q8_0"),
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                "temperature": 0.1,
                "max_tokens": 2000
            }
        elif provider == "openai":
            return {
                "provider": "openai",
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "temperature": 0.1,
                "max_tokens": 2000
            }
        elif provider == "github":
            return {
                "provider": "github",
                "model": os.getenv("GITHUB_MODEL", "gpt-4o-mini"),
                "api_key": os.getenv("GITHUB_API_KEY", ""),
                "endpoint": os.getenv("GITHUB_ENDPOINT", "https://models.github.ai/inference"),
                "temperature": 0.1,
                "max_tokens": 2000,
                "available_models": [
                    "gpt-4o",
                    "gpt-4o-mini", 
                    "deepseek-chat",
                    "deepseek/DeepSeek-V3-0324",
                    "Meta-Llama-3.1-8B-Instruct",
                    "Meta-Llama-3.1-70B-Instruct",
                    "Meta-Llama-3.1-405B-Instruct"
                ]
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    # Verify the directories exist
    @staticmethod
    def init_app(app):
        os.makedirs(os.path.dirname(Config.CSV_FILE), exist_ok=True)
        os.makedirs(Config.TRIPLES_DIR, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    # Add development-specific settings here


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    # Add testing-specific settings here


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # In production, you might want to use a stronger secret key
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY') or 'hard-to-guess-secret'
    # Add production-specific settings here


# Using config_env instead of config
config_env = {
    'development': DevelopmentConfig,
    'testing': TestingConfig, 
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

"""
Configuration Module

This module defines configuration classes for different environments (development,
testing, production) and loads environment variables from the .env file.

Classes:
    Config: Base configuration class with settings common to all environments
    DevelopmentConfig: Configuration settings for development environment
    TestingConfig: Configuration settings for testing environment
    ProductionConfig: Configuration settings for production environment

The configuration is selected based on the FLASK_ENV environment variable.
"""