import json
import re
import requests
from .base_provider import BaseProvider

class OllamaProvider(BaseProvider):
    """Simplified Ollama provider for extraction testing"""
    
    def initialize(self):
        """Initialize direct HTTP connection to Ollama"""
        self.base_url = self.config.get("base_url", "http://localhost:11434")
        self.model = self.config.get("model", "llama3.1:8b-instruct-q8_0")
        self.client = {"base_url": self.base_url, "model": self.model}
        return self.client
    
    def invoke(self, prompt, **kwargs):
        """Direct API call to Ollama for reliable testing"""
        params = {
            "model": self.model,
            "prompt": prompt,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000)
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=params,
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.RequestException as e:
            return f"Error: {str(e)}"
    
    def parse_response(self, response):
        """Extract structured data from response"""
        if isinstance(response, dict):
            return response
            
        # Extract JSON if present
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try finding any JSON content
        try:
            json_content = re.search(r'\{[\s\S]*\}', response)
            if json_content:
                return json.loads(json_content.group(0))
        except json.JSONDecodeError:
            pass
            
        return {"raw_text": response}