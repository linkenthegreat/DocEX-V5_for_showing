# ADR-010: Ontology Integration Strategy for LLM Agents

## Status
**PROPOSED** - Under Active Discussion

## Date
2025-01-16

## Context

Following ADR-009's discussion on natural language graph queries, we identified the need for LLMs to understand our ontology structure. Two architectural approaches emerged:

1. **Approach A**: Convert ontologies (TTL/JSON-LD) → YAML/MD schemas (as discussed in ADR-009 Q3)
2. **Approach B**: Embed ontologies directly in vector DB as `@ontology` entities with instruction prompts

This ADR explores both approaches to determine the optimal strategy for DocEX.

---

## Problem Statement

**Goal**: Enable LLM agents to understand and query our knowledge graph structure effectively.

**Key Questions:**
- Should we convert ontologies to LLM-friendly formats (YAML/MD)?
- Or embed ontologies directly in vector DB and instruct LLMs to reference them?
- Which approach provides better accuracy, maintainability, and performance?

---

## Approach A: Convert Ontologies to YAML/MD Schemas

### **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                     Ontology Layer (Source of Truth)         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ stakeholder  │  │  document    │  │   docex      │      │
│  │ -ontology    │  │  _meta       │  │  -ontology   │      │
│  │  .ttl        │  │  .json       │  │   .ttl       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ↓
                    [Auto-Converter]
                    (OntologyConverter)
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              LLM-Friendly Schema Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ stakeholder  │  │  document    │  │   docex      │      │
│  │ _schema      │  │  _meta       │  │  _schema     │      │
│  │  .yaml       │  │  _schema.yaml│  │   .yaml      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ stakeholder  │  │  document    │  │   docex      │      │
│  │  .md         │  │  _meta.md    │  │   .md        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                          ↓
                    [LLM Agents Load]
                    (System Prompt)
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Agent Memory                              │
│  "You understand the following ontology structure:          │
│   - Stakeholder: hasName, hasRole, stakeholderType...       │
│   - Document: dcterms:title, docex:hasParagraph...          │
│   Use these property names when querying the graph."        │
└─────────────────────────────────────────────────────────────┘
```

### **Implementation Example**

```yaml
# config/schemas/stakeholder_schema.yaml
ontology:
  name: "Stakeholder Engagement Ontology"
  version: "1.0"
  namespace: "https://docex.org/vocab/stakeholder/"

classes:
  Stakeholder:
    description: "Individual or organization involved in project"
    properties:
      - name
      - stakeholderType
      - role
      - organization
      - confidenceScore
    
property_mappings:
  natural_language_to_rdf:
    "stakeholder name": "vocab:name"
    "stakeholder type": "vocab:stakeholderType"
    "role": "vocab:role"
    "works at": "vocab:organization"

query_patterns:
  find_by_role:
    nl_template: "Find stakeholders with role {role}"
    sparql_pattern: "?s vocab:role ?role . FILTER(CONTAINS(LCASE(?role), '{role}'))"
