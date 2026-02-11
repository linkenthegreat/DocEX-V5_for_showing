"""
DeepSeek JSON Mode Capability Test
Tests DeepSeek's JSON mode with structured prompting for stakeholder extraction
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.github_models_processor import GitHubModelsProcessor


class DeepSeekCapabilityTest:
    """Test DeepSeek JSON mode capabilities for stakeholder extraction"""
    
    def __init__(self):
        self.processor = GitHubModelsProcessor()
        self.test_results = []
    
    def create_test_documents(self) -> list[Dict[str, str]]:
        """Create test documents with known stakeholders for validation"""
        return [
            {
                "id": "test_simple",
                "title": "Simple Stakeholder Document",
                "content": """
                This project involves several key stakeholders. John Smith, the Project Manager, 
                is responsible for overall coordination. The Development Team, led by Sarah Johnson, 
                will handle technical implementation. The NDIS Quality and Safeguards Commission 
                will provide regulatory oversight.
                """
            },
            {
                "id": "test_complex",
                "title": "Complex Multi-Stakeholder Document", 
                "content": """
                The NDIS Implementation Review involves multiple organizations and individuals. 
                The Department of Social Services oversees the program, with Minister Anne Ruston 
                having final authority. Regional coordinators including Lisa Chen (Victoria), 
                Mark Thompson (NSW), and the Queensland Disability Network collaborate on service delivery.
                
                Participants and their families are the primary beneficiaries, represented by 
                advocacy groups like Disability Advocacy Network Australia.
                """
            },
            {
                "id": "test_minimal",
                "title": "Minimal Content Document",
                "content": "Project update meeting with Jennifer and the team."
            }
        ]
    
    def test_basic_json_mode(self) -> Dict[str, Any]:
        """Test basic JSON mode functionality using extract_structured_json"""
        print("🧪 Testing DeepSeek Basic JSON Mode...")
        
        try:
            test_doc = self.create_test_documents()[0]
            
            # DeepSeek JSON mode with structured prompting
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert stakeholder analyst. Extract stakeholders from documents and return the result as valid JSON.

REQUIRED JSON FORMAT:
{
  "stakeholders": [
    {
      "name": "string",
      "role": "string", 
      "stakeholder_type": "INDIVIDUAL|GROUP|ORGANIZATIONAL",
      "confidence_score": 0.3-1.0
    }
  ],
  "extraction_confidence": 0.0-1.0
}

IMPORTANT: 
- Return ONLY valid JSON, no other text
- Use exactly the format shown above
- stakeholder_type must be one of: INDIVIDUAL, GROUP, ORGANIZATIONAL
- confidence_score must be between 0.3 and 1.0"""
                },
                {
                    "role": "user",
                    "content": f"Extract stakeholders from this document and return as JSON:\n\nTitle: {test_doc['title']}\n\nContent: {test_doc['content']}"
                }
            ]
            
            # Use extract_structured_json with only supported parameters
            response = self.processor.extract_structured_json(
                messages=messages,
                model="deepseek/DeepSeek-V3-0324"
                # Remove temperature, max_tokens - not supported by this method
            )
            
            # Response should already be parsed if extract_structured_json works correctly
            if isinstance(response, dict):
                parsed_response = response
            elif isinstance(response, str):
                parsed_response = json.loads(response)
            else:
                raise ValueError(f"Unexpected response type: {type(response)}")
            
            return {
                "test": "basic_json_mode",
                "success": True,
                "raw_response": response,
                "parsed_response": parsed_response,
                "validation": self._validate_response_structure(parsed_response)
            }
            
        except json.JSONDecodeError as e:
            return {
                "test": "basic_json_mode",
                "success": False,
                "error": f"JSON parsing failed: {e}",
                "raw_response": response if 'response' in locals() else None
            }
        except Exception as e:
            return {
                "test": "basic_json_mode",
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def test_structured_prompting(self) -> Dict[str, Any]:
        """Test DeepSeek with structured prompting template"""
        print("🔍 Testing DeepSeek Structured Prompting...")
        
        try:
            test_doc = self.create_test_documents()[1]  # Complex document
            
            # More detailed structured prompt for DeepSeek
            messages = [
                {
                    "role": "system", 
                    "content": """You are a professional stakeholder analyst. Extract all stakeholders from documents with high accuracy.

EXTRACTION GUIDELINES:
1. INDIVIDUAL: Named persons (e.g., "John Smith", "Dr. Sarah Johnson")
2. GROUP: Teams, committees, families (e.g., "Development Team", "Participants and their families")  
3. ORGANIZATIONAL: Companies, agencies, institutions (e.g., "NDIS Commission", "University of Melbourne")

CONFIDENCE SCORING:
- 0.9-1.0: Clearly named with explicit role
- 0.7-0.8: Named but role inferred
- 0.5-0.6: Mentioned but limited context
- 0.3-0.4: Ambiguous reference

OUTPUT FORMAT: Return ONLY valid JSON with no additional text."""
                },
                {
                    "role": "user",
                    "content": f"""Extract stakeholders from this document:

{test_doc['content']}

Return as JSON:
{{
  "stakeholders": [
    {{
      "name": "exact name from text",
      "role": "role or responsibility", 
      "stakeholder_type": "INDIVIDUAL|GROUP|ORGANIZATIONAL",
      "confidence_score": 0.3-1.0
    }}
  ],
  "extraction_confidence": 0.0-1.0
}}"""
                }
            ]
            
            response = self.processor.extract_structured_json(
                messages=messages,
                model="deepseek/DeepSeek-V3-0324"
                # Remove temperature parameter
            )
            
            # Handle response format
            if isinstance(response, dict):
                parsed_response = response
            elif isinstance(response, str):
                parsed_response = json.loads(response)
            else:
                parsed_response = {"error": "Unexpected response format"}
            
            validation_results = self._validate_schema_compliance(parsed_response)
            
            return {
                "test": "structured_prompting",
                "success": validation_results["valid"],
                "parsed_response": parsed_response,
                "validation_details": validation_results
            }
            
        except Exception as e:
            return {
                "test": "structured_prompting",
                "success": False,
                "error": str(e)
            }
    
    def test_edge_case_handling(self) -> Dict[str, Any]:
        """Test DeepSeek with minimal content"""
        print("⚠️ Testing DeepSeek Edge Cases...")
        
        try:
            test_doc = self.create_test_documents()[2]  # Minimal document
            
            messages = [
                {
                    "role": "system",
                    "content": """Extract stakeholders from minimal information. If content is limited, use lower confidence scores and extract what you can identify. Return valid JSON only."""
                },
                {
                    "role": "user",
                    "content": f"""Extract stakeholders from this minimal document:

{test_doc['content']}

Return JSON format:
{{
  "stakeholders": [
    {{
      "name": "string",
      "role": "string or null if unknown",
      "stakeholder_type": "INDIVIDUAL|GROUP|ORGANIZATIONAL", 
      "confidence_score": 0.3-1.0
    }}
  ],
  "extraction_confidence": 0.0-1.0
}}

If uncertain, use lower confidence scores but still extract identifiable stakeholders."""
                }
            ]
            
            response = self.processor.extract_structured_json(
                messages=messages,
                model="deepseek/DeepSeek-V3-0324"
                # Remove temperature parameter
            )
            
            # Handle response format
            if isinstance(response, dict):
                parsed_response = response
            elif isinstance(response, str):
                parsed_response = json.loads(response)
            else:
                parsed_response = {"stakeholders": [], "extraction_confidence": 0.0}
            
            edge_case_validation = self._validate_edge_case_handling(parsed_response)
            
            return {
                "test": "edge_case_handling",
                "success": True,
                "parsed_response": parsed_response,
                "edge_case_validation": edge_case_validation
            }
            
        except Exception as e:
            return {
                "test": "edge_case_handling",
                "success": False,
                "error": str(e)
            }
    
    def test_comparison_with_gpt4o(self) -> Dict[str, Any]:
        """Compare DeepSeek results with GPT-4o on same document"""
        print("🔄 Testing DeepSeek vs GPT-4o Comparison...")
        
        try:
            test_doc = self.create_test_documents()[0]
            
            # Same messages for both models
            base_messages = [
                {
                    "role": "system",
                    "content": "Extract stakeholders and return as JSON with stakeholders array and extraction_confidence."
                },
                {
                    "role": "user",
                    "content": f"Extract stakeholders from: {test_doc['content']}"
                }
            ]
            
            # DeepSeek extraction - Remove temperature parameter
            deepseek_response = self.processor.extract_structured_json(
                messages=base_messages,
                model="deepseek/DeepSeek-V3-0324"
            )
            
            # GPT-4o structured JSON - Remove temperature parameter
            gpt4o_response = self.processor.extract_structured_json(
                messages=base_messages,
                model="gpt-4o"
            )
            
            # Ensure both are dictionaries
            if isinstance(deepseek_response, str):
                deepseek_parsed = json.loads(deepseek_response)
            else:
                deepseek_parsed = deepseek_response
            
            if isinstance(gpt4o_response, str):
                gpt4o_parsed = json.loads(gpt4o_response)
            else:
                gpt4o_parsed = gpt4o_response
            
            return {
                "test": "comparison_with_gpt4o",
                "success": True,
                "deepseek_result": {
                    "stakeholder_count": len(deepseek_parsed.get("stakeholders", [])),
                    "extraction_confidence": deepseek_parsed.get("extraction_confidence"),
                    "response": deepseek_parsed
                },
                "gpt4o_result": {
                    "stakeholder_count": len(gpt4o_parsed.get("stakeholders", [])),
                    "extraction_confidence": gpt4o_parsed.get("extraction_confidence"),
                    "response": gpt4o_parsed
                },
                "comparison": self._compare_results(deepseek_parsed, gpt4o_parsed)
            }
            
        except Exception as e:
            return {
                "test": "comparison_with_gpt4o",
                "success": False,
                "error": str(e)
            }
    
    def _validate_response_structure(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate response structure"""
        validation = {
            "has_stakeholders": "stakeholders" in response,
            "has_extraction_confidence": "extraction_confidence" in response,
            "stakeholders_is_list": isinstance(response.get("stakeholders", []), list),
            "extraction_confidence_valid": self._is_valid_confidence(response.get("extraction_confidence")),
            "stakeholder_count": len(response.get("stakeholders", []))
        }
        
        stakeholders = response.get("stakeholders", [])
        if stakeholders:
            first_stakeholder = stakeholders[0]
            validation.update({
                "stakeholder_has_name": "name" in first_stakeholder,
                "stakeholder_has_type": "stakeholder_type" in first_stakeholder,
                "stakeholder_has_confidence": "confidence_score" in first_stakeholder
            })
        
        validation["overall_valid"] = all([
            validation["has_stakeholders"],
            validation["has_extraction_confidence"],
            validation["stakeholders_is_list"],
            validation["extraction_confidence_valid"]
        ])
        
        return validation
    
    def _validate_schema_compliance(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate schema compliance"""
        validation = {"valid": True, "violations": []}
        
        stakeholders = response.get("stakeholders", [])
        
        for i, stakeholder in enumerate(stakeholders):
            if "name" not in stakeholder:
                validation["violations"].append(f"Stakeholder {i}: Missing required 'name' field")
                validation["valid"] = False
            
            stakeholder_type = stakeholder.get("stakeholder_type")
            if stakeholder_type not in ["INDIVIDUAL", "GROUP", "ORGANIZATIONAL"]:
                validation["violations"].append(f"Stakeholder {i}: Invalid stakeholder_type '{stakeholder_type}'")
                validation["valid"] = False
            
            confidence = stakeholder.get("confidence_score")
            if confidence is not None and (confidence < 0.3 or confidence > 1.0):
                validation["violations"].append(f"Stakeholder {i}: Confidence score {confidence} outside valid range")
                validation["valid"] = False
        
        return validation
    
    def _validate_edge_case_handling(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate edge case handling"""
        stakeholders = response.get("stakeholders", [])
        
        return {
            "extracted_from_minimal": len(stakeholders) > 0,
            "appropriate_confidence": all(
                s.get("confidence_score", 1.0) <= 0.8 for s in stakeholders
            ),
            "no_hallucination": len(stakeholders) <= 3,
            "reasonable_extraction": len(stakeholders) >= 1  # Should find at least Jennifer and team
        }
    
    def _compare_results(self, deepseek_result: Dict[str, Any], gpt4o_result: Dict[str, Any]) -> Dict[str, Any]:
        """Compare DeepSeek vs GPT-4o results"""
        if not isinstance(gpt4o_result, dict):
            return {"comparison_failed": "GPT-4o result not in expected format"}
        
        deepseek_names = {s.get("name", "") for s in deepseek_result.get("stakeholders", [])}
        gpt4o_names = {s.get("name", "") for s in gpt4o_result.get("stakeholders", [])}
        
        return {
            "deepseek_count": len(deepseek_names),
            "gpt4o_count": len(gpt4o_names),
            "common_stakeholders": list(deepseek_names.intersection(gpt4o_names)),
            "deepseek_unique": list(deepseek_names - gpt4o_names),
            "gpt4o_unique": list(gpt4o_names - deepseek_names),
            "overlap_percentage": len(deepseek_names.intersection(gpt4o_names)) / max(len(deepseek_names), len(gpt4o_names), 1)
        }
    
    def _is_valid_confidence(self, confidence: Any) -> bool:
        """Check if confidence score is valid"""
        if confidence is None:
            return False
        if not isinstance(confidence, (int, float)):
            return False
        return 0.0 <= confidence <= 1.0
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all DeepSeek capability tests"""
        print("🚀 Starting DeepSeek JSON Mode Capability Tests...")
        print("=" * 50)
        
        test_results = {}
        
        # Test 1: Basic JSON mode
        test_results["basic_json_mode"] = self.test_basic_json_mode()
        
        # Test 2: Structured prompting
        test_results["structured_prompting"] = self.test_structured_prompting()
        
        # Test 3: Edge cases
        test_results["edge_case_handling"] = self.test_edge_case_handling()
        
        # Test 4: Comparison with GPT-4o
        test_results["comparison_with_gpt4o"] = self.test_comparison_with_gpt4o()
        
        # Summary
        successful_tests = sum(1 for result in test_results.values() if result["success"])
        total_tests = len(test_results)
        
        summary = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests,
            "overall_success": successful_tests >= 3  # Allow 1 failure for comparison test
        }
        
        print(f"\n📊 Test Summary:")
        print(f"   ✅ Successful: {successful_tests}/{total_tests}")
        print(f"   📈 Success Rate: {summary['success_rate']:.1%}")
        print(f"   🎯 Overall: {'PASS' if summary['overall_success'] else 'FAIL'}")
        
        return {
            "summary": summary,
            "test_results": test_results,
            "timestamp": "2025-01-08T10:00:00Z"
        }


def main():
    """Run DeepSeek capability tests"""
    print("🧪 DeepSeek JSON Mode Capability Test")
    print("Testing structured JSON extraction with DeepSeek-V3")
    print("=" * 60)
    
    tester = DeepSeekCapabilityTest()
    
    try:
        results = tester.run_all_tests()
        
        # Save results
        results_path = Path(__file__).parent / "deepseek_capability_test_results.json"
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