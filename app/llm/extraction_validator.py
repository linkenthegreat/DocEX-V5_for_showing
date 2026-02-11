"""
Validator for extraction results
"""
import json
from pathlib import Path
import logging

class ExtractionValidator:
    """Validates extraction results against expected outputs"""
    
    def __init__(self, expected_dir=None):
        self.logger = logging.getLogger(__name__)
        # Don't reference test directories in production code
        self.expected_dir = expected_dir or Path(__file__).parent.parent / "data" / "validation_schemas"
        
    def validate(self, extraction_result, document_name, extraction_type):
        """Compare extraction result with expected output"""
        expected_file = self.expected_dir / f"{document_name}_{extraction_type}_expected.json"
        
        if not expected_file.exists():
            self.logger.warning(f"No expected result file found: {expected_file}")
            return {
                "status": "unknown",
                "message": "No expected result available for comparison"
            }
            
        try:
            with open(expected_file, "r", encoding="utf-8") as f:
                expected = json.load(f)
                
            # Simple validation - check if all expected keys exist in result
            extraction_data = extraction_result.get("extraction", {})
            if not extraction_data:
                return {"status": "failed", "message": "No extraction data found"}
                
            # Compare with expected result
            validation_results = self._compare_structures(extraction_data, expected)
            
            return {
                "status": "passed" if validation_results["match"] else "failed",
                "details": validation_results
            }
                
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return {"status": "error", "message": str(e)}
            
    def _compare_structures(self, actual, expected):
        """Compare actual extraction with expected structure"""
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                return {"match": False, "reason": f"Expected dict, got {type(actual).__name__}"}
                
            # Check if expected keys exist in actual
            missing_keys = []
            for key in expected:
                if key not in actual:
                    missing_keys.append(key)
                    
            if missing_keys:
                return {"match": False, "reason": f"Missing keys: {missing_keys}"}
                
            return {"match": True, "details": "Structure matches expected pattern"}
            
        elif isinstance(expected, list):
            if not isinstance(actual, list):
                return {"match": False, "reason": f"Expected list, got {type(actual).__name__}"}
                
            if len(expected) > 0 and isinstance(expected[0], dict):
                # For list of objects, check if required keys exist in each item
                required_keys = set(expected[0].keys())
                for item in actual:
                    if not isinstance(item, dict):
                        return {"match": False, "reason": "List item is not a dict"}
                    if not all(key in item for key in required_keys):
                        return {"match": False, "reason": f"Item missing required keys: {required_keys}"}
                        
            return {"match": True, "details": "List structure matches expected pattern"}
            
        else:
            # Simple types - just check type match
            return {"match": isinstance(actual, type(expected)), 
                    "reason": f"Type mismatch: expected {type(expected).__name__}, got {type(actual).__name__}"}