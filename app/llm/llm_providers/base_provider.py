from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """Abstract base class for LLM providers.
    
    This class defines the interface that all LLM provider implementations
    must follow, ensuring consistent behavior regardless of which underlying
    model or service is being used.
    """
    
    def __init__(self, config):
        """Initialize the provider with configuration.
        
        Args:
            config (dict): Configuration dictionary with provider-specific settings
        """
        self.config = config
        self.client = None
    
    @abstractmethod
    def initialize(self):
        """Initialize the LLM client for this provider.
        
        Returns:
            object: The initialized client
        """
        pass
    
    @abstractmethod
    def invoke(self, prompt, **kwargs):
        """Send a prompt to the LLM and get a response.
        
        Args:
            prompt (str): The prompt to send to the LLM
            **kwargs: Additional provider-specific parameters
            
        Returns:
            object: The response from the LLM
        """
        pass
    
    @abstractmethod
    def parse_response(self, response):
        """Parse the response from the LLM into a standard format.
        
        Args:
            response (object): The raw response from the LLM
            
        Returns:
            dict: The parsed response in a standard format
        """
        pass