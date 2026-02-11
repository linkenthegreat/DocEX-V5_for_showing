"""
Direct Ollama Provider Test for JSON-LD
Uses the provider factory architecture
"""
import json
import sys
from pathlib import Path

# Add project root to path  
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.llm_providers.provider_factory import LLMProviderFactory


def test_ollama_direct():
    """Test Ollama provider directly"""
    print("🦙 Testing Ollama Provider Direct...")
    
    test_content = """
    The NDIS Review is led by Dr. Sarah Mitchell, Chief Policy Officer. 
    The Implementation Committee oversees progress, while Disability Australia 
    advocates for participants.
    """
    
    prompt = f"""Extract stakeholders from this text and return as JSON:

{test_content}

Format:
{{
  "stakeholders": [
    {{
      "name": "person or organization name",
      "role": "their role or responsibility", 
      "type": "INDIVIDUAL or GROUP or ORGANIZATIONAL"
    }}
  ]
}}

Return only the JSON, nothing else."""

    try:
        # Get Ollama provider using correct method
        factory = LLMProviderFactory()
        ollama_provider = factory.create_provider("ollama")  # Fixed: use create_provider instead of get_provider
        
        # Initialize the provider
        ollama_provider.initialize()
        
        print(f"   📡 Provider: {type(ollama_provider).__name__}")
        
        # Make the call
        response = ollama_provider.invoke(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1000
        )
        
        print(f"   📤 Response received: {len(str(response))} chars")
        
        # Parse the response
        parsed_response = ollama_provider.parse_response(response)
        
        print(f"   🔧 Parsed response type: {type(parsed_response)}")
        
        # Handle parsed response
        if isinstance(parsed_response, dict):
            if "stakeholders" in parsed_response:
                # Direct JSON response
                stakeholder_count = len(parsed_response["stakeholders"])
                print(f"   ✅ JSON parsed successfully")
                print(f"   📊 Stakeholders: {stakeholder_count}")
                
                if stakeholder_count > 0:
                    first = parsed_response["stakeholders"][0]
                    print(f"   👤 Example: {first.get('name', 'Unknown')} ({first.get('type', 'Unknown')})")
                
                return {
                    "success": True,
                    "stakeholder_count": stakeholder_count,
                    "response": parsed_response
                }
            elif "raw_text" in parsed_response:
                # Try to extract JSON from raw text
                raw_text = parsed_response["raw_text"]
                print(f"   📝 Raw text response: {len(raw_text)} chars")
                
                # Try to find JSON in raw text
                import re
                json_match = re.search(r'\{[\s\S]*\}', raw_text)
                if json_match:
                    try:
                        json_data = json.loads(json_match.group(0))
                        stakeholder_count = len(json_data.get("stakeholders", []))
                        print(f"   ✅ Extracted JSON from raw text")
                        print(f"   📊 Stakeholders: {stakeholder_count}")
                        
                        return {
                            "success": True,
                            "stakeholder_count": stakeholder_count,
                            "response": json_data
                        }
                    except json.JSONDecodeError as e:
                        print(f"   ❌ Failed to parse extracted JSON: {e}")
                        return {"success": False, "error": f"JSON parsing failed: {e}"}
                else:
                    print(f"   ❌ No JSON found in raw text")
                    return {"success": False, "error": "No JSON found in response"}
            else:
                print(f"   ❌ Unexpected response structure: {list(parsed_response.keys())}")
                return {"success": False, "error": "Unexpected response structure"}
        else:
            print(f"   ❌ Non-dict response: {type(parsed_response)}")
            return {"success": False, "error": f"Unexpected response type: {type(parsed_response)}"}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Test Ollama provider directly"""
    print("🧪 Ollama Provider Direct Test")
    print("=" * 35)
    
    result = test_ollama_direct()
    
    if result["success"]:
        print(f"\n✅ Ollama Provider: WORKING")
        print(f"   📈 Extracted: {result['stakeholder_count']} stakeholders")
        print(f"   🎯 Ready for agent integration")
    else:
        print(f"\n❌ Ollama Provider: FAILED")
        print(f"   🚫 Error: {result.get('error')}")
    
    return result["success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)