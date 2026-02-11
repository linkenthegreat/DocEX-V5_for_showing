
"""
Quick test to compare function calling vs structured output
"""
import json
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.github_models_processor import GitHubModelsProcessor


def test_both_extraction_methods():
    """Test both function calling and structured output methods"""
    
    processor = GitHubModelsProcessor()
    
    # Load schema
    schema_path = Path(__file__).parent.parent / "configs" / "schemas" / "stakeholder_function_schema.json"
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Test document
    messages = [
        {
            "role": "system",
            "content": "Extract stakeholders from the document. Use the exact format specified."
        },
        {
            "role": "user",
            "content": "John Smith is the Project Manager and Sarah Johnson leads the Development Team."
        }
    ]
    
    print("🧪 Testing Both Extraction Methods")
    print("=" * 40)
    
    # Method 1: Function calling
    print("\n1️⃣ Testing Function Calling Method...")
    try:
        result1 = processor.extract_with_function_calling(
            messages=messages,
            functions=[schema],
            model="gpt-4o",
            temperature=0.1
        )
        print(f"   ✅ Function calling successful: {result1}")
    except Exception as e:
        print(f"   ❌ Function calling failed: {e}")
        result1 = None
    
    # Method 2: Structured output
    print("\n2️⃣ Testing Structured Output Method...")
    try:
        result2 = processor.extract_with_structured_output(
            messages=messages,
            schema=schema,
            model="gpt-4o",
            temperature=0.1
        )
        print(f"   ✅ Structured output successful: {result2}")
    except Exception as e:
        print(f"   ❌ Structured output failed: {e}")
        result2 = None
    
    # Method 3: Fallback to JSON mode
    print("\n3️⃣ Testing JSON Mode Fallback...")
    try:
        json_messages = messages + [
            {
                "role": "system", 
                "content": "Return valid JSON with 'stakeholders' array and 'extraction_confidence' number."
            }
        ]
        
        result3 = processor.extract_structured_json(
            messages=json_messages,
            model="gpt-4o"
        )
        print(f"   ✅ JSON mode successful: {result3}")
    except Exception as e:
        print(f"   ❌ JSON mode failed: {e}")
        result3 = None
    
    # Summary
    print(f"\n📊 Results Summary:")
    print(f"   Function Calling: {'✅' if result1 else '❌'}")
    print(f"   Structured Output: {'✅' if result2 else '❌'}")
    print(f"   JSON Mode: {'✅' if result3 else '❌'}")
    
    return result1, result2, result3


if __name__ == "__main__":
    test_both_extraction_methods()