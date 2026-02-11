"""
Simple LLM client for testing extraction capabilities with enhanced error handling
"""
from app.config.config import get_llm_config, DEFAULT_LLM_PROVIDER
import json
import re
import logging
import requests
from typing import Dict, Any, Optional
from pathlib import Path

class LLMClient:
    """Lightweight client for direct LLM interaction via HTTP API"""
    
    def __init__(self, model=None, base_url="http://localhost:11434", timeout=1000):
        self.logger = logging.getLogger(__name__)
        self.model = model or "llama3.1:8b-instruct-q8_0"
        self.base_url = base_url
        self.timeout = timeout  # Set timeout in seconds (5 minutes default)
        self.logger.info(f"Initialized LLM client for model: {self.model} at {self.base_url} (timeout: {self.timeout}s)")
        
        # Default parameters optimized for extraction tasks
        self.default_params = {
            "temperature": 0.1,  # Low temperature for consistent extraction
            "max_tokens": 4000,  # Higher token limit for complex extractions
        }
    
    def analyze_text(self, prompt: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send text to LLM for analysis and return structured response"""
        request_params = self.default_params.copy()
        if params:
            request_params.update(params)
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,  # Important: set to False to get a complete response
            **request_params
        }
        
        self.logger.info(f"Sending request to {self.base_url}/api/generate with model {self.model}")
        
        try:
            start_time = __import__('time').time()
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout  # Use the configurable timeout
            )
            elapsed_time = __import__('time').time() - start_time
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse the JSON response
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                self.logger.error(f"Failed to parse response as JSON: {response.text[:100]}...")
                return {"error": "Failed to parse LLM response as JSON"}
            
            # Extract full text response
            full_text = response_json.get("response", "")
            
            self.logger.info(f"Received response in {elapsed_time:.2f}s, length: {len(full_text)} chars")
            
            if not full_text:
                self.logger.warning("Received empty response from LLM")
                return {"error": "Empty response from LLM", "debug_info": response_json}
                
            # Parse the response to extract structured data
            return self._parse_response(full_text)
            
        except requests.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}")
            return {"error": f"LLM request failed: {str(e)}"}
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Extract structured data from LLM response"""
        self.logger.debug("Parsing LLM response")
        
        # Look for JSON code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        
        if json_match:
            try:
                json_str = json_match.group(1).strip()
                parsed_json = json.loads(json_str)
                self.logger.info("Successfully parsed JSON from code block")
                return parsed_json
            except json.JSONDecodeError:
                self.logger.warning("Found JSON code block but failed to parse it")
        
        # Try to find any JSON-like content without code blocks
        try:
            # Look for content that might be JSON 
            potential_json = re.search(r'\{[\s\S]*\}', text)
            if potential_json:
                json_str = potential_json.group(0)
                parsed_json = json.loads(json_str)
                self.logger.info("Found and parsed JSON from response text")
                return parsed_json
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse potential JSON content")
        
        # If no JSON found, return the raw text
        self.logger.info("No JSON found in response, returning raw text")
        return {"raw_text": text}
    
    def test_connection(self):
        """Test connection to LLM API"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            if response.status_code == 200:
                version = response.json().get("version", "unknown")
                self.logger.info(f"Successfully connected to LLM API, version: {version}")
                return {"status": "connected", "version": version}
            else:
                self.logger.error(f"Failed to connect to LLM API, status: {response.status_code}")
                return {"status": "error", "code": response.status_code}
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return {"status": "error", "message": str(e)}