```

**Agent System Prompt:**
```python
system_prompt = f"""You are a knowledge graph query assistant.

# Ontology Knowledge
{load_yaml('config/schemas/stakeholder_schema.yaml')}

When user asks questions:
1. Identify entities and properties from the ontology above
2. Map natural language to RDF property names
3. Use the query patterns as templates

Example:
User: "Find accessibility advocates"
Your thinking: 
- Entity: Stakeholder
- Property to search: 'role'
- RDF property: vocab:role
- Query pattern: find_by_role
"""
```

### **Advantages ✅**

| Advantage | Impact | Reasoning |
|-----------|--------|-----------|
| **Optimized Format** | ⭐⭐⭐⭐⭐ | YAML/MD designed for human/LLM readability |
| **Smaller Context** | ⭐⭐⭐⭐⭐ | Compressed, no RDF boilerplate |
| **Fast Loading** | ⭐⭐⭐⭐⭐ | Direct file load, no vector search needed |
| **Explicit Mappings** | ⭐⭐⭐⭐ | Clear NL → RDF property translation |
| **Query Templates** | ⭐⭐⭐⭐ | Pre-built SPARQL patterns |
| **Version Control** | ⭐⭐⭐⭐⭐ | YAML/MD diffs easy to track in Git |

### **Challenges ⚠️**

| Challenge | Impact | Mitigation |
|-----------|--------|-----------|
| **Manual Sync** | ⭐⭐⭐ | Auto-converter eliminates this |
| **Two Layers** | ⭐⭐ | Converter maintains consistency |
| **Build Step** | ⭐⭐ | Auto-run on startup/commit hook |

---

## Approach B: Embed Ontology in Vector Database

### **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                 Unified Vector Database                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Collection: ontology_definitions                      │  │
│  │                                                        │  │
│  │  {                                                     │  │
│  │    "@type": "@ontology",                              │  │
│  │    "name": "StakeholderOntology",                     │  │
│  │    "classes": [...],                                  │  │
│  │    "properties": [...],                               │  │
│  │    "vector": [0.123, 0.456, ...]                      │  │
│  │  }                                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Collection: document_data                             │  │
│  │                                                        │  │
│  │  {                                                     │  │
│  │    "@type": "Stakeholder",                            │  │
│  │    "name": "Jason Moore",                             │  │
│  │    "role": "Accessibility Advocate",                  │  │
│  │    "vector": [0.789, 0.012, ...]                      │  │
│  │  }                                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### **Implementation Example**

```python
# Embed ontology as special entity in vector DB
def embed_ontology_definition(ontology_jsonld_path):
    """Store ontology as searchable entity in vector DB"""
    
    with open(ontology_jsonld_path, 'r') as f:
        ontology_data = json.load(f)
    
    # Create searchable text representation
    ontology_text = f"""
    Ontology: {ontology_data.get('ontology_name', 'Unknown')}
    
    Classes:
    {format_classes(ontology_data.get('classes', {}))}
    
    Properties:
    {format_properties(ontology_data.get('properties', {}))}
    
    This ontology defines the structure of our knowledge graph.
    All data entities follow this schema.
    """
    
    # Generate embedding
    vector = embedder.encode(ontology_text)
    
    # Store in vector DB with special type
    vector_db.upsert(
        collection_name="ontology_definitions",
        points=[{
            "id": "ontology:stakeholder",
            "vector": vector.tolist(),
            "payload": {
                "@type": "@ontology",
                "ontology_name": "StakeholderOntology",
                "ontology_data": ontology_data,
                "schema_version": "1.0",
                "last_updated": datetime.now().isoformat()
            }
        }]
    )
```

**Agent Query Flow:**
```python
async def query_with_embedded_ontology(user_question: str):
    """Query using embedded ontology reference"""
    
    # Step 1: Retrieve relevant ontology
    ontology_results = vector_db.search(
        collection_name="ontology_definitions",
        query_text="knowledge graph schema structure",
        limit=1
    )
    
    ontology_context = ontology_results[0].payload['ontology_data']
    
    # Step 2: Build instruction prompt
    instruction_prompt = f"""You are querying a knowledge graph.

# IMPORTANT: Follow this ontology structure
{json.dumps(ontology_context, indent=2)}

The data you query follows this exact schema.
- All property names must match the ontology
- All class types must match the ontology
- Use the defined relationships only

User question: {user_question}

Based on the ontology above, construct your query."""
    
    # Step 3: Search actual data with schema awareness
    data_results = vector_db.search(
        collection_name="document_data",
        query_text=user_question,
        limit=5
    )
    
    # Step 4: LLM generates answer with ontology context
    answer = await llm.generate(
        prompt=instruction_prompt,
        context=data_results,
        system="Answer based on ontology structure and provided data"
    )
    
    return answer
