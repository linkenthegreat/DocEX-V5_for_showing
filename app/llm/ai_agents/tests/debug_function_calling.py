"""
Debug version of function calling test - step by step debugging
"""
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.github_models_processor import GitHubModelsProcessor


def test_schema_loading():
    """Test if we can load the schema file"""
    print("🔍 Testing Schema Loading...")
    
    schema_path = Path(__file__).parent.parent / "configs" / "schemas" / "stakeholder_function_schema.json"
    print(f"   Schema path: {schema_path}")
    print(f"   File exists: {schema_path.exists()}")
    
    if schema_path.exists():
        try:
            with open(schema_path, 'r') as f:
                schema = json.load(f)
            print(f"   ✅ Schema loaded successfully")
            print(f"   Function name: {schema.get('name')}")
            return schema
        except Exception as e:
            print(f"   ❌ Schema loading failed: {e}")
            return None
    else:
        print(f"   ❌ Schema file not found")
        return None


def test_function_calling_method():
    """Test if the extract_with_function_calling method exists"""
    print("\n🔍 Testing Function Calling Method...")
    
    try:
        processor = GitHubModelsProcessor()
        
        # Check if method exists
        if hasattr(processor, 'extract_with_function_calling'):
            print("   ✅ extract_with_function_calling method exists")
            return processor
        else:
            print("   ❌ extract_with_function_calling method NOT found")
            print("   Available methods:")
            for attr in dir(processor):
                if not attr.startswith('_') and callable(getattr(processor, attr)):
                    print(f"      - {attr}")
            return None
            
    except Exception as e:
        print(f"   ❌ Processor initialization failed: {e}")
        return None


def test_simple_function_call():
    """Test a very simple function call"""
    print("\n🧪 Testing Simple Function Call...")
    
    processor = GitHubModelsProcessor()
    
    # Simple function schema - Fix: use Python boolean False, not JSON false
    simple_function = {
        "name": "get_info",
        "description": "Extract basic information",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "A simple message"
                }
            },
            "required": ["message"],
            "additionalProperties": False  # Fix: Python boolean, not JSON
        }
    }
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Use the get_info function to respond."
        },
        {
            "role": "user",
            "content": "Say hello using the function."
        }
    ]
    
    try:
        print("   Calling extract_with_function_calling...")
        result = processor.extract_with_function_calling(
            messages=messages,
            functions=[simple_function],
            model="gpt-4o",  # Use "gpt-4o" not "openai/gpt-4o"
            temperature=0.1
        )
        print(f"   ✅ Function call successful: {result}")
        return True
        
    except Exception as e:
        print(f"   ❌ Function call failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


def test_model_name_format():
    """Test different model name formats"""
    print("\n🔍 Testing Model Name Formats...")
    
    processor = GitHubModelsProcessor()
    
    # Test simple GPT call with different model names
    test_models = ["gpt-4o", "openai/gpt-4o", "gpt-4o-mini"]
    
    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Say hello in one word."}
    ]
    
    for model in test_models:
        try:
            response = processor.call_gpt_model(messages, model=model)
            print(f"   ✅ Model '{model}' works: {response}")
        except Exception as e:
            print(f"   ❌ Model '{model}' failed: {e}")


def main():
    """Run all debug tests"""
    print("🐛 Function Calling Debug Tests")
    print("=" * 40)
    
    # Test 1: Schema loading
    schema = test_schema_loading()
    
    # Test 2: Method exists
    processor = test_function_calling_method()
    
    # Test 3: Model name formats
    test_model_name_format()
    
    # Test 4: Simple function call
    if processor and schema:
        test_simple_function_call()
    else:
        print("\n❌ Cannot proceed with function call test - prerequisites failed")


if __name__ == "__main__":
    main()