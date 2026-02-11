"""
Quick Llama3.1 8B JSON-LD Capability Test
Test local model's structured output for JSON-LD extraction
"""
import json
import sys
from pathlib import Path

# Add project root to path  
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.llm_client import LLMClient
from app.llm.llm_providers.provider_factory import LLMProviderFactory  # Fixed import


def test_llama_jsonld_basic():
    """Test Llama3.1 8B basic JSON-LD extraction"""
    print("🦙 Testing Llama3.1 8B JSON-LD Capability...")
    
    test_content = """
    The NDIS Review is led by Dr. Sarah Mitchell, Chief Policy Officer. 
    The Implementation Committee oversees progress, while Disability Australia 
    advocates for participants.
    """
    
    prompt = f"""Extract stakeholders in JSON-LD format:

{test_content}

Return only valid JSON in this format:
{{
  "@context": {{"@vocab": "https://docex.org/vocab/"}},
  "@type": "StakeholderExtraction", 
  "stakeholders": [
    {{
      "@type": "Stakeholder",
      "@id": "stakeholder:unique-id",
      "name": "string",
      "role": "string",
      "stakeholderType": "INDIVIDUAL|GROUP|ORGANIZATIONAL",
      "confidenceScore": 0.3-1.0
    }}
  ],
  "extractionConfidence": 0.0-1.0
}}

Return ONLY the JSON, no explanations."""

    try:
        # Method 1: Try using the provider factory (FIXED METHOD)
        try:
            provider_factory = LLMProviderFactory()
            ollama_provider = provider_factory.create_provider("ollama")  # Fixed: use create_provider
            ollama_provider.initialize()
            
            response = ollama_provider.invoke(
                prompt=prompt,
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse response
            parsed_response = ollama_provider.parse_response(response)
            
            print(f"   📡 Using Ollama Provider (Fixed)")
            
            # Handle parsed response
            if "raw_text" in parsed_response:
                response_text = parsed_response["raw_text"]
            else:
                response_text = json.dumps(parsed_response)
            
        except Exception as provider_error:
            print(f"   ⚠️ Provider method failed: {provider_error}")
            
            # Method 2: Fallback to direct LLM client (THIS METHOD WORKS)
            print(f"   📡 Falling back to direct LLM client")
            client = LLMClient(model="llama3.1:8b-instruct-q8_0")
            
            result = client.analyze_text(prompt)
            
            # Extract response text
            if "error" in result:
                raise Exception(result["error"])
            elif "raw_text" in result:
                response_text = result["raw_text"]
            else:
                response_text = json.dumps(result)
        
        # Try to parse JSON response
        try:
            # Clean up response if it has extra text
            response_clean = response_text.strip()
            
            # Try to extract JSON from response
            if response_clean.startswith('{') and response_clean.endswith('}'):
                parsed = json.loads(response_clean)
            else:
                # Look for JSON in the response
                import re
                json_match = re.search(r'\{[\s\S]*\}', response_clean)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                else:
                    raise json.JSONDecodeError("No JSON found", response_clean, 0)
            
            has_context = "@context" in parsed
            has_type = "@type" in parsed
            has_stakeholders = "stakeholders" in parsed
            
            result = {
                "success": True,
                "json_ld_compliant": has_context and has_type,
                "stakeholder_count": len(parsed.get("stakeholders", [])),
                "response": parsed
            }
            
            print(f"   ✅ JSON-LD parsing: {'✅' if result['json_ld_compliant'] else '❌'}")
            print(f"   📊 Stakeholders: {result['stakeholder_count']}")
            
            if result['json_ld_compliant'] and result['stakeholder_count'] > 0:
                print(f"   🎯 Example stakeholder: {parsed['stakeholders'][0].get('name', 'Unknown')}")
            
            return result
            
        except json.JSONDecodeError as json_error:
            print(f"   ❌ JSON parsing failed: {json_error}")
            print(f"   📝 Raw response (first 200 chars): {response_text[:200]}...")
            return {
                "success": False,
                "error": "Invalid JSON",
                "raw_response": response_text[:200] + "..." if len(response_text) > 200 else response_text
            }
            
    except Exception as e:
        print(f"   ❌ Connection/processing error: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def test_ollama_connectivity():
    """Test if Ollama is running and accessible"""
    print("\n🔌 Testing Ollama Connectivity...")
    
    try:
        client = LLMClient()
        connection_result = client.test_connection()
        
        if connection_result.get("status") == "connected":
            print(f"   ✅ Ollama connected, version: {connection_result.get('version', 'unknown')}")
            return True
        else:
            print(f"   ❌ Ollama connection failed: {connection_result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ollama connectivity test failed: {e}")
        return False


def main():
    """Quick Llama3.1 capability check"""
    print("🧪 Llama3.1 8B JSON-LD Quick Test")
    print("=" * 40)
    
    # First test connectivity
    if not test_ollama_connectivity():
        print("\n❌ Cannot proceed: Ollama not accessible")
        print("💡 Make sure Ollama is running: ollama serve")
        return False
    
    # Run JSON-LD capability test
    result = test_llama_jsonld_basic()
    
    print("\n📊 Final Result:")
    if result["success"]:
        if result.get('json_ld_compliant'):
            print("✅ Llama3.1 8B: READY FOR JSON-LD")
            print(f"   📈 Quality: {result['stakeholder_count']} stakeholders extracted")
            print(f"   🎯 Recommendation: Add to agent as 'ollama_structured' strategy")
        else:
            print("⚠️ Llama3.1 8B: PARTIAL SUCCESS")
            print(f"   📊 Extracts data but JSON-LD structure needs improvement")
            print(f"   🎯 Recommendation: Use as fallback with enhanced prompting")
    else:
        print("❌ Llama3.1 8B: NOT READY")
        print(f"   🚫 Error: {result.get('error', 'Unknown error')}")
        print(f"   🎯 Recommendation: Skip Llama for now, focus on GPT-4o + DeepSeek")
    
    return result["success"]


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)