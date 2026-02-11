<!-- Update adr_006_implementation_checklist.md -->
# ADR-006 Implementation Checklist
## Model-Capability-Driven Agent System

## Phase 1: Model-Capability Foundation (Week 1)

### Day 1-2: Model Analysis & Configuration Setup
- [ ] **Research & Document Model Capabilities**
  - [ ] Test GPT-4o function calling capabilities
  - [ ] Test DeepSeek JSON mode behavior  
  - [ ] Test Ollama structured output API
  - [ ] Document capability matrix in agents.yaml

- [ ] **Create Model-Specific Configurations**
  - [ ] Create `app/llm/ai_agents/configs/agents.yaml` with model strategies
  - [ ] Create `app/llm/ai_agents/configs/schemas/stakeholder_function_schema.json` (GPT-4o)
  - [ ] Create `app/llm/ai_agents/configs/schemas/stakeholder_ollama_schema.json` (Ollama)
  - [ ] Create `app/llm/ai_agents/configs/prompts/deepseek_extraction_template.md`
  - [ ] Create `app/llm/ai_agents/configs/prompts/ollama_guided_extraction.md`

- [ ] **Test Configuration Loading**
  - [ ] Implement basic config loader
  - [ ] Test YAML parsing
  - [ ] Validate schema files
  - [ ] Test prompt template loading

### Day 3-4: Data Extraction Agent Development
- [ ] **Implement Core Agent Class**
  - [ ] Create `app/llm/ai_agents/data_extraction_agent.py`
  - [ ] Implement model capability detection
  - [ ] Implement strategy selection logic
  - [ ] Add fallback chain mechanism

- [ ] **Implement Model-Specific Strategies**
  - [ ] `_execute_function_calling()` for GPT-4o
  - [ ] `_execute_json_mode()` for DeepSeek  
  - [ ] `_execute_ollama_structured()` for Ollama
  - [ ] `_execute_guided_json()` for legacy models

- [ ] **Implement Response Cleaning (Fixes Current Issue)**
  - [ ] `_clean_structured_response()` for GPT-4o
  - [ ] `_clean_deepseek_response()` for DeepSeek (fixes `_clean_github_response` error)
  - [ ] `_standardize_ollama_response()` for Ollama
  - [ ] `_clean_guided_json_response()` for legacy

- [ ] **Test Agent with Existing Modules**
  - [ ] Test with `app.llm.github_models_processor`
  - [ ] Test with `app.llm.llm_client`
  - [ ] Validate all response cleaning methods
  - [ ] Test fallback chains

### Day 5: Integration & Compatibility
- [ ] **Create Agent Orchestrator**
  - [ ] Create `app/llm/ai_agents/agent_orchestrator.py`
  - [ ] Implement agent instance management
  - [ ] Add workflow execution logic
  - [ ] Maintain backward compatibility interface

- [ ] **Update LLM Adapter**
  - [ ] Modify `app/extraction/adapters/llm_adapter.py` (700→150 lines)
  - [ ] Replace direct processor calls with agent orchestration
  - [ ] Keep existing method signatures for compatibility
  - [ ] Add agent selection options

- [ ] **Integration Testing**
  - [ ] Run existing test suite
  - [ ] Test GitHub Models extraction specifically
  - [ ] Test Ollama extraction if available
  - [ ] Fix any integration issues

## Phase 2: Advanced Model Intelligence (Week 2)

### Days 1-2: Model Selection & Optimization
- [ ] **Implement Smart Model Selection**
  - [ ] Cost-based selection logic
  - [ ] Quality-based selection logic  
  - [ ] Speed-based selection logic
  - [ ] Privacy-based selection (local vs cloud)

- [ ] **Add Performance Monitoring**
  - [ ] Track extraction success rates per model
  - [ ] Monitor response times per model
  - [ ] Track cost per extraction
  - [ ] Log error rates and types

