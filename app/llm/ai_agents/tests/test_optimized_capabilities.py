
"""
Optimized Multi-Model Capability Test
Single document set, all models, comparative results
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.github_models_processor import GitHubModelsProcessor
from app.llm.llm_client import LLMClient


class OptimizedCapabilityTest:
    """Efficient testing across all models with single document set"""
    
    def __init__(self):
        self.github_processor = GitHubModelsProcessor()
        self.llm_client = LLMClient()
        
        # Single optimized test document (instead of 3-4 per test)
        self.test_document = {
            "title": "NDIS Quality and Safeguards Review",
            "content": """
            The NDIS Quality and Safeguards Commission Review involves multiple stakeholders 
            across government, industry, and community sectors.
            
            Government: Department of Social Services (lead agency), NDIS Quality and 
            Safeguards Commission (Commissioner Prof. David Chen), Minister Amanda Foster.
            
            Industry: Australian Disability Enterprise Network, EnableMe Services (CEO: Michael O'Brien).
            
            Community: Disability Advocacy Network Australia (President: Sarah Mitchell), 
            Participant Advisory Committee (co-chaired by James Rodriguez and Maria Gonzalez).
            
            Research: University of Sydney Disability Research Institute (Dr. Patricia Lee).
            """
        }
    
    def test_all_models_jsonld(self) -> Dict[str, Any]:
        """Test JSON-LD extraction across all available models"""
        
        results = {}
        
        # GPT-4o Function Calling
        print("🧪 Testing GPT-4o Function Calling...")
        results["gpt4o"] = self._test_gpt4o_function_calling()
        
        # DeepSeek JSON Mode  
        print("🧪 Testing DeepSeek JSON Mode...")
        results["deepseek"] = self._test_deepseek_json_mode()
        
        # Llama3.1 8B Structured
        print("🧪 Testing Llama3.1 8B...")
        results["llama31"] = self._test_llama_structured()
        
        return results
    
    def _get_jsonld_prompt(self) -> str:
        """Standard JSON-LD prompt for all models"""
        return f"""Extract stakeholders in JSON-LD format from this document:

Title: {self.test_document['title']}
Content: {self.test_document['content']}

Return valid JSON-LD:
{{
  "@context": {{"@vocab": "https://docex.org/vocab/"}},
  "@type": "StakeholderExtraction",
  "extractionMetadata": {{
    "@type": "ExtractionMetadata",
    "extractionConfidence": 0.0-1.0,
    "extractorModel": "model-name"
  }},
  "stakeholders": [
    {{
      "@type": "Stakeholder", 
      "@id": "stakeholder:unique-id",
      "name": "string",
      "role": "string",
      "stakeholderType": "INDIVIDUAL|GROUP|ORGANIZATIONAL",
      "confidenceScore": 0.3-1.0
    }}
  ]
}}"""
    
    def _test_gpt4o_function_calling(self) -> Dict[str, Any]:
        """Test GPT-4o with function calling"""
        try:
            messages = [
                {"role": "system", "content": "Extract stakeholders using JSON-LD format."},
                {"role": "user", "content": self._get_jsonld_prompt()}
            ]
            
            response = self.github_processor.extract_structured_json(
                messages=messages,
                model="gpt-4o"
            )
            
            # Parse and validate
            if isinstance(response, str):
                parsed = json.loads(response)
            else:
                parsed = response
                
            return {
                "success": True,
                "model": "gpt-4o",
                "method": "structured_json",
                "stakeholder_count": len(parsed.get("stakeholders", [])),
                "json_ld_compliant": "@context" in parsed and "@type" in parsed,
                "response": parsed
            }
            
        except Exception as e:
            return {"success": False, "model": "gpt-4o", "error": str(e)}
    
    def _test_deepseek_json_mode(self) -> Dict[str, Any]:
        """Test DeepSeek with JSON mode"""
        try:
            messages = [
                {"role": "system", "content": "Extract stakeholders using JSON-LD format. Return only valid JSON."},
                {"role": "user", "content": self._get_jsonld_prompt()}
            ]
            
            response = self.github_processor.extract_structured_json(
                messages=messages,
                model="deepseek/DeepSeek-V3-0324"
            )
            
            # Parse and validate
            if isinstance(response, str):
                parsed = json.loads(response)
            else:
                parsed = response
                
            return {
                "success": True,
                "model": "deepseek/DeepSeek-V3-0324",
                "method": "json_mode",
                "stakeholder_count": len(parsed.get("stakeholders", [])),
                "json_ld_compliant": "@context" in parsed and "@type" in parsed,
                "response": parsed
            }
            
        except Exception as e:
            return {"success": False, "model": "deepseek/DeepSeek-V3-0324", "error": str(e)}
    
    def _test_llama_structured(self) -> Dict[str, Any]:
        """Test Llama3.1 8B with structured output"""
        try:
            prompt = self._get_jsonld_prompt()
            
            # Try structured output first
            try:
                response = self.llm_client.call_ollama_structured(
                    prompt=prompt,
                    model="llama3.1:8b-instruct-q8_0",
                    format="json"
                )
            except:
                # Fallback to regular call
                response = self.llm_client.call_ollama(
                    prompt=prompt,
                    model="llama3.1:8b-instruct-q8_0"
                )
            
            # Parse and validate
            parsed = json.loads(response)
                
            return {
                "success": True,
                "model": "llama3.1:8b-instruct-q8_0", 
                "method": "ollama_structured",
                "stakeholder_count": len(parsed.get("stakeholders", [])),
                "json_ld_compliant": "@context" in parsed and "@type" in parsed,
                "response": parsed
            }
            
        except Exception as e:
            return {"success": False, "model": "llama3.1:8b-instruct-q8_0", "error": str(e)}
    
    def generate_comparison_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive comparison report"""
        
        successful_models = [k for k, v in results.items() if v.get("success")]
        
        comparison = {
            "test_summary": {
                "total_models": len(results),
                "successful_models": len(successful_models),
                "success_rate": len(successful_models) / len(results)
            },
            "model_comparison": {},
            "recommendations": {}
        }
        
        # Compare successful models
        for model_name, result in results.items():
            if result.get("success"):
                comparison["model_comparison"][model_name] = {
                    "stakeholders_extracted": result.get("stakeholder_count", 0),
                    "json_ld_compliant": result.get("json_ld_compliant", False),
                    "method": result.get("method", "unknown")
                }
        
        # Generate recommendations
        if "gpt4o" in successful_models and "deepseek" in successful_models:
            comparison["recommendations"]["production"] = "Use DeepSeek for cost, GPT-4o for quality"
        elif "gpt4o" in successful_models:
            comparison["recommendations"]["production"] = "GPT-4o only (DeepSeek failed)"
        elif "deepseek" in successful_models:
            comparison["recommendations"]["production"] = "DeepSeek only (GPT-4o failed)"
        
        if "llama31" in successful_models:
            comparison["recommendations"]["privacy"] = "Llama3.1 8B available for sensitive documents"
        else:
            comparison["recommendations"]["privacy"] = "No local model available - use cloud with caution"
        
        return comparison


def main():
    """Run optimized capability test"""
    print("🧪 Optimized Multi-Model JSON-LD Capability Test")
    print("=" * 55)
    
    tester = OptimizedCapabilityTest()
    
    print(f"📄 Test Document: {tester.test_document['title']}")
    print(f"📊 Expected: ~8-10 stakeholders")
    print()
    
    # Run all tests
    results = tester.test_all_models_jsonld()
    
    # Generate report
    report = tester.generate_comparison_report(results)
    
    # Display results
    print("\n📊 Results Summary:")
    print(f"   ✅ Successful: {report['test_summary']['successful_models']}/{report['test_summary']['total_models']}")
    print(f"   📈 Success Rate: {report['test_summary']['success_rate']:.1%}")
    
    print("\n🎯 Model Performance:")
    for model, comparison in report["model_comparison"].items():
        stakeholders = comparison["stakeholders_extracted"] 
        compliant = "✅" if comparison["json_ld_compliant"] else "❌"
        print(f"   {model}: {stakeholders} stakeholders, JSON-LD: {compliant}")
    
    print("\n💡 Recommendations:")
    for category, recommendation in report["recommendations"].items():
        print(f"   {category.title()}: {recommendation}")
    
    # Save detailed results
    results_path = Path(__file__).parent / "optimized_capability_results.json"
    with open(results_path, 'w') as f:
        json.dump({"results": results, "report": report}, f, indent=2)
    
    print(f"\n💾 Detailed results: {results_path}")
    
    return report["test_summary"]["success_rate"] >= 0.5  # At least 50% success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)