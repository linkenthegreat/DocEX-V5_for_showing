from .ollama_provider import OllamaProvider
from .github_provider import GitHubProvider
from app.config.config import get_llm_config

class LLMProviderFactory:
    """Factory for creating LLM provider instances"""
    
    @staticmethod
    def create_provider(provider_type: str, config=None):
        """Create an LLM provider instance based on type"""
        if provider_type == "ollama":
            if not config:
                config = {
                    "base_url": "http://localhost:11434",
                    "model": "llama3.1:8b-instruct-q8_0"
                }
            return OllamaProvider(config)
            
        elif provider_type == "github":
            if not config:
                # Get config from centralized config module
                config = get_llm_config('github')
            
            # Validate required keys
            required_keys = ["endpoint", "api_key", "model"]
            missing_keys = [key for key in required_keys if key not in config]
            
            if missing_keys:
                raise ValueError(f"GitHub provider requires these config keys: {missing_keys}")
            
            return GitHubProvider(config)
            
        else:
            raise ValueError(f"Unsupported provider: {provider_type}")

# Backward compatibility function
def create_provider(provider_type: str, config=None):
    """Create an LLM provider instance based on type (backward compatibility)"""
    return LLMProviderFactory.create_provider(provider_type, config)