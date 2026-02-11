"""
GitHub Models LLM Processor for structured stakeholder extraction

This module provides integration with GitHub Models SDK for accessing
various LLM providers including GPT, Deepseek, and other hosted models.
"""

import os
import json
import re
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class GitHubModelsProcessor:
    """
    Processor for GitHub Models SDK integration supporting multiple LLM providers
    """
    
    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the GitHub Models processor"""
        self.endpoint = endpoint or os.getenv('GITHUB_ENDPOINT', 'https://models.github.ai/inference')
        self.api_key = api_key or os.getenv('GITHUB_API_KEY')
        
        if not self.api_key:
            raise ValueError("GitHub API key is required. Set GITHUB_API_KEY environment variable.")
        
        # Initialize clients
        self._init_clients()
        
        # Model configurations
        self.models = {
            'gpt-4o-mini': {
                'provider': 'openai',
                'max_tokens': 4000,
                'temperature': 0.1,
                'supports_json': True
            },
            'gpt-4o': {
                'provider': 'openai', 
                'max_tokens': 4000,
                'temperature': 0.1,
                'supports_json': True
            },
            'deepseek-chat': {
                'provider': 'azure',
                'max_tokens': 4000,
                'temperature': 0.1,
                'supports_json': True
            },
            'deepseek/DeepSeek-V3-0324': {
                'provider': 'azure',
                'max_tokens': 4000,
                'temperature': 0.1,
                'supports_json': True
            },
            'Meta-Llama-3.1-405B-Instruct': {
                'provider': 'azure',
                'max_tokens': 4000,
                'temperature': 0.1,
                'supports_json': False
            }
        }
        
        logger.info(f"Initialized GitHub Models processor with endpoint: {self.endpoint}")
    
    def _init_clients(self):
        """Initialize the different client types"""
        # OpenAI-compatible client for GPT models
        self.openai_client = OpenAI(
            base_url=self.endpoint,
            api_key=self.api_key
        )
        
        # Azure AI client for other models
        self.azure_client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.api_key)
        )
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        return list(self.models.keys())
    
    def call_gpt_model(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini", 
                      **kwargs) -> str:
        """
        Call GPT models through OpenAI-compatible interface
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use
            **kwargs: Additional parameters
            
        Returns:
            Response content as string
        """
        # Handle different model name formats
        actual_model = model
        if model.startswith("openai/"):
            actual_model = model.replace("openai/", "")
        
        if actual_model not in self.models or self.models[actual_model]['provider'] != 'openai':
            raise ValueError(f"Model {model} not supported for OpenAI interface. Available OpenAI models: {[k for k, v in self.models.items() if v['provider'] == 'openai']}")
        
        model_config = self.models[actual_model]
        
        try:
            response = self.openai_client.chat.completions.create(
                model=actual_model,  # Use cleaned model name
                messages=messages,
                temperature=kwargs.get('temperature', model_config['temperature']),
                max_tokens=kwargs.get('max_tokens', model_config['max_tokens']),
                top_p=kwargs.get('top_p', 1.0),
                response_format=kwargs.get('response_format', None)
            )
            
            content = response.choices[0].message.content
            logger.info(f"Successfully called {model}, response length: {len(content)} chars")
            return content
            
        except Exception as e:
            logger.error(f"Error calling {model}: {str(e)}")
            raise
    
    def call_azure_model(self, messages: List[Dict[str, str]], model: str = "deepseek-chat",
                        **kwargs) -> str:
        """
        Call Azure-hosted models (Deepseek, Llama, etc.)
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'  
            model: Model name to use
            **kwargs: Additional parameters
            
        Returns:
            Response content as string
        """
        if model not in self.models or self.models[model]['provider'] != 'azure':
            raise ValueError(f"Model {model} not supported for Azure interface")
        
        model_config = self.models[model]
        
        # Convert messages to Azure format
        azure_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                azure_messages.append(SystemMessage(content=msg['content']))
            elif msg['role'] == 'user':
                azure_messages.append(UserMessage(content=msg['content']))
            # Note: Azure format may need adjustment for assistant messages
        
        try:
            response = self.azure_client.complete(
                messages=azure_messages,
                model=model,
                temperature=kwargs.get('temperature', model_config['temperature']),
                max_tokens=kwargs.get('max_tokens', model_config['max_tokens']),
                top_p=kwargs.get('top_p', 1.0)
            )
            
            content = response.choices[0].message.content
            logger.info(f"Successfully called {model}, response length: {len(content)} chars")
            return content
            
        except Exception as e:
            logger.error(f"Error calling {model}: {str(e)}")
            raise
    
    def call_model(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini",
                  **kwargs) -> str:
        """
        Universal model calling interface that routes to appropriate client
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use  
            **kwargs: Additional parameters
            
        Returns:
            Response content as string
        """
        if model not in self.models:
            raise ValueError(f"Model {model} not supported. Available: {list(self.models.keys())}")
        
        provider = self.models[model]['provider']
        
        if provider == 'openai':
            return self.call_gpt_model(messages, model, **kwargs)
        elif provider == 'azure':
            return self.call_azure_model(messages, model, **kwargs)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def extract_structured_json(self, messages: List[Dict[str, str]], model: str = "gpt-4o-mini",
                               schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Extract structured JSON output from model response
        
        Args:
            messages: List of message dictionaries
            model: Model to use
            schema: Optional JSON schema for structured output
            
        Returns:
            Parsed JSON response
        """
        model_config = self.models.get(model, {})
        
        # For models that support structured JSON output
        if model_config.get('supports_json') and schema:
            kwargs = {
                'response_format': {
                    'type': 'json_object'
                }
            }
        else:
            kwargs = {}
        
        # Add instruction for JSON output in the system message if not already present
        if messages and messages[0]['role'] == 'system':
            if 'JSON' not in messages[0]['content']:
                messages[0]['content'] += "\n\nIMPORTANT: Return your response as valid JSON only."
        else:
            messages.insert(0, {
                'role': 'system',
                'content': 'You are a helpful assistant. Return your response as valid JSON only.'
            })
        
        response_text = self.call_model(messages, model, **kwargs)
        
        # Parse JSON response
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            else:
                # If no JSON found, try parsing the entire response
                return json.loads(response_text)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {model} response: {str(e)}")
            logger.debug(f"Response text: {response_text[:500]}...")
            
            # Return structured error response
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response_text,
                "model": model
            }
    
    def test_connection(self, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """
        Test connection to a specific model
        
        Args:
            model: Model to test
            
        Returns:
            Test result dictionary
        """
        test_messages = [
            {
                "role": "system", 
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": "Say 'Hello, I am working!' in JSON format with a 'message' field."
            }
        ]
        
        try:
            result = self.extract_structured_json(test_messages, model)
            return {
                "status": "success",
                "model": model,
                "response": result
            }
        except Exception as e:
            return {
                "status": "error", 
                "model": model,
                "error": str(e)
            }
    
    def extract_with_function_calling(self, messages: List[Dict[str, str]], 
                                      functions: List[Dict[str, Any]], 
                                      model: str = "gpt-4o",
                                      **kwargs) -> Dict[str, Any]:
        """
        Extract data using GPT function calling (tools)
        
        Args:
            messages: List of message dictionaries
            functions: List of function definitions
            model: Model to use (must support function calling)
            **kwargs: Additional parameters
            
        Returns:
            Function call result as dictionary
        """
        # Handle different model name formats
        actual_model = model
        if model.startswith("openai/"):
            actual_model = model.replace("openai/", "")
        
        # Check if model supports function calling (OpenAI models)
        if actual_model not in self.models or self.models[actual_model]['provider'] != 'openai':
            raise ValueError(f"Model {model} does not support function calling. Available OpenAI models: {[k for k, v in self.models.items() if v['provider'] == 'openai']}")
        
        model_config = self.models[actual_model]
        
        # Convert functions to tools format for OpenAI API
        tools = [
            {
                "type": "function",
                "function": func
            }
            for func in functions
        ]
        
        try:
            response = self.openai_client.chat.completions.create(
                model=actual_model,  # Use the cleaned model name
                messages=messages,
                tools=tools,
                tool_choice="auto",  # Let model decide when to call function
                temperature=kwargs.get('temperature', model_config['temperature']),
                max_tokens=kwargs.get('max_tokens', model_config['max_tokens']),
                top_p=kwargs.get('top_p', 1.0)
            )
            
            # Extract function call result
            message = response.choices[0].message
            
            if message.tool_calls:
                # Function was called
                tool_call = message.tool_calls[0]
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Function {tool_call.function.name} called successfully")
                return function_args
            else:
                # No function call, return regular response
                logger.warning("No function call made, returning regular response")
                return {
                    "error": "No function call made",
                    "response": message.content,
                    "model": model
                }
                
        except Exception as e:
            logger.error(f"Error in function calling with {model}: {str(e)}")
            raise
    
    def extract_with_structured_output(self, messages: List[Dict[str, str]], 
                                      schema: Dict[str, Any],
                                      model: str = "gpt-4o",
                                      **kwargs) -> Dict[str, Any]:
        """
        Extract data using GPT structured output (response_format)
        This is the newer OpenAI approach that might be more reliable
        
        Args:
            messages: List of message dictionaries
            schema: JSON schema for structured output
            model: Model to use (must support structured outputs)
            **kwargs: Additional parameters
            
        Returns:
            Structured response as dictionary
        """
        # Handle different model name formats
        actual_model = model
        if model.startswith("openai/"):
            actual_model = model.replace("openai/", "")
        
        if actual_model not in self.models or self.models[actual_model]['provider'] != 'openai':
            raise ValueError(f"Model {model} does not support structured output")
        
        model_config = self.models[actual_model]
        
        try:
            response = self.openai_client.chat.completions.create(
                model=actual_model,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.get("name", "extraction_result"),
                        "description": schema.get("description", "Structured extraction result"),
                        "schema": schema.get("parameters", schema)
                    }
                },
                temperature=kwargs.get('temperature', model_config['temperature']),
                max_tokens=kwargs.get('max_tokens', model_config['max_tokens']),
                top_p=kwargs.get('top_p', 1.0)
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            logger.info(f"Structured output extraction successful")
            return result
            
        except Exception as e:
            logger.error(f"Error in structured output with {model}: {str(e)}")
            raise


# Convenience function for backward compatibility
def create_processor() -> GitHubModelsProcessor:
    """Create a GitHubModelsProcessor instance with default settings"""
    return GitHubModelsProcessor()


# Test function
def test_github_models():
    """Test function to verify GitHub Models integration"""
    processor = create_processor()
    
    print("🧪 Testing GitHub Models Integration")
    print("=" * 40)
    
    # Test GPT model
    print("Testing GPT-4o-mini...")
    gpt_result = processor.test_connection("gpt-4o-mini")
    print(f"GPT Result: {gpt_result}")
    
    # Test Deepseek model (if available)
    print("\nTesting Deepseek...")
    deepseek_result = processor.test_connection("deepseek-chat")
    print(f"Deepseek Result: {deepseek_result}")


if __name__ == "__main__":
    test_github_models()
