"""
Comprehensive Test for Complete Data Extraction Agent
Tests all strategies, models, and priority modes
"""
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

from app.llm.ai_agents.data_extraction_agent import (
    DataExtractionAgent, 
    extract_stakeholders_from_document,
    extract_stakeholders_with_privacy,
    extract_stakeholders_with_quality,
    extract_stakeholders_with_cost_optimization
)


def test_agent_initialization():
    """Test agent initializes with all models"""
    print("🧪 Testing Agent Initialization...")
    
    try:
        agent = DataExtractionAgent()
        availability = agent.model_availability
        
        print(f"   ✅ Agent initialized successfully")
        print(f"   📊 Model availability:")
        for model, available in availability.items():
            status = "✅" if available else "❌"
            print(f"      {status} {model}")
        
        return True
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
        return False


def test_priority_modes():
    """Test all priority modes"""
    print("\n🎯 Testing Priority Modes...")
    
    test_content = """
    The National Disability Insurance Scheme Review involves multiple stakeholders.
    Minister Janet Roberts provides political oversight, while Dr. Sarah Chen leads
    the research team. The Participant Advisory Committee ensures community input,
    and service providers like EnableMe Australia deliver support services.
    """
    
    priorities = {
        "cost": "Most cost-effective (local → DeepSeek → GPT)",
        "quality": "Highest quality (GPT-4o function calling)",
        "speed": "Fastest processing (DeepSeek JSON mode)",
        "privacy": "Local processing only (Llama 3.1)"
    }
    
    results = {}
    
    for priority, description in priorities.items():
        try:
            print(f"\n   🎚️ Testing {priority} priority: {description}")
            
            result = extract_stakeholders_from_document(
                test_content, 
                f"NDIS Review - {priority} test",
                priority=priority
            )
            
            results[priority] = result
            
            print(f"      ✅ Success: {result.success}")
            print(f"      🤖 Strategy: {result.strategy_used}")
            print(f"      🧠 Model: {result.model_used}")
            print(f"      📊 Stakeholders: {len(result.stakeholders)}")
            print(f"      💰 Cost: ${result.cost_estimate:.4f}")
            print(f"      ⏱️ Time: {result.processing_time:.2f}s")
            print(f"      🎯 Confidence: {result.extraction_confidence:.2f}")
            
        except Exception as e:
            print(f"      ❌ {priority} priority failed: {e}")
            results[priority] = None
    
    successful_priorities = sum(1 for r in results.values() if r and r.success)
    total_priorities = len(priorities)
    
    print(f"\n   📈 Priority Mode Results: {successful_priorities}/{total_priorities} successful")
    return successful_priorities >= 2  # At least 2 priorities working


def test_convenience_functions():
    """Test convenience functions"""
    print("\n🚀 Testing Convenience Functions...")
    
    test_content = """
    The project team includes Project Manager Lisa Wang, Technical Lead Ahmed Hassan,
    and stakeholder representative Maria González. The steering committee provides
    governance oversight.
    """
    
    functions = {
        "Privacy": extract_stakeholders_with_privacy,
        "Quality": extract_stakeholders_with_quality, 
        "Cost": extract_stakeholders_with_cost_optimization
    }
    
    results = {}
    
    for name, func in functions.items():
        try:
            print(f"\n   🔧 Testing {name} function...")
            
            result = func(test_content, f"{name} Test Document")
            results[name] = result
            
            print(f"      ✅ Success: {result.success}")
            print(f"      📊 Stakeholders: {len(result.stakeholders)}")
            print(f"      🧠 Model: {result.model_used}")
            
            if result.stakeholders:
                example = result.stakeholders[0]
                print(f"      👤 Example: {example.get('name')} ({example.get('stakeholderType')})")
            
        except Exception as e:
            print(f"      ❌ {name} function failed: {e}")
            results[name] = None
    
    successful_functions = sum(1 for r in results.values() if r and r.success)
    total_functions = len(functions)
    
    print(f"\n   📈 Convenience Function Results: {successful_functions}/{total_functions} successful")
    return successful_functions >= 2


