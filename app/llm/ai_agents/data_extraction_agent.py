"""
DocEX Data Extraction Agent - Production Implementation
Model-capability-driven stakeholder extraction with automatic strategy selection
Supports GPT-4o, DeepSeek-V3, and Local Llama3.1 8B
"""
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

from app.llm.github_models_processor import GitHubModelsProcessor
from app.llm.ai_agents.local_llama_client import LocalLlamaClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Standardized extraction result across all models"""
    stakeholders: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    success: bool
    strategy_used: str
    model_used: str
    processing_time: float
    extraction_confidence: float
    cost_estimate: float = 0.0
    errors: List[str] = None


class DataExtractionAgent:
    """
    Production Data Extraction Agent with validated multi-model support
    Automatic strategy selection based on priority: cost|quality|speed|privacy
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Data Extraction Agent
        
        Args:
            config_path: Path to agents.yaml config file
        """
        self.config_path = config_path or Path(__file__).parent / "configs" / "agents.yaml"
        self.config = self._load_config()
        self.agent_config = self.config["agents"]["data_extraction_agent"]
        
        # Initialize processors
        self.github_processor = GitHubModelsProcessor()
        self.local_llama_client = LocalLlamaClient()
        
        # Load schemas and templates
        self.schemas = self._load_schemas()
        
        # Performance tracking
        self.performance_stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "strategy_usage": {},
            "model_usage": {},
            "total_cost": 0.0,
            "average_processing_time": 0.0
        }
        
        # Test model availability
        self._test_model_availability()
        
        logger.info(f"🧪 Data Extraction Agent initialized")
        logger.info(f"📊 Available strategies: {list(self.agent_config['model_strategies'].keys())}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration from YAML"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            raise
    
    def _load_schemas(self) -> Dict[str, Any]:
        """Load extraction schemas"""
        schemas = {}
        schema_dir = Path(__file__).parent / "configs" / "schemas"
        
        try:
            # Load GPT function calling schema
            function_schema_path = schema_dir / "stakeholder_function_schema.json"
            if function_schema_path.exists():
                with open(function_schema_path, 'r') as f:
                    schemas["function_calling"] = json.load(f)
                logger.info("✅ Function calling schema loaded")
            
            return schemas
            
        except Exception as e:
            logger.warning(f"⚠️ Schema loading warning: {e}")
            return {}
    
    def _test_model_availability(self) -> Dict[str, bool]:
        """Test availability of all configured models"""
        availability = {}
        
        # Test GitHub Models (GPT-4o and DeepSeek)
        try:
            test_result = self.github_processor.test_connection()
            availability["gpt-4o"] = test_result.get("status") == "connected"
            availability["deepseek/DeepSeek-V3-0324"] = availability["gpt-4o"]  # Same endpoint
            logger.info(f"✅ GitHub Models: {'connected' if availability['gpt-4o'] else 'failed'}")
        except Exception as e:
            availability["gpt-4o"] = False
            availability["deepseek/DeepSeek-V3-0324"] = False
            logger.warning(f"⚠️ GitHub Models unavailable: {e}")
        
        # Test Local Llama
        try:
            llama_status = self.local_llama_client.test_connection()
            availability["llama3.1:8b-instruct-q8_0"] = llama_status.get("status") == "connected"
            logger.info(f"✅ Local Llama: {'connected' if availability['llama3.1:8b-instruct-q8_0'] else 'failed'}")
        except Exception as e:
            availability["llama3.1:8b-instruct-q8_0"] = False
            logger.warning(f"⚠️ Local Llama unavailable: {e}")
        
        self.model_availability = availability
        
        # Log availability summary
        available_models = [model for model, available in availability.items() if available]
        logger.info(f"📊 Model availability:")
        for model, available in availability.items():
            status = "✅" if available else "❌"
            logger.info(f"   {status} {model}")
        
        return availability
    
    def extract_stakeholders(self, 
                           document_content: str,
                           document_title: str = "",
                           priority: str = "cost",
                           strategy: Optional[str] = None,
                           model: Optional[str] = None,
                           **kwargs) -> ExtractionResult:
        """
        Extract stakeholders from document content with intelligent model selection
        
        Args:
            document_content: The text content to analyze
            document_title: Optional document title for context
            priority: Extraction priority (cost|quality|speed|privacy)
            strategy: Override automatic strategy selection
            model: Override automatic model selection
            **kwargs: Additional parameters
            
        Returns:
            ExtractionResult with stakeholders and metadata
        """
        start_time = datetime.now()
        
        try:
            # Strategy and model selection
            selected_strategy = strategy or self._select_strategy(priority, model)
            selected_model = model or self._select_model(selected_strategy, priority)
            
            logger.info(f"🎯 Using strategy: {selected_strategy} with model: {selected_model}")
            logger.info(f"🎚️ Priority: {priority}")
            
            # Execute extraction based on strategy
            if selected_strategy == "native_structured":
                result = self._extract_native_structured(
                    document_content, document_title, selected_model, **kwargs
                )
            elif selected_strategy == "json_mode_guided":
                result = self._extract_json_mode_guided(
                    document_content, document_title, selected_model, **kwargs
                )
            elif selected_strategy == "ollama_structured":
                result = self._extract_ollama_structured(
                    document_content, document_title, selected_model, **kwargs
                )
            else:  # guided_json_prompting fallback
                result = self._extract_guided_json_prompting(
                    document_content, document_title, selected_model, **kwargs
                )
            
            # Calculate processing time and cost
            processing_time = (datetime.now() - start_time).total_seconds()
            cost_estimate = self._calculate_cost(selected_model, document_content, result)
            
            # Update result metadata
            result.processing_time = processing_time
            result.strategy_used = selected_strategy
            result.model_used = selected_model
            result.cost_estimate = cost_estimate
            
            # Update performance stats
            self._update_performance_stats(result)
            
            logger.info(f"✅ Extraction completed in {processing_time:.2f}s, cost: ${cost_estimate:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            
            # Try fallback if not already using fallback
            if selected_strategy != "guided_json_prompting":
                logger.info("🔄 Attempting fallback strategy...")
                return self._attempt_fallback(document_content, document_title, priority, **kwargs)
            
            # Return error result
            processing_time = (datetime.now() - start_time).total_seconds()
            return ExtractionResult(
                stakeholders=[],
                metadata={"error": str(e), "priority": priority},
                success=False,
                strategy_used=selected_strategy if 'selected_strategy' in locals() else "unknown",
                model_used=selected_model if 'selected_model' in locals() else "unknown",
                processing_time=processing_time,
                extraction_confidence=0.0,
                cost_estimate=0.0,
                errors=[str(e)]
            )
    
    def _select_strategy(self, priority: str, model: Optional[str] = None) -> str:
        """Select optimal extraction strategy based on priority"""
        
        # Priority-based selection with model availability check
        if priority == "quality" and self.model_availability.get("gpt-4o", False):
            return "native_structured"
        elif priority == "privacy" and self.model_availability.get("llama3.1:8b-instruct-q8_0", False):
            return "ollama_structured"
        elif priority in ["cost", "speed"] and self.model_availability.get("llama3.1:8b-instruct-q8_0", False):
            return "ollama_structured"  # Free and fast
        elif self.model_availability.get("deepseek/DeepSeek-V3-0324", False):
            return "json_mode_guided"  # Cheap cloud option
        elif self.model_availability.get("gpt-4o", False):
            return "native_structured"  # Premium fallback
        
        # Model-based selection if specified
        if model:
            for strategy_name, strategy_config in self.agent_config["model_strategies"].items():
                if model in strategy_config["applicable_models"]:
                    if self.model_availability.get(model, False):
                        return strategy_name
        
        # Default fallback
        return "guided_json_prompting"
    
    def _select_model(self, strategy: str, priority: str) -> str:
        """Select optimal model for strategy and priority"""
        
        strategy_config = self.agent_config["model_strategies"][strategy]
        available_models = [m for m in strategy_config["applicable_models"] 
                          if self.model_availability.get(m, False)]
        
        if not available_models:
            raise RuntimeError(f"No available models for strategy: {strategy}")
        
        # Priority-based model selection from available models
        if priority == "cost" and "llama3.1:8b-instruct-q8_0" in available_models:
            return "llama3.1:8b-instruct-q8_0"
        elif priority == "quality" and "openai/gpt-4o" in available_models:
            return "openai/gpt-4o"
        elif priority == "speed" and "deepseek/DeepSeek-V3-0324" in available_models:
            return "deepseek/DeepSeek-V3-0324"
        elif priority == "privacy" and "llama3.1:8b-instruct-q8_0" in available_models:
            return "llama3.1:8b-instruct-q8_0"
        
        # Return first available model
        return available_models[0]
    
    def _extract_native_structured(self, content: str, title: str, model: str, **kwargs) -> ExtractionResult:
        """Extract using native structured output (GPT-4o function calling)"""
        
        if "function_calling" not in self.schemas:
            raise ValueError("Function calling schema not loaded")
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert stakeholder analyst. Use the extract_stakeholders function to analyze documents with high precision."
            },
            {
                "role": "user",
                "content": f"Extract stakeholders from this document:\n\nTitle: {title}\n\nContent: {content}"
            }
        ]
        
        try:
            # Use validated function calling method
            response = self.github_processor.extract_with_function_calling(
                messages=messages,
                functions=[self.schemas["function_calling"]],
                model=model
            )
            
            # Validate response structure
            if "stakeholders" in response and "extraction_confidence" in response:
                return ExtractionResult(
                    stakeholders=response["stakeholders"],
                    metadata={
                        "extraction_confidence": response["extraction_confidence"],
                        "extraction_method": "function_calling",
                        "json_ld_compliant": "@type" in response.get("stakeholders", [{}])[0] if response.get("stakeholders") else False
                    },
                    success=True,
                    strategy_used="native_structured",
                    model_used=model,
                    processing_time=0.0,  # Will be set by caller
                    extraction_confidence=response["extraction_confidence"]
                )
            else:
                raise ValueError("Invalid response structure from function calling")
                
        except Exception as e:
            logger.error(f"Native structured extraction failed: {e}")
            raise
    
    def _extract_json_mode_guided(self, content: str, title: str, model: str, **kwargs) -> ExtractionResult:
        """Extract using JSON mode with guided prompting (DeepSeek)"""
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert stakeholder analyst. Extract stakeholders and return as valid JSON-LD.

REQUIRED JSON-LD FORMAT:
{
  "@context": {"@vocab": "https://docex.org/vocab/"},
  "@type": "StakeholderExtraction",
  "extractionMetadata": {
    "@type": "ExtractionMetadata",
    "extractionConfidence": 0.95,
    "extractorModel": "deepseek-v3"
  },
  "stakeholders": [
    {
      "@type": "Stakeholder",
      "@id": "stakeholder:unique-id",
      "name": "string",
      "role": "string",
      "stakeholderType": "INDIVIDUAL|GROUP|ORGANIZATIONAL",
      "confidenceScore": 0.3-1.0
    }
  ],
  "extractionConfidence": 0.0-1.0
}

IMPORTANT: Return ONLY valid JSON-LD, no other text."""
            },
            {
                "role": "user",
                "content": f"Extract stakeholders from this document:\n\nTitle: {title}\n\nContent: {content}"
            }
        ]
        
        try:
            # Use validated structured JSON method
            response = self.github_processor.extract_structured_json(
                messages=messages,
                model=model
            )
            
            # Handle response format
            if isinstance(response, str):
                parsed_response = json.loads(response)
            else:
                parsed_response = response
            
            # Validate response structure
            if "stakeholders" in parsed_response:
                extraction_confidence = parsed_response.get("extractionConfidence", 
                                                          parsed_response.get("extractionMetadata", {}).get("extractionConfidence", 0.8))
                
                return ExtractionResult(
                    stakeholders=parsed_response["stakeholders"],
                    metadata={
                        "extraction_confidence": extraction_confidence,
                        "extraction_method": "json_mode_guided",
                        "json_ld_compliant": "@context" in parsed_response and "@type" in parsed_response
                    },
                    success=True,
                    strategy_used="json_mode_guided",
                    model_used=model,
                    processing_time=0.0,  # Will be set by caller
                    extraction_confidence=extraction_confidence
                )
            else:
                raise ValueError("Invalid response structure from JSON mode")
                
        except Exception as e:
            logger.error(f"JSON mode guided extraction failed: {e}")
            raise
    
    def _extract_ollama_structured(self, content: str, title: str, model: str, **kwargs) -> ExtractionResult:
        """Extract using Ollama structured output (Local Llama3.1 8B)"""
        
        try:
            # Use the validated local Llama client
            llama_result = self.local_llama_client.extract_stakeholders_jsonld(
                document_content=content,
                document_title=title,
                temperature=kwargs.get("temperature", 0.1)
            )
            
            if llama_result["success"]:
                stakeholders = llama_result["stakeholders"]
                metadata = llama_result["metadata"]
                
                return ExtractionResult(
                    stakeholders=stakeholders,
                    metadata={
                        "extraction_confidence": metadata.get("extraction_confidence", 0.8),
                        "extraction_method": "ollama_structured",
                        "json_ld_compliant": metadata.get("json_ld_compliant", False)
                    },
                    success=True,
                    strategy_used="ollama_structured",
                    model_used=model,
                    processing_time=0.0,  # Will be set by caller
                    extraction_confidence=metadata.get("extraction_confidence", 0.8)
                )
            else:
                raise ValueError(f"Ollama extraction failed: {llama_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Ollama structured extraction failed: {e}")
            raise
    
    def _extract_guided_json_prompting(self, content: str, title: str, model: str, **kwargs) -> ExtractionResult:
        """Extract using guided JSON prompting (fallback method)"""
        
        # Simple fallback using available model
        if self.model_availability.get("llama3.1:8b-instruct-q8_0", False):
            # Use simple JSON extraction as fallback
            llama_result = self.local_llama_client.extract_simple_json(
                document_content=content,
                temperature=0.2
            )
            
            if llama_result["success"]:
                # Convert simple format to standard format
                stakeholders = []
                for stakeholder in llama_result["stakeholders"]:
                    stakeholders.append({
                        "name": stakeholder.get("name", "Unknown"),
                        "role": stakeholder.get("role", "Unknown"),
                        "stakeholderType": stakeholder.get("type", "INDIVIDUAL"),
                        "confidenceScore": 0.7
                    })
                
                return ExtractionResult(
                    stakeholders=stakeholders,
                    metadata={
                        "extraction_confidence": 0.7,
                        "extraction_method": "guided_json_prompting_fallback",
                        "json_ld_compliant": False
                    },
                    success=True,
                    strategy_used="guided_json_prompting",
                    model_used=model,
                    processing_time=0.0,
                    extraction_confidence=0.7
                )
            else:
                raise ValueError("Fallback extraction failed")
        else:
            raise RuntimeError("No available models for fallback extraction")
    
    def _attempt_fallback(self, content: str, title: str, priority: str, **kwargs) -> ExtractionResult:
        """Attempt fallback strategy chain"""
        
        fallback_chain = self.agent_config["strategy_selection"]["fallback_chain"]
        
        for strategy in fallback_chain:
            try:
                logger.info(f"🔄 Trying fallback strategy: {strategy}")
                return self.extract_stakeholders(
                    content, title, priority=priority, strategy=strategy, **kwargs
                )
            except Exception as e:
                logger.warning(f"⚠️ Fallback strategy {strategy} failed: {e}")
                continue
        
        # All fallbacks failed
        raise RuntimeError("All extraction strategies failed")
    
    def _calculate_cost(self, model: str, content: str, result: ExtractionResult) -> float:
        """Calculate estimated cost for the extraction"""
        
        # Local models are free
        if "llama" in model.lower() or "ollama" in model.lower():
            return 0.0
        
        # Estimate token count (rough approximation)
        input_tokens = len(content.split()) * 1.3  # Account for tokenization
        output_tokens = len(str(result.stakeholders)) * 1.3
        
        # GitHub Models pricing (estimated)
        if "gpt-4o" in model:
            # GPT-4o pricing: $2.50/1M input, $10/1M output
            cost = (input_tokens * 2.50 / 1_000_000) + (output_tokens * 10.0 / 1_000_000)
        elif "deepseek" in model.lower():
            # DeepSeek pricing: $0.27/1M input, $1.10/1M output
            cost = (input_tokens * 0.27 / 1_000_000) + (output_tokens * 1.10 / 1_000_000)
        else:
            cost = 0.0
        
        return cost
    
    def _update_performance_stats(self, result: ExtractionResult):
        """Update performance tracking statistics"""
        self.performance_stats["total_extractions"] += 1
        self.performance_stats["total_cost"] += result.cost_estimate
        
        if result.success:
            self.performance_stats["successful_extractions"] += 1
        
        # Update strategy usage
        strategy = result.strategy_used
        if strategy not in self.performance_stats["strategy_usage"]:
            self.performance_stats["strategy_usage"][strategy] = 0
        self.performance_stats["strategy_usage"][strategy] += 1
        
        # Update model usage
        model = result.model_used
        if model not in self.performance_stats["model_usage"]:
            self.performance_stats["model_usage"][model] = 0
        self.performance_stats["model_usage"][model] += 1
        
        # Update average processing time
        total = self.performance_stats["total_extractions"]
        current_avg = self.performance_stats["average_processing_time"]
        new_avg = ((current_avg * (total - 1)) + result.processing_time) / total
        self.performance_stats["average_processing_time"] = new_avg
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics report"""
        stats = self.performance_stats.copy()
        
        if stats["total_extractions"] > 0:
            stats["success_rate"] = stats["successful_extractions"] / stats["total_extractions"]
            stats["average_cost"] = stats["total_cost"] / stats["total_extractions"]
        else:
            stats["success_rate"] = 0.0
            stats["average_cost"] = 0.0
        
        # Find most used strategy
        if stats["strategy_usage"]:
            most_used_strategy = max(stats["strategy_usage"], key=stats["strategy_usage"].get)
        else:
            most_used_strategy = "None"
        
        return {
            "performance_stats": stats,
            "most_used_strategy": most_used_strategy,
            "model_availability": self.model_availability,
            "config_summary": {
                "available_strategies": list(self.agent_config["model_strategies"].keys()),
                "validated_models": [
                    "openai/gpt-4o",
                    "deepseek/DeepSeek-V3-0324", 
                    "llama3.1:8b-instruct-q8_0"
                ]
            }
        }


# Convenience functions for direct usage
def extract_stakeholders_with_privacy(document_content: str, 
                                    document_title: str = "",
                                    **kwargs) -> ExtractionResult:
    """Extract stakeholders using privacy-focused local processing only"""
    agent = DataExtractionAgent()
    return agent.extract_stakeholders(document_content, document_title, priority="privacy", **kwargs)


def extract_stakeholders_with_quality(document_content: str,
                                     document_title: str = "",
                                     **kwargs) -> ExtractionResult:
    """Extract stakeholders using highest quality model (GPT-4o)"""
    agent = DataExtractionAgent()
    return agent.extract_stakeholders(document_content, document_title, priority="quality", **kwargs)


def extract_stakeholders_with_cost_optimization(document_content: str,
                                               document_title: str = "",
                                               **kwargs) -> ExtractionResult:
    """Extract stakeholders using most cost-effective approach"""
    agent = DataExtractionAgent()
    return agent.extract_stakeholders(document_content, document_title, priority="cost", **kwargs)


def extract_stakeholders_from_document(document_content: str, 
                                     document_title: str = "",
                                     priority: str = "cost",
                                     **kwargs) -> ExtractionResult:
    """
    Main convenience function to extract stakeholders using the Data Extraction Agent
    
    Args:
        document_content: Text content to analyze
        document_title: Optional document title
        priority: Extraction priority (cost|quality|speed|privacy)
        **kwargs: Additional parameters (strategy, model, temperature, etc.)
        
    Returns:
        ExtractionResult with stakeholders and metadata
    """
    agent = DataExtractionAgent()
    return agent.extract_stakeholders(document_content, document_title, priority, **kwargs)


if __name__ == "__main__":
    # Test the complete agent
    test_content = """
    The NDIS Reform Project involves several key stakeholders. Dr. Emily Watson, 
    the Chief Policy Officer, leads the initiative. The Implementation Committee 
    provides oversight, while the Department of Social Services sponsors the project.
    Michael Chen from EnableMe Services represents service providers.
    """
    
    print("🧪 Testing Complete Data Extraction Agent")
    print("=" * 50)
    
    # Test all priority modes
    priorities = ["cost", "quality", "speed", "privacy"]
    
    for priority in priorities:
        print(f"\n🎯 Testing {priority} priority...")
        result = extract_stakeholders_from_document(test_content, "Test Document", priority)
        
        print(f"   Success: {result.success}")
        print(f"   Strategy: {result.strategy_used}")
        print(f"   Model: {result.model_used}")
        print(f"   Stakeholders: {len(result.stakeholders)}")
        print(f"   Cost: ${result.cost_estimate:.4f}")
        print(f"   Time: {result.processing_time:.2f}s")
        
        if result.stakeholders:
            print(f"   Example: {result.stakeholders[0].get('name')} ({result.stakeholders[0].get('stakeholderType')})")
    
    # Performance report
    agent = DataExtractionAgent()
    report = agent.get_performance_report()
    print(f"\n📊 Performance Summary:")
    print(f"   Available Models: {sum(report['model_availability'].values())}/{len(report['model_availability'])}")
    print(f"   Strategies: {len(report['config_summary']['available_strategies'])}")
    print(f"   Most Used Strategy: {report['most_used_strategy']}")