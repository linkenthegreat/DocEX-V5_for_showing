
"""
JSON-LD Capability Test for Both GPT-4o and DeepSeek
Tests structured JSON-LD extraction capabilities for stakeholder analysis
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.github_models_processor import GitHubModelsProcessor


class JSONLDCapabilityTest:
    """Test JSON-LD capabilities for both GPT-4o and DeepSeek"""
    
    def __init__(self):
        self.processor = GitHubModelsProcessor()
        self.test_results = []
    
    def get_jsonld_schema_prompt(self) -> str:
        """Get the JSON-LD schema prompt for stakeholder extraction"""
        return """
You are an expert stakeholder analyst. Extract stakeholders and return as JSON-LD format.

est_jsonld_capabilities.pyREQUIRED JSON-LD FORMAT:
{
  "@context": {
    "@vocab": "https://docex.org/vocab/",
    "stakeholder": "https://docex.org/vocab/stakeholder/",
    "confidence": "https://docex.org/vocab/confidence/",
    "role": "https://docex.org/vocab/role/",
    "type": "https://docex.org/vocab/type/"
  },
  "@type": "StakeholderExtraction",
  "extractionMetadata": {
    "@type": "ExtractionMetadata",
    "extractionConfidence": 0.0-1.0,
    "extractionDate": "2025-01-08",
    "extractorModel": "model-name"
  },
  "stakeholders": [
    {
      "@type": "Stakeholder",
      "@id": "stakeholder:unique-id",
      "name": "string",
      "role": "string",
      "stakeholderType": "INDIVIDUAL|GROUP|ORGANIZATIONAL",
      "confidenceScore": 0.3-1.0,
      "mentions": [
        {
          "@type": "Mention",
          "text": "exact text from document",
          "context": "surrounding context"
        }
      ]
    }
  ]
}

