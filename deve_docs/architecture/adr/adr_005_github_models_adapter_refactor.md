# ADR-005: GitHub Models Adapter Refactor

## Status
Superseded by ADR-006

## Context
The current LLM adapter (`llm_adapter.py`) has grown to over 700 lines and mixes multiple concerns:
- GitHub Models integration
- Ollama integration  
- OpenAI integration
- JSON-LD processing
- Response cleaning and validation

This monolithic approach has led to:
- Difficult debugging and testing
- Missing method implementations (`_clean_github_response`)
- Complex initialization logic
- Hard to add new models
- Mixed provider patterns (factory vs direct instantiation)

Additionally, different GitHub models have different capabilities:
- **GPT-4o**: Excellent structured output, built-in schema validation
- **DeepSeek-V3**: Cost-effective but requires JSON prompting
- **Future models**: Unknown capabilities

## Decision
We will refactor the monolithic LLM adapter into focused, single-responsibility adapters:

### New Architecture:
```
app/extraction/adapters/
├── base_adapter.py              # Common interface and utilities
├── github_models_adapter.py     # 🆕 Dedicated GitHub Models adapter
├── ollama_adapter.py           # Extract Ollama logic
├── openai_adapter.py           # Extract OpenAI logic
├── format_converter.py         # Keep as-is
└── jsonld_extraction_bridge.py # Keep as-is
```

### GitHub Models Adapter Features:
- **Model Selection**: Support GPT-4o, DeepSeek-V3, and future models
- **Capability Detection**: Different strategies for structured vs JSON output
- **Cost Optimization**: Automatic model recommendations based on use case
- **Clean Error Handling**: Proper fallback and retry mechanisms
- **Configuration-Driven**: Easy model switching via config

## Consequences

### Positive:
- **Maintainability**: Smaller, focused modules (~200 lines each)
- **Testability**: Isolated concerns are easier to unit test
- **Extensibility**: Easy to add new models and providers
- **Debuggability**: Clear error paths and logging
- **Performance**: Model-specific optimizations

### Negative:
- **Initial Refactoring Effort**: Need to extract and reorganize existing code
- **Potential Breaking Changes**: Existing imports may need updates
- **Testing Overhead**: More modules to test individually

### Mitigation:
- Maintain backward compatibility through adapter factory
- Comprehensive test suite for each adapter
- Clear migration guide for existing code

## Implementation Plan

### Phase 1: Create GitHub Models Adapter
1. Extract GitHub-specific logic from `llm_adapter.py`
2. Implement model selection and capability detection
3. Add proper error handling and response cleaning
4. Create comprehensive unit tests

### Phase 2: Extract Other Adapters
1. Create `ollama_adapter.py` 
2. Create `openai_adapter.py`
3. Update `base_adapter.py` with common utilities

### Phase 3: Update Integration Layer
1. Update `jsonld_extraction_bridge.py` to use new adapters
2. Create adapter factory for backward compatibility
3. Update documentation and examples

## Notes
- This refactor was superseded by the agent-based architecture approach in ADR-006
- The core issues identified (monolithic adapter, missing methods) are addressed by the agent system
- Model-specific capabilities analysis remains valid and was incorporated into agent design

## References
- ADR-002: GitHub Models Integration
- Current implementation: `app/extraction/adapters/llm_adapter.py`
- GitHub Models SDK documentation