- [ ] **Error Recovery Enhancement**
  - [ ] Improve retry logic with exponential backoff
  - [ ] Add temperature variation on retries
  - [ ] Implement cross-model fallback
  - [ ] Add detailed error logging

### Days 3-4: Advanced Features
- [ ] **Model Capability Auto-Detection**
  - [ ] Runtime model capability testing
  - [ ] Dynamic strategy adjustment
  - [ ] Model availability checking
  - [ ] Capability caching

- [ ] **Cost & Performance Optimization**
  - [ ] Implement cost tracking per model
  - [ ] Add performance benchmarking
  - [ ] Create model recommendation engine
  - [ ] Add usage analytics

### Day 5: Testing & Validation
- [ ] **Comprehensive Model Testing**
  - [ ] Test all models with identical documents
  - [ ] Compare output quality across models
  - [ ] Benchmark performance metrics
  - [ ] Validate cost calculations

- [ ] **Load Testing**
  - [ ] Test concurrent extractions
  - [ ] Test failover scenarios
  - [ ] Test rate limiting
  - [ ] Validate error recovery

## Phase 3: OG-RAG Foundation (Week 3)

### Days 1-3: Advanced Workflows
- [ ] **Query Decomposition Preparation**
  - [ ] Extend agent config for complex queries
  - [ ] Add workflow orchestration patterns
  - [ ] Design multi-step reasoning workflows
  - [ ] Plan SPARQL-like query patterns

- [ ] **Semantic Retrieval Integration**
  - [ ] Integrate with `app.embedding.semantic_retriever`
  - [ ] Add context-aware extraction workflows
  - [ ] Implement hybrid vector + symbolic reasoning
  - [ ] Test knowledge graph preparation patterns

### Days 4-5: Production Readiness
- [ ] **Monitoring & Observability**
  - [ ] Add comprehensive logging
  - [ ] Implement performance metrics
  - [ ] Add health checks
  - [ ] Create monitoring dashboards

- [ ] **Documentation & Deployment**
  - [ ] Complete API documentation
  - [ ] Create deployment guides
  - [ ] Write troubleshooting guides
  - [ ] Prepare for production deployment

## Success Criteria Validation

### Technical Validation
- [ ] **All Existing Tests Pass**
  - [ ] GitHub Models extraction tests
  - [ ] Ollama extraction tests (if available)
  - [ ] Integration tests with existing pipeline
  - [ ] Performance regression tests

- [ ] **Model-Specific Success Rates**
  - [ ] GPT-4o: >98% structured output success
  - [ ] DeepSeek-V3: >90% JSON parsing success  
  - [ ] Ollama: >85% structured output success
  - [ ] Legacy: >75% guided JSON success

- [ ] **Performance Targets**
  - [ ] Processing time maintained (<30 seconds)
  - [ ] Error rate <1% across all models
  - [ ] Automatic model selection accuracy >95%
  - [ ] Fallback success rate >90%

### Business Validation
- [ ] **Cost Optimization**
  - [ ] 30-50% cost reduction through model selection
  - [ ] Detailed cost tracking and reporting
  - [ ] ROI analysis for different model strategies

- [ ] **Development Velocity**
  - [ ] Easy addition of new models via config
  - [ ] Simplified testing with isolated agents
  - [ ] Faster debugging with clear error paths

## Risk Mitigation Checklist
- [ ] **Backward Compatibility Maintained**
  - [ ] All existing interfaces preserved
  - [ ] Gradual migration path available
  - [ ] Rollback strategy documented

- [ ] **Error Handling Robust**
  - [ ] Multiple fallback strategies tested
  - [ ] Graceful degradation verified
  - [ ] Error recovery scenarios validated

- [ ] **Performance Impact Minimal**
  - [ ] No significant latency increase
  - [ ] Memory usage within acceptable limits
  - [ ] CPU usage optimized

This enhanced checklist addresses the specific technical challenges of handling different model capabilities while maintaining the architectural benefits of the agent system.