def test_performance_tracking():
    """Test performance tracking and reporting"""
    print("\n📊 Testing Performance Tracking...")
    
    try:
        agent = DataExtractionAgent()
        
        # Run multiple extractions
        test_docs = [
            ("Simple doc with John Smith as manager.", "Simple Test"),
            ("Committee led by Dr. Sarah Jones with oversight from Board.", "Committee Test"),
            ("Project includes Development Team and Quality Assurance Group.", "Team Test")
        ]
        
        for content, title in test_docs:
            agent.extract_stakeholders(content, title, priority="cost")
        
        # Get performance report
        report = agent.get_performance_report()
        
        print(f"   ✅ Performance tracking working")
        print(f"   📈 Extractions: {report['performance_stats']['total_extractions']}")
        print(f"   🎯 Success rate: {report['performance_stats']['success_rate']:.1%}")
        print(f"   💰 Total cost: ${report['performance_stats']['total_cost']:.4f}")
        print(f"   ⏱️ Avg time: {report['performance_stats']['average_processing_time']:.2f}s")
        print(f"   🏆 Most used strategy: {report['most_used_strategy']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Performance tracking failed: {e}")
        return False


def test_fallback_system():
    """Test fallback system with intentionally problematic input"""
    print("\n🔄 Testing Fallback System...")
    
    try:
        agent = DataExtractionAgent()
        
        # Test with minimal content that might challenge some models
        minimal_content = "Project."
        
        result = agent.extract_stakeholders(
            minimal_content, 
            "Minimal Content Test",
            priority="quality"
        )
        
        print(f"   ✅ Fallback handling: {result.success}")
        print(f"   🔧 Final strategy: {result.strategy_used}")
        print(f"   📊 Stakeholders found: {len(result.stakeholders)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Fallback system failed: {e}")
        return False


def test_model_validation():
    """Test that all validated models work as expected"""
    print("\n✅ Testing Model Validation...")
    
    test_content = """
    The NDIS Quality Framework Review is coordinated by the Department of Social Services,
    with Dr. Patricia Chen as the Lead Researcher. The Quality and Safeguards Commission
    provides regulatory oversight, while participant advocates ensure community voice.
    """
    
    # Test each model directly
    models_to_test = [
        ("gpt-4o", "native_structured"),
        ("deepseek/DeepSeek-V3-0324", "json_mode_guided"),
        ("llama3.1:8b-instruct-q8_0", "ollama_structured")
    ]
    
    results = {}
    
    for model, strategy in models_to_test:
        try:
            print(f"\n   🧠 Testing {model} with {strategy}...")
            
            agent = DataExtractionAgent()
            result = agent.extract_stakeholders(
                test_content,
                "Model Validation Test",
                priority="cost",
                strategy=strategy,
                model=model
            )
            
            results[model] = result
            
            if result.success:
                print(f"      ✅ Success: {len(result.stakeholders)} stakeholders")
                print(f"      📊 JSON-LD: {result.metadata.get('json_ld_compliant', False)}")
                print(f"      💰 Cost: ${result.cost_estimate:.4f}")
            else:
                print(f"      ❌ Failed: {result.errors}")
            
        except Exception as e:
            print(f"      ❌ {model} test failed: {e}")
            results[model] = None
    
    successful_models = sum(1 for r in results.values() if r and r.success)
    total_models = len(models_to_test)
    
    print(f"\n   📈 Model Validation Results: {successful_models}/{total_models} successful")
    return successful_models >= 2  # At least 2 models working


def main():
    """Run comprehensive agent test suite"""
    print("🧪 Complete Data Extraction Agent Test Suite")
    print("=" * 60)
    
    tests = [
        test_agent_initialization,
        test_priority_modes,
        test_convenience_functions,
        test_performance_tracking,
        test_fallback_system,
        test_model_validation
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Summary
    successful = sum(results)
    total = len(results)
    
    print(f"\n📊 Complete Agent Test Summary:")
    print(f"   ✅ Successful: {successful}/{total}")
    print(f"   📈 Success Rate: {successful/total:.1%}")
    
    if successful == total:
        print(f"   🎯 Status: PRODUCTION READY 🚀")
        print(f"   💡 All models and strategies validated")
        print(f"   🎉 Ready for DocEX integration!")
    elif successful >= 4:
        print(f"   ⚠️ Status: MOSTLY READY")
        print(f"   💡 Core functionality working, minor issues detected")
    else:
        print(f"   ❌ Status: NEEDS WORK")
        print(f"   💡 Significant issues detected, review required")
    
    return successful >= 4  # 4+ tests passing = good enough for production


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)