
"""
Test the dedicated Local Llama Client
Clean, reliable testing for Llama3.1 8B integration
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.ai_agents.local_llama_client import LocalLlamaClient, test_local_llama_connection, extract_stakeholders_local


def test_connection():
    """Test connection to local Llama"""
    print("🔌 Testing Local Llama Connection...")
    
    result = test_local_llama_connection()
    
    if result["status"] == "connected":
        print(f"   ✅ Connected to Ollama v{result['version']}")
        print(f"   🦙 Model available: {result['model_available']}")
        return True
    else:
        print(f"   ❌ Connection failed: {result.get('error')}")
        return False


def test_jsonld_extraction():
    """Test JSON-LD extraction"""
    print("\n🦙 Testing JSON-LD Extraction...")
    
    test_content = """
    The NDIS Quality Review involves multiple stakeholders. Dr. Emily Watson, 
    the Chief Policy Officer, leads the initiative. The Implementation Committee 
    provides oversight, while the Department of Social Services sponsors the project.
    """
    
    result = extract_stakeholders_local(
        test_content, 
        "NDIS Quality Review",
        use_jsonld=True
    )
    
    if result["success"]:
        stakeholders = result.get("stakeholders", [])
        metadata = result.get("metadata", {})
        
        print(f"   ✅ Extraction successful")
        print(f"   📊 Stakeholders found: {len(stakeholders)}")
        print(f"   🎯 JSON-LD compliant: {metadata.get('json_ld_compliant', False)}")
        print(f"   📈 Confidence: {metadata.get('extraction_confidence', 0.0):.2f}")
        
        if stakeholders:
            print(f"   👤 Example: {stakeholders[0].get('name')} ({stakeholders[0].get('stakeholderType')})")
        
        return True
    else:
        print(f"   ❌ Extraction failed: {result.get('error')}")
        return False


def test_simple_extraction():
    """Test simple JSON extraction (fallback)"""
    print("\n📋 Testing Simple JSON Extraction...")
    
    test_content = """
    The project is managed by John Smith and includes the Development Team.
    Oversight is provided by the Board of Directors.
    """
    
    result = extract_stakeholders_local(
        test_content,
        use_jsonld=False
    )
    
    if result["success"]:
        stakeholders = result.get("stakeholders", [])
        print(f"   ✅ Simple extraction successful")
        print(f"   📊 Stakeholders found: {len(stakeholders)}")
        
        if stakeholders:
            print(f"   👤 Example: {stakeholders[0].get('name')} ({stakeholders[0].get('type')})")
        
        return True
    else:
        print(f"   ❌ Simple extraction failed: {result.get('error')}")
        return False


def main():
    """Run all local Llama tests"""
    print("🧪 Local Llama Client Test Suite")
    print("=" * 40)
    
    tests = [
        test_connection,
        test_jsonld_extraction,
        test_simple_extraction
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    successful = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Successful: {successful}/{total}")
    print(f"   📈 Success Rate: {successful/total:.1%}")
    
    if successful == total:
        print(f"   🎯 Status: READY FOR AGENT INTEGRATION")
    elif successful >= 2:
        print(f"   ⚠️ Status: PARTIAL SUCCESS - Use with caution")
    else:
        print(f"   ❌ Status: NOT READY - Skip local integration")
    
    return successful >= 2  # At least connection + one extraction method


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)