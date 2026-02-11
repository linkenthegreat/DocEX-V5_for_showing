import re
import json
from typing import Dict, Any, Optional
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from app.config.config import get_llm_config
from .base_provider import BaseProvider

class GitHubProvider(BaseProvider):
    """GitHub AI provider for DeepSeek models - Using config only"""
    
    def __init__(self, config=None):
        # Call parent constructor
        super().__init__(config or {})
        
        # Get config from centralized config module if not provided
        if not config:
            self.config = get_llm_config('github')
        
        # Extract configuration
        self.model = self.config.get('model')
        self.token = self.config.get('api_key')
        self.endpoint = self.config.get('endpoint')
        
        # Validate required parameters
        if not self.token:
            raise ValueError("GitHub API key is required. Check GITHUB_API_KEY in .env or config.")
        if not self.endpoint:
            raise ValueError("GitHub endpoint is required. Check GITHUB_ENDPOINT in .env or config.")
        if not self.model:
            raise ValueError("GitHub model is required. Check GITHUB_MODEL in .env or config.")
    
    def initialize(self):
        """Initialize the GitHub client"""
        try:
            self.client = ChatCompletionsClient(
                endpoint=self.endpoint,
                credential=AzureKeyCredential(self.token),
            )
            return self.client
        except Exception as e:
            raise RuntimeError(f"Failed to initialize GitHub client: {e}")
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """Send prompt to GitHub's LLM API and get response"""
        if not self.client:
            self.initialize()
            
        try:
            system_message = kwargs.get("system_message", 
                                      "You are a helpful AI assistant specialized in extracting structured data from text.")
            
            # Send request using Azure SDK
            response = self.client.complete(
                messages=[
                    SystemMessage(content=system_message),
                    UserMessage(content=prompt),
                ],
                temperature=kwargs.get("temperature", 0.1),
                max_tokens=kwargs.get("max_tokens", 2000),
                model=self.model
            )
            
            # Extract content from response
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            return "Error: Unexpected response format"
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def parse_response(self, response: str) -> Dict[str, Any]:
        """Parse response from GitHub AI into structured data"""
        if response.startswith("Error:"):
            return {"error": response}
            
        # Extract JSON if present
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON-like content
        try:
            json_pattern = re.compile(r'(\{[\s\S]*\})')
            match = json_pattern.search(response)
            if match:
                return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
            
        # Return raw text if no JSON found
        return {"content": response}