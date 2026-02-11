<!-- Update adr_006_docex_agent-based_architecture_proposal.md -->
# 🎯 **DocEX Agent-Based Architecture Proposal**
## Model-Capability-Driven Agent System with Structured Output Optimization

## Status
**Approved** - Ready for Implementation

## 📋 **Executive Summary**

Transform your current monolithic adapter architecture into a **model-capability-driven agent system** that automatically selects optimal extraction strategies based on each model's structured output capabilities.

**Key Benefits:**
- ✅ **Fix immediate issues** (`_clean_github_response` error)
- ✅ **Model-specific optimization** - GPT-4o function calling vs DeepSeek JSON mode
- ✅ **Single agent, multiple strategies** - no separate configs per model
- ✅ **Automatic fallback chains** - robust error handling
- ✅ **Structured output optimization** - leverages each model's best capabilities
- ✅ **OG-RAG foundation** - prepares for graph reasoning

---

## 🔧 **Enhanced Technical Design: Model-Capability-Aware**

### **Key Insight: Different Models Need Different Approaches**
Based on analysis of [Ollama structured outputs](https://ollama.com/blog/structured-outputs) and [DeepSeek JSON mode](https://api-docs.deepseek.com/guides/json_mode):

| Model | Optimal Strategy | Implementation |
|-------|-----------------|----------------|
| **GPT-4o** | Function calling with schema | Native structured output API |
| **DeepSeek-V3** | JSON mode + careful prompting | `response_format: {"type": "json_object"}` |
| **Llama (Ollama)** | Structured output API | Simple schema with format parameter |
| **Legacy Models** | Guided JSON prompting | Template-based with fallback parsing |

### **1. Single Agent with Multiple Model Strategies**

```yaml
# configs/agents.yaml - Enhanced model-capability approach
agents:
  data_extraction_agent:
    name: "🧪 Data Extraction Agent"
    purpose: "Extract stakeholders with model-optimized strategies"
    
    # Model-specific strategies within one agent
    model_strategies:
      # GPT-4o Strategy - Native Structured Output
      native_structured:
        models: ["openai/gpt-4o", "openai/gpt-4o-mini"]
        backend_module: "app.llm.github_models_processor"
        method: "function_calling"
        
        config:
          temperature: 0.1
          max_tokens: 2000
          
        schema_definition:
          type: "function_calling"
          function_name: "extract_stakeholders"
          schema_file: "schemas/stakeholder_function_schema.json"
      
      # DeepSeek Strategy - JSON Mode + Careful Prompting
      json_mode_guided:
        models: ["deepseek/DeepSeek-V3-0324"]
        backend_module: "app.llm.github_models_processor"
        method: "json_mode_prompting"
        
        config:
          temperature: 0.1
          max_tokens: 2000
          response_format: {"type": "json_object"}  # DeepSeek JSON mode
          
        prompt_strategy:
          type: "structured_template"
          template_file: "prompts/deepseek_extraction_template.md"
          validation: "post_processing"
      
      # Ollama Strategy - Structured Outputs API
      ollama_structured:
        models: ["llama3.1:8b-instruct-q8_0", "llama3.2:3b"]
        backend_module: "app.llm.llm_client"
        method: "ollama_structured_output"
        
        config:
          temperature: 0.2
          format: "json"  # Ollama structured output format
          
        schema_definition:
          type: "ollama_schema"
          schema_file: "schemas/stakeholder_ollama_schema.json"

    # Auto-selection with fallback chain
    strategy_selection:
      auto_select: true
      fallback_chain:
        - "native_structured"      # Try best first
        - "json_mode_guided"       # Fall back to JSON mode
        - "ollama_structured"      # Try local processing
        - "guided_json_prompting"  # Last resort
```

### **2. Model-Capability-Aware Agent Implementation**

```python
class DataExtractionAgent:
    """Single agent that adapts to different model capabilities"""
    
    async def extract_stakeholders(
        self, 
        document_data: Dict[str, Any],
        model: str = "auto",
        quality_priority: bool = False
    ) -> Dict[str, Any]:
        """Extract stakeholders using optimal strategy for the model"""
        
        # Auto-select model if needed
        if model == "auto":
            model = self._select_optimal_model(quality_priority)
        
        # Get strategy for this model's capabilities
        strategy_name = self._get_strategy_for_model(model)
        
        # Execute with model-specific strategy
        try:
            result = await self._execute_strategy(strategy_name, document_data, model)
            
            # Add processing metadata
            result['processing_metadata'] = {
                'model_used': model,
                'strategy_used': strategy_name,
                'capabilities_detected': self._get_model_capabilities(model)
            }
            
            return result
            
        except Exception as e:
            # Try fallback strategies automatically
            return await self._execute_fallback_chain(document_data, model, str(e))
```

---

## 📋 **Updated Implementation Plan**

### **Phase 1: Model-Capability Foundation (Week 1)**
**Days 1-2: Configuration Setup**
- [x] Analyze model structured output capabilities
- [ ] Create model-strategy mapping in `agents.yaml`
- [ ] Create model-specific prompt templates
- [ ] Create model-specific schema definitions

**Days 3-4: Agent Development**
- [ ] Implement `DataExtractionAgent` with strategy selection
- [ ] Add model capability detection
- [ ] Implement response cleaning (fixes `_clean_github_response` error)
- [ ] Test with all model types

**Day 5: Integration**
- [ ] Update `llm_adapter.py` to use capability-aware agent
- [ ] Maintain backward compatibility
- [ ] Run existing test suite with all models

### **Phase 2: Advanced Model Intelligence (Week 2)**
**Days 1-2: Strategy Optimization**
- [ ] Implement automatic model selection based on requirements
- [ ] Add cost-performance optimization
- [ ] Add error recovery and retry logic
- [ ] Implement fallback chains

**Days 3-4: Performance Monitoring**
- [ ] Add model performance tracking
- [ ] Implement cost monitoring
- [ ] Add quality metrics per model
- [ ] Create model recommendation engine

**Day 5: Testing & Validation**
- [ ] Comprehensive testing across all models
- [ ] Performance benchmarking
- [ ] Cost analysis and optimization
- [ ] Error rate validation

### **Phase 3: OG-RAG Integration (Week 3)**
**Days 1-3: Advanced Capabilities**
- [ ] Extend agent for complex query handling
- [ ] Add workflow orchestration for multi-step reasoning
- [ ] Integrate with semantic retrieval
- [ ] Prepare for SPARQL-like query patterns

**Days 4-5: Production Readiness**
- [ ] Complete error handling and monitoring
- [ ] Final performance optimization
- [ ] Documentation completion
- [ ] Deployment preparation

---

## 🎯 **Enhanced Success Criteria**

### **Technical Metrics:**
- ✅ All existing tests pass across all models
- ✅ GitHub extraction error rate < 1% for each model type
- ✅ Processing time optimized per model capability
- ✅ Automatic model selection accuracy > 95%
- ✅ Structured output success rate > 98% (GPT-4o), > 90% (others)

### **Model-Specific Targets:**
- **GPT-4o**: Use function calling, expect 98%+ structured success
- **DeepSeek-V3**: Use JSON mode, expect 90%+ with post-processing
- **Ollama**: Use structured API, expect 85%+ with simple schemas
- **Legacy**: Guided prompting, expect 75%+ with keyword fallback

---

## 💡 **Key Architectural Decisions**

### **1. Single Agent vs Multiple Model Agents**
**Decision**: Single `DataExtractionAgent` with multiple strategies
**Rationale**: 
- Simpler configuration management
- Easier testing and maintenance
- Natural fallback chain implementation
- Consistent interface across models

### **2. Model Capability Detection**
**Decision**: Configuration-driven capability mapping
**Rationale**:
- Clear documentation of model differences
- Easy to update as models evolve
- Predictable behavior for testing
- Supports automatic optimization

### **3. Response Cleaning Strategy**
**Decision**: Model-specific cleaning in agent
**Rationale**:
- Fixes immediate `_clean_github_response` issue
- Handles model-specific response patterns
- Centralizes cleanup logic
- Enables model-specific validation

This enhanced approach directly addresses the structured output differences between models while maintaining the simplicity and benefits of the agent architecture.