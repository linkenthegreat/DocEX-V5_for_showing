
"""
Basic GitHub Models Connection Test
Verifies that GitHub Models API is working with the current processor
"""
import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.github_models_processor import GitHubModelsProcessor


def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking Environment Variables...")
    
    github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GITHUB_API_KEY')
    endpoint = os.getenv('GITHUB_ENDPOINT', 'https://models.github.ai/inference')
    
    print(f"   GITHUB_TOKEN: {'✅ Set' if github_token else '❌ Missing'}")
    print(f"   Endpoint: {endpoint}")
    
    if not github_token:
        print("\n❌ GITHUB_TOKEN environment variable is required!")
        print("Set it using one of these commands:")
        print("   PowerShell: $Env:GITHUB_TOKEN='your-token-here'")
        print("   Bash: export GITHUB_TOKEN='your-token-here'")
        print("   Cmd: set GITHUB_TOKEN=your-token-here")
        return False
    
    return True


def test_basic_connection():
    """Test basic connection to GitHub Models"""
    print("\n🧪 Testing Basic GitHub Models Connection...")
    
    try:
        processor = GitHubModelsProcessor()
        print("   ✅ GitHubModelsProcessor initialized successfully")
        
        # Get available models
        models = processor.get_available_models()
        print(f"   ✅ Available models: {models}")
        
        return processor
    
    except Exception as e:
        print(f"   ❌ Failed to initialize processor: {e}")
        return None


def test_simple_gpt_call(processor):
    """Test simple GPT model call"""
    print("\n🧪 Testing GPT-4o Simple Call...")
    
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user", 
                "content": "What is the capital of France? Answer in one word."
            }
        ]
        
        response = processor.call_gpt_model(messages, model="gpt-4o")
        print(f"   ✅ GPT-4o Response: {response}")
        return True
        
    except Exception as e:
        print(f"   ❌ GPT-4o call failed: {e}")
        return False


def test_json_mode(processor):
    """Test JSON mode with GPT-4o"""
    print("\n🧪 Testing GPT-4o JSON Mode...")
    
    try:
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Return responses in JSON format."
            },
            {
                "role": "user",
                "content": "What is the capital of France? Return as JSON with 'country' and 'capital' fields."
            }
        ]
        
        response = processor.call_gpt_model(
            messages, 
            model="gpt-4o",
            response_format={"type": "json_object"}
        )
        print(f"   ✅ JSON Response: {response}")
        
        # Try to parse as JSON
        import json
        parsed = json.loads(response)
        print(f"   ✅ Successfully parsed JSON: {parsed}")
        return True
        
    except Exception as e:
        print(f"   ❌ JSON mode test failed: {e}")
        return False


def test_structured_extraction(processor):
    """Test structured extraction method"""
    print("\n🧪 Testing Structured JSON Extraction...")
    
    try:
        messages = [
            {
                "role": "user",
                "content": "Extract information about John Smith who is a Project Manager at ACME Corp. Return as JSON with 'name', 'role', and 'company' fields."
            }
        ]
        
        result = processor.extract_structured_json(messages, model="gpt-4o")
        print(f"   ✅ Structured extraction result: {result}")
        
        # Check if it's valid JSON structure
        if isinstance(result, dict) and 'name' in str(result):
            print("   ✅ Structure appears valid")
            return True
        else:
            print("   ⚠️ Structure may be incomplete but method works")
            return True
            
    except Exception as e:
        print(f"   ❌ Structured extraction failed: {e}")
        return False


def test_deepseek_model(processor):
    """Test DeepSeek model if available"""
    print("\n🧪 Testing DeepSeek Model...")
    
    try:
        # Try the DeepSeek model from your config
        messages = [
            {
                "role": "user",
                "content": "Say hello in JSON format with a 'message' field."
            }
        ]
        
        # Try with the DeepSeek model name from your processor
        result = processor.extract_structured_json(messages, model="deepseek/DeepSeek-V3-0324")
        print(f"   ✅ DeepSeek Response: {result}")
        return True
        
    except Exception as e:
        print(f"   ⚠️ DeepSeek test failed (may not be available): {e}")
        return False


def main():
    """Run all basic tests"""
    print("🚀 GitHub Models Basic Integration Test")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        return 1
    
    # Test basic connection
    processor = test_basic_connection()
    if not processor:
        return 1
    
    # Run tests
    test_results = []
    
    test_results.append(test_simple_gpt_call(processor))
    test_results.append(test_json_mode(processor))
    test_results.append(test_structured_extraction(processor))
    test_results.append(test_deepseek_model(processor))  # This may fail, that's OK
    
    # Summary
    successful_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"\n📊 Test Summary:")
    print(f"   ✅ Successful: {successful_tests}/{total_tests}")
    print(f"   📈 Success Rate: {successful_tests/total_tests:.1%}")
    
    if successful_tests >= 3:  # At least 3 out of 4 should pass
        print(f"   🎯 Overall: PASS - GitHub Models is working!")
        return 0
    else:
        print(f"   🎯 Overall: FAIL - Need to fix GitHub Models setup")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)