```

### **Advantages ✅**

| Advantage | Impact | Reasoning |
|-----------|--------|-----------|
| **Single Source** | ⭐⭐⭐⭐⭐ | No conversion layer needed |
| **Semantic Search** | ⭐⭐⭐⭐ | Can find relevant ontology parts |
| **Dynamic Loading** | ⭐⭐⭐⭐ | LLM retrieves only needed schema |
| **Unified System** | ⭐⭐⭐⭐ | Everything in vector DB |
| **No Build Step** | ⭐⭐⭐⭐⭐ | Direct JSON-LD storage |

### **Challenges ⚠️**

| Challenge | Impact | Mitigation |
|-----------|--------|-----------|
| **Larger Context** | ⭐⭐⭐⭐ | Full JSON-LD verbose, eats tokens |
| **Retrieval Overhead** | ⭐⭐⭐ | Every query needs ontology fetch |
| **Less Optimized** | ⭐⭐⭐ | JSON-LD not designed for LLM reading |
| **Complex Prompting** | ⭐⭐⭐⭐ | "Follow @ontology" less clear |
| **Vector Noise** | ⭐⭐ | Ontology vectors mixed with data |

---

## Detailed Comparison Matrix

### **Technical Comparison**

| Aspect | Approach A: Converted YAML/MD | Approach B: Embedded @ontology | Winner |
|--------|------------------------------|--------------------------------|--------|
| **Token Efficiency** | ~500 tokens (compressed) | ~2000 tokens (full JSON-LD) | **A** ⭐⭐⭐⭐⭐ |
| **Load Time** | <1ms (file load) | ~50ms (vector search) | **A** ⭐⭐⭐⭐ |
| **Maintenance** | Auto-convert on change | Direct update | **B** ⭐⭐⭐ |
| **LLM Clarity** | Explicit YAML structure | "Follow @ontology" instruction | **A** ⭐⭐⭐⭐⭐ |
| **Version Control** | Clear YAML diffs | JSON-LD diffs | **A** ⭐⭐⭐⭐ |
| **Semantic Search** | N/A (direct load) | Can search for schema parts | **B** ⭐⭐⭐ |
| **Complexity** | Two-layer system | Single storage | **B** ⭐⭐⭐⭐ |
| **Query Templates** | Pre-built patterns | Generate on-the-fly | **A** ⭐⭐⭐⭐ |

### **Example: Token Usage Comparison**

**Approach A (YAML Schema):**
```yaml
# ~500 tokens
classes:
  Stakeholder:
    properties: [name, role, stakeholderType, organization]
    relationships: [collaboratesWith, belongsToOrganization]

property_mappings:
  "name": "vocab:name"
  "role": "vocab:role"
```

**Approach B (JSON-LD Ontology):**
```json
// ~2000 tokens
{
  "@context": {
    "@vocab": "https://docex.org/vocab/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#"
  },
  "@graph": [
    {
      "@id": "vocab:Stakeholder",
      "@type": "owl:Class",
      "rdfs:label": "Stakeholder",
      "rdfs:comment": "Represents any person, group, or organization...",
      "rdfs:subClassOf": "vocab:Entity"
    },
    {
      "@id": "vocab:name",
      "@type": "owl:DatatypeProperty",
      "rdfs:label": "name",
      "rdfs:domain": "vocab:Stakeholder",
      "rdfs:range": "xsd:string",
      "rdfs:comment": "Name of the stakeholder entity"
    },
    // ... many more verbose definitions
  ]
}
```

**Impact:** Approach A uses **4x fewer tokens** per query!

---

## Hybrid Approach: Best of Both Worlds? 🤔

### **Option C: Layered Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Ontology Source (Git)                     │
│  stakeholder-ontology.ttl, document_meta.json               │
└─────────────────────────────────────────────────────────────┘
                          ↓
                    [Auto-Converter]
                          ↓
    ┌─────────────────────────────────────────┐
    │                                          │
    ↓                                          ↓
┌──────────────────┐              ┌────────────────────────┐
│ YAML/MD Schemas  │              │ Vector DB Embeddings   │
│ (For LLM System  │              │ (For Semantic Search)  │
│  Prompts)        │              │                        │
│                  │              │  - Full ontology text  │
│  - Compressed    │              │  - Class definitions   │
│  - Query patterns│              │  - Property examples   │
│  - NL mappings   │              │                        │
└──────────────────┘              └────────────────────────┘
         ↓                                    ↓
    [Load at Init]                    [Search at Runtime]
         ↓                                    ↓
┌─────────────────────────────────────────────────────────────┐
│              Agent with Hybrid Knowledge                     │
│                                                              │
│  System Memory:                   Dynamic Retrieval:         │
│  - YAML schema (fast)             - Search: "What are       │
│  - Query templates                   stakeholder types?"     │
│  - Property mappings              - Returns: Enum values    │
│                                     from ontology           │
└─────────────────────────────────────────────────────────────┘
```

### **Hybrid Implementation**