IMPORTANT:
- Use valid JSON-LD with proper @context, @type, and @id
- Generate unique IDs for each stakeholder (e.g., "stakeholder:john-smith")
- Include extraction metadata
- Capture exact mentions from the text
- Return ONLY valid JSON-LD, no other text
"""
    
    def create_test_documents(self) -> list[Dict[str, str]]:
        """Create test documents for JSON-LD testing"""
        return [
            {
                "id": "test_simple_jsonld",
                "title": "Simple Stakeholder Document",
                "content": """
                The NDIS Reform Project involves key stakeholders. Dr. Emily Watson, the Chief Policy Officer, 
                leads the initiative. The Implementation Committee, consisting of 12 members, provides oversight. 
                The Department of Social Services sponsors the project, while Disability Services Australia 
                represents service providers. Local advocacy groups, including Rights4All Victoria, 
                ensure participant voice is heard.
                """
            },
            {
                "id": "test_complex_jsonld",
                "title": "Complex Multi-Entity Document",
                "content": """
                The National Disability Insurance Scheme Quality Review is a comprehensive evaluation 
                involving multiple stakeholders across government, industry, and community sectors.
                
                Government entities include the Department of Social Services (lead agency), 
                headed by Secretary Ms. Rachel Thompson, and the NDIS Quality and Safeguards Commission, 
                directed by Commissioner Prof. David Chen. Minister for Social Services, 
                The Hon. Amanda Foster MP, provides political oversight.
                
                Industry representatives encompass the Australian Disability Enterprise Network, 
                Community Care Providers Association, and individual providers like EnableMe Services 
                (CEO: Michael O'Brien) and Supportive Living Solutions.
                
                Community stakeholders include participant advocacy organizations such as 
                Disability Advocacy Network Australia (President: Sarah Mitchell), 
                family support groups, and individual participants. The Participant Advisory Committee, 
                co-chaired by James Rodriguez and Maria Gonzalez, ensures direct participant input.
                
                Research partners from the University of Sydney's Disability Research Institute, 
                led by Dr. Patricia Lee, provide evidence-based analysis.
                """
            }
        ]
    
    def test_gpt4o_jsonld_extraction(self) -> Dict[str, Any]:
        """Test GPT-4o JSON-LD extraction using function calling"""
        print("🧪 Testing GPT-4o JSON-LD Extraction...")
        
        try:
            test_doc = self.create_test_documents()[0]
            
            # Create JSON-LD function schema
            jsonld_function_schema = {
                "name": "extract_stakeholders_jsonld",
                "description": "Extract stakeholders in JSON-LD format with semantic annotations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "@context": {
                            "type": "object",
                            "description": "JSON-LD context definition"
                        },
                        "@type": {
                            "type": "string",
                            "description": "Root type identifier"
                        },
                        "extractionMetadata": {
                            "type": "object",
                            "properties": {
                                "@type": {"type": "string"},
                                "extractionConfidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                                "extractionDate": {"type": "string"},
                                "extractorModel": {"type": "string"}
                            },
                            "required": ["@type", "extractionConfidence", "extractionDate", "extractorModel"]
                        },
                        "stakeholders": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "@type": {"type": "string"},
                                    "@id": {"type": "string"},
                                    "name": {"type": "string"},
                                    "role": {"type": "string"},
                                    "stakeholderType": {
                                        "type": "string",
                                        "enum": ["INDIVIDUAL", "GROUP", "ORGANIZATIONAL"]
                                    },
                                    "confidenceScore": {"type": "number", "minimum": 0.3, "maximum": 1.0},
                                    "mentions": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "@type": {"type": "string"},
                                                "text": {"type": "string"},
                                                "context": {"type": "string"}
                                            },
                                            "required": ["@type", "text", "context"]
                                        }
                                    }
                                },
                                "required": ["@type", "@id", "name", "stakeholderType", "confidenceScore"]
                            }
                        }
                    },
                    "required": ["@context", "@type", "extractionMetadata", "stakeholders"]
                }
            }
            
            messages = [
                {
                    "role": "system",
                    "content": self.get_jsonld_schema_prompt()
                },
                {
                    "role": "user",
                    "content": f"Extract stakeholders in JSON-LD format from:\n\nTitle: {test_doc['title']}\n\nContent: {test_doc['content']}"
                }
            ]
            
            # Use GPT-4o function calling
            response = self.processor.extract_with_function_calling(
                messages=messages,
                functions=[jsonld_function_schema],
                model="gpt-4o"
            )
            
            validation = self._validate_jsonld_structure(response)
            
            return {
                "test": "gpt4o_jsonld_extraction",
                "model": "gpt-4o",
                "success": validation["is_valid_jsonld"],
                "response": response,
                "validation": validation
            }
            
        except Exception as e:
            return {
                "test": "gpt4o_jsonld_extraction",
                "model": "gpt-4o",
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def test_deepseek_jsonld_extraction(self) -> Dict[str, Any]:
        """Test DeepSeek JSON-LD extraction using structured prompting"""
        print("🔍 Testing DeepSeek JSON-LD Extraction...")
        
        try:
            test_doc = self.create_test_documents()[0]
            
            messages = [
                {
                    "role": "system",
                    "content": self.get_jsonld_schema_prompt()
                },
                {
                    "role": "user",
                    "content": f"""Extract stakeholders in JSON-LD format from this document:

Title: {test_doc['title']}

Content: {test_doc['content']}

Remember to:
1. Use proper JSON-LD structure with @context, @type, @id
2. Generate unique IDs for each stakeholder
3. Include extraction metadata with model name "deepseek/DeepSeek-V3-0324"
4. Capture exact mentions from the text
5. Return ONLY valid JSON-LD"""
                }
            ]
            
            # Use DeepSeek structured JSON
            response = self.processor.extract_structured_json(
                messages=messages,
                model="deepseek/DeepSeek-V3-0324"
            )
            
            # Handle response format
            if isinstance(response, str):
                parsed_response = json.loads(response)
            else:
                parsed_response = response
            
            validation = self._validate_jsonld_structure(parsed_response)
            
            return {
                "test": "deepseek_jsonld_extraction",
                "model": "deepseek/DeepSeek-V3-0324",
                "success": validation["is_valid_jsonld"],
                "response": parsed_response,
                "validation": validation
            }
            
        except Exception as e:
            return {
                "test": "deepseek_jsonld_extraction",
                "model": "deepseek/DeepSeek-V3-0324",
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def test_complex_document_comparison(self) -> Dict[str, Any]:
        """Test both models on complex document with many stakeholders"""
        print("🔄 Testing Complex Document - Model Comparison...")
        
        try:
            test_doc = self.create_test_documents()[1]  # Complex document
            
            base_messages = [
                {
                    "role": "system", 
                    "content": self.get_jsonld_schema_prompt()
                },
                {
                    "role": "user",
                    "content": f"Extract all stakeholders in JSON-LD format from this complex document:\n\n{test_doc['content']}"
                }
            ]
            
            # Test GPT-4o with structured JSON (simpler than function calling for comparison)
            gpt4o_response = self.processor.extract_structured_json(
                messages=base_messages,
                model="gpt-4o"
            )
            
            # Test DeepSeek
            deepseek_response = self.processor.extract_structured_json(
                messages=base_messages,
                model="deepseek/DeepSeek-V3-0324"
            )
            
            # Parse responses
            if isinstance(gpt4o_response, str):
                gpt4o_parsed = json.loads(gpt4o_response)
            else:
                gpt4o_parsed = gpt4o_response
                
            if isinstance(deepseek_response, str):
                deepseek_parsed = json.loads(deepseek_response)
            else:
                deepseek_parsed = deepseek_response
            
            # Validate both
            gpt4o_validation = self._validate_jsonld_structure(gpt4o_parsed)
            deepseek_validation = self._validate_jsonld_structure(deepseek_parsed)
            
            # Compare results
            comparison = self._compare_jsonld_results(gpt4o_parsed, deepseek_parsed)
            
            return {
                "test": "complex_document_comparison",
                "success": gpt4o_validation["is_valid_jsonld"] and deepseek_validation["is_valid_jsonld"],
                "gpt4o_result": {
                    "validation": gpt4o_validation,
                    "stakeholder_count": len(gpt4o_parsed.get("stakeholders", [])),
                    "response": gpt4o_parsed
                },
                "deepseek_result": {
                    "validation": deepseek_validation,
                    "stakeholder_count": len(deepseek_parsed.get("stakeholders", [])),
                    "response": deepseek_parsed
                },
                "comparison": comparison
            }
            
        except Exception as e:
            return {
                "test": "complex_document_comparison",
                "success": False,
                "error": str(e)
            }
    
    def test_jsonld_semantic_features(self) -> Dict[str, Any]:
        """Test semantic features specific to JSON-LD"""
        print("🔗 Testing JSON-LD Semantic Features...")
        
        try:
            # Test with document containing relationships
            test_content = """
            The NDIS Review Committee is chaired by Prof. Angela Davis from Griffith University. 
            The committee includes Dr. Michael Chen (disability researcher), 
            Sarah Williams (participant advocate), and Tom Johnson representing service providers. 
            The committee reports to Minister Janet Roberts, who oversees the Department of 
            Social Services through Secretary Amanda Foster.
            """
            
            messages = [
                {
                    "role": "system",
                    "content": self.get_jsonld_schema_prompt() + """

ADDITIONAL SEMANTIC REQUIREMENTS:
- Include organizational relationships where possible
- Add semantic links between related stakeholders
- Use proper JSON-LD linking with @id references
- Include additional semantic properties:
  * "affiliatedWith": "@id reference to organization"
  * "reportsTo": "@id reference to supervisor"
  * "memberOf": "@id reference to group/committee"
"""
                },
                {
                    "role": "user",
                    "content": f"Extract stakeholders with semantic relationships in JSON-LD format:\n\n{test_content}"
                }
            ]
            
            # Test with GPT-4o (more likely to handle complex semantic features)
            response = self.processor.extract_structured_json(
                messages=messages,
                model="gpt-4o"
            )
            
            if isinstance(response, str):
                parsed_response = json.loads(response)
            else:
                parsed_response = response
            
            semantic_validation = self._validate_semantic_features(parsed_response)
            
            return {
                "test": "jsonld_semantic_features",
                "success": semantic_validation["has_semantic_features"],
                "response": parsed_response,
                "semantic_validation": semantic_validation
            }
            
        except Exception as e:
            return {
                "test": "jsonld_semantic_features",
                "success": False,
                "error": str(e)
            }
    
    def _validate_jsonld_structure(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON-LD structure"""
        validation = {
            "has_context": "@context" in response,
            "has_type": "@type" in response,
            "has_extraction_metadata": "extractionMetadata" in response,
            "has_stakeholders": "stakeholders" in response,
            "stakeholders_is_list": isinstance(response.get("stakeholders", []), list),
            "stakeholder_count": len(response.get("stakeholders", []))
        }
        
        # Validate stakeholders have proper JSON-LD structure
        stakeholders = response.get("stakeholders", [])
        if stakeholders:
            first_stakeholder = stakeholders[0]
            validation.update({
                "stakeholder_has_type": "@type" in first_stakeholder,
                "stakeholder_has_id": "@id" in first_stakeholder,
                "stakeholder_has_name": "name" in first_stakeholder,
                "stakeholder_has_role": "role" in first_stakeholder,
                "stakeholder_has_type_enum": "stakeholderType" in first_stakeholder
            })
        
        # Overall validation
        validation["is_valid_jsonld"] = all([
            validation["has_context"],
            validation["has_type"], 
            validation["has_stakeholders"],
            validation["stakeholders_is_list"]
        ])
        
        return validation
    
    def _validate_semantic_features(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate semantic features in JSON-LD"""
        stakeholders = response.get("stakeholders", [])
        
        semantic_features = {
            "has_id_references": any("@id" in s for s in stakeholders),
            "has_relationships": any(
                any(key in s for key in ["affiliatedWith", "reportsTo", "memberOf"]) 
                for s in stakeholders
            ),
            "has_mentions": any("mentions" in s for s in stakeholders),
            "has_context_vocab": isinstance(response.get("@context", {}), dict),
            "proper_namespace_usage": "@vocab" in response.get("@context", {})
        }
        
        semantic_features["has_semantic_features"] = any(semantic_features.values())
        
        return semantic_features
    
    def _compare_jsonld_results(self, gpt4o_result: Dict[str, Any], deepseek_result: Dict[str, Any]) -> Dict[str, Any]:
        """Compare JSON-LD results between models"""
        gpt4o_stakeholders = {s.get("name", "") for s in gpt4o_result.get("stakeholders", [])}
        deepseek_stakeholders = {s.get("name", "") for s in deepseek_result.get("stakeholders", [])}
        
        return {
            "gpt4o_count": len(gpt4o_stakeholders),
            "deepseek_count": len(deepseek_stakeholders),
            "common_stakeholders": list(gpt4o_stakeholders.intersection(deepseek_stakeholders)),
            "gpt4o_unique": list(gpt4o_stakeholders - deepseek_stakeholders),
            "deepseek_unique": list(deepseek_stakeholders - gpt4o_stakeholders),
            "overlap_percentage": len(gpt4o_stakeholders.intersection(deepseek_stakeholders)) / max(len(gpt4o_stakeholders), len(deepseek_stakeholders), 1),
            "jsonld_quality_comparison": {
                "gpt4o_has_proper_context": "@context" in gpt4o_result,
                "deepseek_has_proper_context": "@context" in deepseek_result,
                "gpt4o_has_metadata": "extractionMetadata" in gpt4o_result,
                "deepseek_has_metadata": "extractionMetadata" in deepseek_result
            }
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all JSON-LD capability tests"""
        print("🚀 Starting JSON-LD Capability Tests...")
        print("=" * 50)
        
        test_results = {}
        
        # Test 1: GPT-4o JSON-LD extraction
        test_results["gpt4o_jsonld_extraction"] = self.test_gpt4o_jsonld_extraction()
        
        # Test 2: DeepSeek JSON-LD extraction
        test_results["deepseek_jsonld_extraction"] = self.test_deepseek_jsonld_extraction()
        
        # Test 3: Complex document comparison
        test_results["complex_document_comparison"] = self.test_complex_document_comparison()
        
        # Test 4: Semantic features
        test_results["jsonld_semantic_features"] = self.test_jsonld_semantic_features()
        
        # Summary
        successful_tests = sum(1 for result in test_results.values() if result["success"])
        total_tests = len(test_results)
        
        summary = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests,
            "overall_success": successful_tests >= 3  # Allow 1 failure
        }
        
        print(f"\n📊 JSON-LD Test Summary:")
        print(f"   ✅ Successful: {successful_tests}/{total_tests}")
        print(f"   📈 Success Rate: {summary['success_rate']:.1%}")
        print(f"   🎯 Overall: {'PASS' if summary['overall_success'] else 'FAIL'}")
        
        return {
            "summary": summary,
            "test_results": test_results,
            "timestamp": "2025-01-08T10:00:00Z"
        }


def main():
    """Run JSON-LD capability tests"""
    print("🧪 JSON-LD Capability Test for GPT-4o and DeepSeek")
    print("Testing semantic structured data extraction")
    print("=" * 60)
    
    tester = JSONLDCapabilityTest()
    
    try:
        results = tester.run_all_tests()
        
        # Save results
        results_path = Path(__file__).parent / "jsonld_capability_test_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_path}")
        
        return 0 if results["summary"]["overall_success"] else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)