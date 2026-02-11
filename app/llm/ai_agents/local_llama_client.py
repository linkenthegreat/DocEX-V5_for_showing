
"""
Dedicated Local Llama Client for Agent Integration
Clean, reliable interface for Llama3.1 8B JSON-LD extraction
"""
import json
import re
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalLlamaClient:
    """
    Purpose-built client for local Llama3.1 8B integration
    Optimized for JSON-LD stakeholder extraction
    """
    
    def __init__(self, 
                 base_url: str = "http://localhost:11434",
                 model: str = "llama3.1:8b-instruct-q8_0",
                 timeout: int = 600):
        """
        Initialize Local Llama client
        
        Args:
            base_url: Ollama server URL
            model: Llama model identifier  
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.session = requests.Session()
        
        logger.info(f"🦙 Local Llama client initialized: {model}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to local Ollama server"""
        try:
            response = self.session.get(f"{self.base_url}/api/version", timeout=5)
            response.raise_for_status()
            
            version_data = response.json()
            
            return {
                "status": "connected",
                "version": version_data.get("version", "unknown"),
                "model_available": self._check_model_availability()
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _check_model_availability(self) -> bool:
        """Check if the specified model is available"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            models_data = response.json()
            available_models = [model["name"] for model in models_data.get("models", [])]
            
            return self.model in available_models
        except Exception:
            return False
    
    def extract_stakeholders_jsonld(self, 
                                  document_content: str,
                                  document_title: str = "",
                                  temperature: float = 0.1) -> Dict[str, Any]:
        """
        Extract stakeholders in JSON-LD format using local Llama
        
        Args:
            document_content: Text to analyze
            document_title: Optional document title
            temperature: Generation temperature (0.1 for consistency)
            
        Returns:
            Dict with extraction results
        """
        
        # Optimized prompt for Llama JSON-LD generation
        prompt = self._build_jsonld_prompt(document_content, document_title)
        
        try:
            # Make request to Ollama
            response_data = self._make_ollama_request(prompt, temperature)
            
            # Extract and validate JSON-LD
            jsonld_result = self._extract_and_validate_jsonld(response_data)
            
            return {
                "success": True,
                "extraction_method": "local_llama_jsonld",
                "model": self.model,
                "stakeholders": jsonld_result.get("stakeholders", []),
                "metadata": {
                    "extraction_confidence": jsonld_result.get("extractionConfidence", 0.7),
                    "json_ld_compliant": self._validate_jsonld_structure(jsonld_result),
                    "extraction_date": datetime.now().isoformat(),
                    "document_title": document_title
                }
            }
            
        except Exception as e:
            logger.error(f"🦙 Local Llama extraction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "extraction_method": "local_llama_jsonld",
                "model": self.model
            }
    
    def _build_jsonld_prompt(self, content: str, title: str) -> str:
        """Build optimized JSON-LD prompt for Llama"""
        
        prompt = f"""You are a stakeholder analysis expert. Extract stakeholders from this document and return ONLY valid JSON-LD.

Document Title: {title}
Document Content:
{content}

CRITICAL INSTRUCTIONS:
1. Return ONLY the JSON object below - NO explanations, NO markdown, NO extra text
2. Use this EXACT format:

{{
  "@context": {{"@vocab": "https://docex.org/vocab/"}},
  "@type": "StakeholderExtraction",
  "extractionMetadata": {{
    "@type": "ExtractionMetadata",
    "extractionConfidence": 0.8,
    "extractorModel": "llama3.1-8b"
  }},
  "stakeholders": [
    {{
      "@type": "Stakeholder",
      "@id": "stakeholder:unique-name",
      "name": "Stakeholder Name",
      "role": "Their role or responsibility",
      "stakeholderType": "INDIVIDUAL",
      "confidenceScore": 0.9
    }}
  ],
  "extractionConfidence": 0.8
}}

STAKEHOLDER TYPES: Use exactly "INDIVIDUAL", "GROUP", or "ORGANIZATIONAL"
CONFIDENCE: Use values between 0.3 and 1.0

Extract all identifiable stakeholders. Return ONLY the JSON - nothing else."""

        return prompt
    
    def _make_ollama_request(self, prompt: str, temperature: float) -> Dict[str, Any]:
        """Make request to Ollama API with error handling"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 2000,  # Max tokens
                "stop": ["</s>", "Human:", "Assistant:"]  # Stop sequences
            }
        }
        
        logger.info(f"🦙 Making request to {self.base_url}/api/generate")
        
        response = self.session.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        return response.json()
    
    def _extract_and_validate_jsonld(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and validate JSON-LD from Ollama response"""
        
        # Get response text
        response_text = response_data.get("response", "").strip()
        
        if not response_text:
            raise ValueError("Empty response from Ollama")
        
        logger.debug(f"🦙 Raw response length: {len(response_text)} chars")
        
        # Try to extract JSON from response
        json_data = self._extract_json_from_text(response_text)
        
        if not json_data:
            raise ValueError(f"No valid JSON found in response: {response_text[:200]}...")
        
        # Validate JSON-LD structure
        if not self._validate_jsonld_structure(json_data):
            logger.warning("🦙 Response is valid JSON but not proper JSON-LD structure")
        
        return json_data
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from potentially messy text response"""
        
        # Method 1: Direct JSON parsing if clean
        try:
            if text.startswith('{') and text.endswith('}'):
                return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Method 2: Find JSON in text using regex
        json_patterns = [
            r'\{[\s\S]*\}',  # Basic JSON pattern
            r'```(?:json)?\s*(\{[\s\S]*?\})\s*```',  # JSON in code blocks
            r'(?:^|\n)\s*(\{[\s\S]*?\})\s*(?:\n|$)'  # JSON on its own lines
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    json_str = match.group(1) if match.groups() else match.group(0)
                    json_str = json_str.strip()
                    
                    # Try to parse
                    parsed = json.loads(json_str)
                    
                    # Check if it looks like our expected structure
                    if isinstance(parsed, dict) and ("stakeholders" in parsed or "@type" in parsed):
                        logger.info("🦙 Successfully extracted JSON from text")
                        return parsed
                        
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _validate_jsonld_structure(self, data: Dict[str, Any]) -> bool:
        """Validate JSON-LD structure compliance"""
        
        required_fields = ["@context", "@type", "stakeholders"]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                return False
        
        # Check stakeholder structure
        stakeholders = data.get("stakeholders", [])
        if not isinstance(stakeholders, list):
            return False
        
        # Validate stakeholder fields
        for stakeholder in stakeholders:
            if not isinstance(stakeholder, dict):
                return False
            
            required_stakeholder_fields = ["@type", "name", "stakeholderType"]
            for field in required_stakeholder_fields:
                if field not in stakeholder:
                    return False
        
        return True
    
    def extract_simple_json(self, 
                           document_content: str,
                           temperature: float = 0.1) -> Dict[str, Any]:
        """
        Simple JSON extraction (fallback method)
        """
        
        prompt = f"""Extract stakeholders from this text and return as JSON:

{document_content}

Return only this JSON format:
{{
  "stakeholders": [
    {{
      "name": "Person or Organization Name",
      "role": "Their role", 
      "type": "INDIVIDUAL or GROUP or ORGANIZATIONAL"
    }}
  ]
}}

Return ONLY the JSON, nothing else."""

        try:
            response_data = self._make_ollama_request(prompt, temperature)
            response_text = response_data.get("response", "").strip()
            
            json_data = self._extract_json_from_text(response_text)
            
            if json_data and "stakeholders" in json_data:
                return {
                    "success": True,
                    "stakeholders": json_data["stakeholders"],
                    "extraction_method": "local_llama_simple"
                }
            else:
                raise ValueError("No valid stakeholder JSON found")
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "extraction_method": "local_llama_simple"
            }


# Convenience functions
def test_local_llama_connection() -> Dict[str, Any]:
    """Test connection to local Llama"""
    client = LocalLlamaClient()
    return client.test_connection()


def extract_stakeholders_local(document_content: str, 
                             document_title: str = "",
                             use_jsonld: bool = True) -> Dict[str, Any]:
    """
    Extract stakeholders using local Llama
    
    Args:
        document_content: Text to analyze
        document_title: Optional title
        use_jsonld: Whether to use JSON-LD format (default) or simple JSON
        
    Returns:
        Extraction results
    """
    client = LocalLlamaClient()
    
    if use_jsonld:
        return client.extract_stakeholders_jsonld(document_content, document_title)
    else:
        return client.extract_simple_json(document_content)


if __name__ == "__main__":
    # Test the local Llama client
    print("🧪 Testing Local Llama Client")
    print("=" * 35)
    
    # Connection test
    connection = test_local_llama_connection()
    print(f"Connection: {connection}")
    
    if connection.get("status") == "connected":
        # Extraction test
        test_content = """
        The NDIS Review is led by Dr. Sarah Mitchell, Chief Policy Officer. 
        The Implementation Committee oversees progress, while Disability Australia 
        advocates for participants.
        """
        
        result = extract_stakeholders_local(test_content, "NDIS Review Test")
        print(f"\nExtraction Success: {result.get('success')}")
        
        if result.get('success'):
            stakeholders = result.get('stakeholders', [])
            print(f"Stakeholders found: {len(stakeholders)}")
            for stakeholder in stakeholders:
                print(f"  - {stakeholder.get('name')}")