```python
class HybridOntologyAgent:
    def __init__(self):
        # Load compressed schema for system prompt (Approach A)
        self.schema = load_yaml('config/schemas/stakeholder_schema.yaml')
        
        # Also have access to full ontology in vector DB (Approach B)
        self.vector_db = VectorDBManager()
    
    async def query(self, user_question: str):
        # Step 1: Use YAML schema in system prompt (fast, token-efficient)
        system_prompt = f"""You understand this ontology:
{yaml.dump(self.schema, default_flow_style=False)}

Use these property names and query patterns when answering."""
        
        # Step 2: If complex question, search vector DB for ontology details
        if self._is_complex_schema_question(user_question):
            ontology_details = self.vector_db.search(
                collection="ontology_definitions",
                query_text=user_question,
                limit=1
            )
            
            # Augment context with detailed ontology info
            system_prompt += f"\n\nAdditional Schema Details:\n{ontology_details}"
        
        # Step 3: Query data with schema-aware prompt
        data_results = self.vector_db.search(
            collection="document_data",
            query_text=user_question,
            limit=5
        )
        
        # Step 4: Generate answer
        answer = await self.llm.generate(
            system=system_prompt,
            context=data_results,
            question=user_question
        )
        
        return answer
    
    def _is_complex_schema_question(self, question: str) -> bool:
        """Detect if question needs detailed ontology lookup"""
        schema_keywords = [
            "what types", "what properties", "what relationships",
            "valid values", "ontology structure", "schema definition"
        ]
        return any(kw in question.lower() for kw in schema_keywords)
```

### **Hybrid Advantages**

✅ **Token Efficient**: YAML schema in system prompt (500 tokens)
✅ **Semantically Searchable**: Full ontology in vector DB when needed
✅ **Fast Queries**: Most queries use cached YAML, no vector search
✅ **Deep Dive Capable**: Complex questions fetch detailed ontology
✅ **Single Source of Truth**: Both derived from same ontology files

---

## Performance Benchmarks (Estimated)

### **Simple Query: "Find accessibility advocates"**

| Approach | Tokens Used | Latency | Cost |
|----------|-------------|---------|------|
| **A: YAML Schema** | 500 + 200 (data) = 700 | 1.2s | $0.0007 |
| **B: Embedded @ontology** | 2000 + 200 (data) = 2200 | 1.5s | $0.0022 |
| **C: Hybrid** | 500 + 200 (data) = 700 | 1.2s | $0.0007 |

**Winner: Approach A or C (tied)** ⭐⭐⭐⭐⭐

### **Complex Query: "What are all valid stakeholder types with their descriptions?"**

| Approach | Tokens Used | Latency | Cost |
|----------|-------------|---------|------|
| **A: YAML Schema** | 500 (schema has it!) | 1.0s | $0.0005 |
| **B: Embedded @ontology** | 2000 + 500 (search) = 2500 | 1.8s | $0.0025 |
| **C: Hybrid** | 500 + 1000 (detailed fetch) = 1500 | 1.4s | $0.0015 |

**Winner: Approach A** ⭐⭐⭐⭐⭐

### **Schema Evolution: Ontology Updated**

| Approach | Update Process | Risk |
|----------|---------------|------|
| **A: YAML Schema** | Auto-convert (2s) → Restart agents | Low |
| **B: Embedded @ontology** | Re-embed to vector DB (30s) | Medium (cache invalidation) |
| **C: Hybrid** | Both above | Medium |

**Winner: Approach A** ⭐⭐⭐⭐

---

## Decision Recommendation

### **RECOMMENDED: Approach A (Converted YAML/MD) + Optional Hybrid Enhancement**

#### **Primary Strategy: Approach A**

**Implement Now:**
```bash
# Week 1: Core converter
python -m app.cli convert-all --ontology-dir ontology --output-dir config/schemas

# Result: Clean YAML schemas for all agents
```

**Why Approach A Wins:**
1. ✅ **4x Token Efficiency**: 500 tokens vs 2000 tokens
2. ✅ **Faster Queries**: Direct load vs vector search
3. ✅ **Clearer LLM Instructions**: YAML is explicit
4. ✅ **Better Query Templates**: Pre-built SPARQL patterns
5. ✅ **Version Control**: Clean Git diffs
6. ✅ **Production Ready**: Proven pattern (AutoGPT, LangChain use this)

#### **Optional Enhancement: Hybrid (Approach C)**

