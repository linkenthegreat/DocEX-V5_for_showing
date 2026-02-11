"""
GPT-4o Function Calling Capability Test
Tests the native structured output capabilities with our stakeholder extraction schema
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.github_models_processor import GitHubModelsProcessor


class GPT4oCapabilityTest:
    """Test GPT-4o function calling capabilities for stakeholder extraction"""
    
    def __init__(self):
        self.processor = GitHubModelsProcessor()
        self.schema_path = Path(__file__).parent.parent / "configs" / "schemas" / "stakeholder_function_schema.json"
        self.test_results = []
    
    def load_function_schema(self) -> Dict[str, Any]:
        """Load the GPT-4o function calling schema"""
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")
    
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
                will provide regulatory oversight. Dr. Michael Brown from the University of Melbourne 
                serves as the research advisor.
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
                advocacy groups like Disability Advocacy Network Australia. Service providers 
                such as EnableMe Services and Community Care Solutions deliver support services.
                
                The review committee includes Dr. Jennifer Walsh (disability researcher), 
                Tom Anderson (policy analyst), and representatives from the Australian Disability 
                Enterprises Association.
                """
            },
            {
                "id": "test_minimal",
                "title": "Minimal Content Document",
                "content": "Project update meeting with Jennifer and the team."
            }
        ]
    
    def test_function_calling_basic(self) -> Dict[str, Any]:
        """Test basic function calling capability"""
        print("🧪 Testing GPT-4o Basic Function Calling...")
        
        try:
            # Load schema
            function_schema = self.load_function_schema()
            
            # Test with simple document
            test_doc = self.create_test_documents()[0]
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert stakeholder analyst. Use the extract_stakeholders function to analyze documents."
                },
                {
                    "role": "user", 
                    "content": f"Extract stakeholders from this document:\n\nTitle: {test_doc['title']}\n\nContent: {test_doc['content']}"
                }
            ]
            
            # Call GitHub Models with function calling (REMOVE await)
            response = self.processor.extract_with_function_calling(
                messages=messages,
                functions=[function_schema],
                model="gpt-4o",
                temperature=0.1,
                max_tokens=2000
            )
            
            return {
                "test": "basic_function_calling",
                "success": True,
                "response": response,
                "validation": self._validate_response_structure(response)
            }
            
        except Exception as e:
            return {
                "test": "basic_function_calling",
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def test_schema_validation(self) -> Dict[str, Any]:
        """Test that GPT-4o respects schema constraints"""
        print("🔍 Testing Schema Validation...")
        
        try:
            function_schema = self.load_function_schema()
            test_doc = self.create_test_documents()[1]  # Complex document
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a precise stakeholder analyst. Follow the schema exactly. Use only the specified enum values."
                },
                {
                    "role": "user",
                    "content": f"Extract stakeholders from:\n\n{test_doc['content']}\n\nIMPORTANT: Use only INDIVIDUAL, GROUP, or ORGANIZATIONAL for stakeholder_type."
                }
            ]
            
            # REMOVE await
            response = self.processor.extract_with_function_calling(
                messages=messages,
                functions=[function_schema],
                model="gpt-4o",
                temperature=0.1
            )
            
            validation_results = self._validate_schema_compliance(response)
            
            return {
                "test": "schema_validation",
                "success": validation_results["valid"],
                "response": response,
                "validation_details": validation_results
            }
            
        except Exception as e:
            return {
                "test": "schema_validation", 
                "success": False,
                "error": str(e)
            }
    
    def test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases and error handling"""
        print("⚠️ Testing Edge Cases...")
        
        try:
            function_schema = self.load_function_schema()
            test_doc = self.create_test_documents()[2]  # Minimal document
            
            messages = [
                {
                    "role": "system",
                    "content": "Extract stakeholders even from minimal information. If uncertain, use lower confidence scores."
                },
                {
                    "role": "user",
                    "content": f"Extract stakeholders from this minimal document:\n\n{test_doc['content']}"
                }
            ]
            
            # REMOVE await
            response = self.processor.extract_with_function_calling(
                messages=messages,
                functions=[function_schema],
                model="gpt-4o",
                temperature=0.2  # Slightly higher for creativity with minimal data
            )
            
            edge_case_validation = self._validate_edge_case_handling(response)
            
            return {
                "test": "edge_cases",
                "success": True,
                "response": response,
                "edge_case_validation": edge_case_validation
            }
            
        except Exception as e:
            return {
                "test": "edge_cases",
                "success": False,
                "error": str(e)
            }
    
    def _validate_response_structure(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that response has expected structure"""
        validation = {
            "has_stakeholders": "stakeholders" in response,
            "has_extraction_confidence": "extraction_confidence" in response,
            "stakeholders_is_list": isinstance(response.get("stakeholders", []), list),
            "extraction_confidence_valid": self._is_valid_confidence(response.get("extraction_confidence")),
            "stakeholder_count": len(response.get("stakeholders", []))
        }
        
        # Validate individual stakeholders
        stakeholders = response.get("stakeholders", [])
        if stakeholders:
            first_stakeholder = stakeholders[0]
            validation.update({
                "stakeholder_has_name": "name" in first_stakeholder,
                "stakeholder_has_type": "stakeholder_type" in first_stakeholder,
                "stakeholder_has_confidence": "confidence_score" in first_stakeholder,
                "confidence_score_valid": self._is_valid_confidence(first_stakeholder.get("confidence_score"))
            })
        
        validation["overall_valid"] = all([
            validation["has_stakeholders"],
            validation["has_extraction_confidence"], 
            validation["stakeholders_is_list"],
            validation["extraction_confidence_valid"]
        ])
        
        return validation
    
    def _validate_schema_compliance(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate response complies with schema constraints"""
        validation = {"valid": True, "violations": []}
        
        stakeholders = response.get("stakeholders", [])
        
        for i, stakeholder in enumerate(stakeholders):
            # Check required fields
            if "name" not in stakeholder:
                validation["violations"].append(f"Stakeholder {i}: Missing required 'name' field")
                validation["valid"] = False
            
            if "stakeholder_type" not in stakeholder:
                validation["violations"].append(f"Stakeholder {i}: Missing required 'stakeholder_type' field")
                validation["valid"] = False
            
            # Check enum values
            stakeholder_type = stakeholder.get("stakeholder_type")
            if stakeholder_type not in ["INDIVIDUAL", "GROUP", "ORGANIZATIONAL"]:
                validation["violations"].append(f"Stakeholder {i}: Invalid stakeholder_type '{stakeholder_type}'")
                validation["valid"] = False
            
            # Check confidence score range
            confidence = stakeholder.get("confidence_score")
            if confidence is not None and (confidence < 0.3 or confidence > 1.0):
                validation["violations"].append(f"Stakeholder {i}: Confidence score {confidence} outside valid range [0.3, 1.0]")
                validation["valid"] = False
        
        return validation
    
    def _validate_edge_case_handling(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate how well the model handles edge cases"""
        stakeholders = response.get("stakeholders", [])
        
        return {
            "extracted_from_minimal": len(stakeholders) > 0,
            "appropriate_confidence": all(
                s.get("confidence_score", 1.0) <= 0.8 for s in stakeholders
            ),  # Lower confidence expected for minimal data
            "no_hallucination": len(stakeholders) <= 3,  # Shouldn't over-extract from minimal content
        }
    
    def _is_valid_confidence(self, confidence: Any) -> bool:
        """Check if confidence score is valid"""
        if confidence is None:
            return False
        if not isinstance(confidence, (int, float)):
            return False
        return 0.0 <= confidence <= 1.0
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all GPT-4o capability tests"""
        print("🚀 Starting GPT-4o Capability Tests...")
        print("=" * 50)
        
        test_results = {}
        
        # Test 1: Basic function calling
        test_results["basic_function_calling"] = self.test_function_calling_basic()
        
        # Test 2: Schema validation  
        test_results["schema_validation"] = self.test_schema_validation()
        
        # Test 3: Edge cases
        test_results["edge_cases"] = self.test_edge_cases()
        
        # Summary
        successful_tests = sum(1 for result in test_results.values() if result["success"])
        total_tests = len(test_results)
        
        summary = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests,
            "overall_success": successful_tests == total_tests
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
    """Run GPT-4o capability tests"""
    print("🧪 GPT-4o Function Calling Capability Test")
    print("Testing stakeholder extraction with native structured output")
    print("=" * 60)
    
    tester = GPT4oCapabilityTest()
    
    try:
        results = tester.run_all_tests()
        
        # Save results
        results_path = Path(__file__).parent / "gpt4o_capability_test_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_path}")
        
        # Return success code based on results
        return 0 if results["summary"]["overall_success"] else 1
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)