**Add Later if Needed:**
- Embed full ontology descriptions in vector DB
- Use for complex schema questions only
- Keeps token efficiency for 95% of queries

#### **When to Use Approach B (Embedded @ontology)?**

Only consider if:
- ❓ Ontology changes extremely frequently (hourly)
- ❓ Need semantic search across ontology definitions
- ❓ Want truly unified storage layer

**For DocEX: Approach A is optimal** ✅

---

## Implementation Plan

### **Phase 1: Core Converter (This Week) - 10 hours**

```python
# 1. Implement OntologyConverter class
# 2. Add CLI commands
# 3. Auto-convert on startup
# 4. Generate YAML + Markdown

# Result:
config/schemas/
├── stakeholder_schema.yaml
├── document_meta_schema.yaml
├── docex_schema.yaml
└── LLM-instruction/
    ├── stakeholder.md
    ├── document_meta.md
    └── docex.md
```

### **Phase 2: Agent Integration (Next Week) - 8 hours**

```python
# Update agent system prompts to load YAML schemas
class SchemaAwareAgent:
    def __init__(self):
        self.schemas = {
            'stakeholder': load_yaml('config/schemas/stakeholder_schema.yaml'),
            'document': load_yaml('config/schemas/document_meta_schema.yaml')
        }
    
    def build_system_prompt(self):
        return f"""You understand these ontologies:
        
# Stakeholder Ontology
{self.format_schema(self.schemas['stakeholder'])}

# Document Ontology  
{self.format_schema(self.schemas['document'])}

Use these structures when querying the knowledge graph."""
```

### **Phase 3 (Optional): Hybrid Enhancement - 6 hours**

Only if complex schema queries show limitations:
```python
# Add vector search for detailed ontology lookups
# Keep YAML for 95% of queries
```

---

## Consequences

### **Positive**

✅ **Token Efficiency**: 4x reduction in context size
✅ **Query Performance**: Faster agent responses
✅ **Maintainability**: Auto-conversion eliminates sync issues
✅ **Developer Experience**: Clean YAML diffs in Git
✅ **Agent Clarity**: Explicit schema structure
✅ **Cost Savings**: Lower LLM API costs

### **Negative (Mitigated)**

⚠️ **Build Step Required**: Auto-convert on startup
⚠️ **Two Storage Layers**: Converter maintains consistency
⚠️ **No Semantic Ontology Search**: Can add via Hybrid approach

### **Risks**

⚠️ **Ontology Changes**: Mitigated by auto-converter
⚠️ **Schema Sync**: Mitigated by single source of truth
⚠️ **Complex Ontologies**: Test with large ontologies (>100K triples)

---

## Success Metrics

### **Performance Targets**

- [ ] Schema loading: <50ms per agent
- [ ] Token usage: <800 tokens per query (incl. schema)
- [ ] Query accuracy: 90%+ with schema-aware prompts
- [ ] Conversion time: <5s for all ontologies

### **Maintainability Targets**

- [ ] Zero manual schema updates
- [ ] 100% auto-conversion success rate
- [ ] Clear Git diffs for ontology changes

---

## Related ADRs

- **ADR-009**: Natural Language Graph Query System (parent decision)
- **ADR-005**: Vector Database Integration
- **ADR-003**: RDF/JSON-LD Document Storage

---

## Final Recommendation Summary

**Primary Approach: A (Converted YAML/MD Schemas)** ✅

**Implementation Order:**
1. **This Week**: Build OntologyConverter (10 hours)
2. **Next Week**: Integrate with agents (8 hours)
3. **Optional**: Add hybrid vector search if needed (6 hours)

**Why Not Approach B (Embedded @ontology)?**
- ❌ 4x more tokens per query
- ❌ Slower (vector search overhead)
- ❌ Less clear for LLMs ("follow @ontology" ambiguous)
- ❌ Mixed concerns (ontology + data in same vector space)

**Approach B is elegant but not optimal for our use case.**

**Decision: Proceed with Approach A** 🎯

---

**Status**: Ready for implementation
**Next Steps**: 
1. Create `app/utils/ontology_converter.py`
2. Run batch conversion: `python -m app.cli convert-all`
3. Update agent system prompts to load YAML schemas
4. Test with real queries

**Estimated Time to Production**: 18 hours (1-2 weeks part-time)