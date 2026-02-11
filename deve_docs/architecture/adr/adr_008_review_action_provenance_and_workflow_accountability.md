# ADR-008: Review Action Provenance and Workflow Accountability

## Status
**APPROVED** - URI-based linking with separate graphs approach

## Context
- Unified frontend integration (ADR-007) successfully implemented
- Review system functional but lacks provenance tracking
- Critical gap: User modifications not recorded in RDF graph
- Compliance requirement: Full audit trail for research/legal environments
- **Key Insight**: URI linking eliminates need for graph merging

## Problem Statement
Current workflow: Extract → Review → Save lacks accountability tracking and provenance linking between metadata and extraction graphs.

## User Proposed Workflow
Document metadata extraction → save RDF into JSON-LD {file_directory.json} → embed into vector database → user clicks the extraction button → LLM extracts the "content" from the RDF (metadata) → The LLM makes an extraction based on ontology (stakeholder engagement for this POC) → The result is saved into JSON-LD as {file_name_llm_analysis.json} → Display the result for user to review/edit → user verify/edit the result → add additional tag "user preference" into the extracted RDF {file_name_llm_analysis.json} → when user save the result of review a popup box to check if user want to combine the graph{file_directory.json} and {file_name_llm_analysis.json} to a single graph {file_directory_result_update.json}

## Decision Options Evaluated

### Option 1: Graph Merging Approach
- Combine metadata + extraction into single graph file
- **Rejected**: Complex merging logic, versioning difficulties

### Option 2: URI-Based Linking with Separate Graphs ✅ **SELECTED**
- Keep metadata and extraction as separate JSON-LD files
- Link via consistent URI scheme
- Embed both graphs separately in vector database
- **Benefits**: Clean separation, easy versioning, efficient updates

### Option 3: Hybrid Embedding Strategy
- Embed metadata graph for LLM context optimization
- Embed extraction graph for semantic search
- **Benefits**: Optimal performance, clear data lifecycle

## Recommended Solution

### **Architecture: Separate Graphs with URI Linking**

```
Graph Structure:
├── file_directory.json (Document Metadata Graph)
│   ├── @id: "docx:harvest_hearth_2024"
│   ├── hasAnalysis: "docx:harvest_hearth_2024/analysis"
│   └── Vector Embedding: Yes (for LLM context)
│
├── file_name_llm_analysis.json (Extraction Graph) 
│   ├── @id: "docx:harvest_hearth_2024/analysis"
│   ├── analyzedDocument: "docx:harvest_hearth_2024"
│   ├── Vector Embedding: Yes (for semantic search)
│   └── User Provenance: Review actions tracked here
│
└── Optional: file_directory_result_update.json (Combined View)
    └── @graph: [metadata + extraction] (for export/visualization)
```

### **URI Linking Strategy**
```json
// file_directory.json (Metadata Graph)
{
  "@context": {...},
  "@id": "docx:harvest_hearth_2024",
  "@type": "Document",
  "hasAnalysis": "docx:harvest_hearth_2024/analysis",
  "analysisStatus": "completed"
}

// file_name_llm_analysis.json (Extraction Graph)
{
  "@context": {...},
  "@id": "docx:harvest_hearth_2024/analysis", 
  "@type": "StakeholderExtraction",
  "analyzedDocument": "docx:harvest_hearth_2024",
  "stakeholders": [...],
  "reviewHistory": [
    {
      "@type": "ReviewAction",
      "@id": "docx:harvest_hearth_2024/review/001",
      "reviewer": "user:alice",
      "timestamp": "2025-08-16T14:30:00Z",
      "action": "stakeholder_modified",
      "originalValue": "Sarah Chen",
      "reviewedValue": "Dr. Sarah Chen",
      "rationale": "Added professional title"
    }
  ]
}
```

## Implementation Plan

### **Phase 1: Core URI Linking (2 hours) 🚀**

**Files to Update:**
1. `app/routes/agent_api.py` - Update extraction results with URI links
2. `app/utils/rdf_utils.py` - Add URI generation utilities  
3. `app/static/js/review.js` - Add provenance capture
4. Test with existing files

**Key Changes:**
```python
# app/utils/rdf_utils.py
def generate_document_uri(filename):
    """Generate consistent URI for documents"""
    safe_name = filename.replace('.', '_').replace(' ', '_').replace('&', '_')
    return f"https://docex.org/vocab/document/{safe_name}"

def link_extraction_to_document(extraction_data, document_filename):
    """Add URI links between extraction and document"""
    doc_uri = generate_document_uri(document_filename)
    extraction_data["@id"] = f"{doc_uri}/analysis"
    extraction_data["analyzedDocument"] = doc_uri
    return extraction_data
```

### **Phase 2: Review Provenance (1 hour) 🔧**

**Review Modal Enhancement:**
```javascript
// Add rationale field to review actions
function saveStakeholderEdit() {
    const reviewAction = {
        "@type": "ReviewAction",
        "@id": `${current_extraction_uri}/review/${Date.now()}`,
        "reviewer": `user:${getCurrentUser()}`,
        "timestamp": new Date().toISOString(),
        "action": "stakeholder_modified",
        "originalValue": originalStakeholder.name,
        "reviewedValue": editedStakeholder.name,
        "rationale": document.getElementById('changeRationale').value
    };
    
    // Add to extraction graph's reviewHistory
    addReviewActionToGraph(reviewAction);
}
```

### **Phase 3: Vector Database Integration (30 minutes) ⚡**

**Dual Embedding Strategy:**
```python
# Embed metadata graph for LLM context
vector_db.embed_document(
    doc_id=document_uri,
    content=metadata_graph,
    type="document_metadata"
)

# Embed extraction graph for semantic search  
vector_db.embed_document(
    doc_id=f"{document_uri}/analysis",
    content=extraction_graph,
    type="stakeholder_extraction"
)
```

## Module Impact Analysis

### **Minimal Changes Required:**

**Backend Modules:**
- ✅ `app/routes/agent_api.py` - Add URI linking (5 lines)
- ✅ `app/utils/rdf_utils.py` - Add URI utilities (20 lines)
- ✅ `app/routes/main.py` - Update file processing (minimal)

**Frontend Modules:**  
- ✅ `app/static/js/review.js` - Add provenance capture (30 lines)
- ✅ `app/templates/review_modal.html` - Add rationale field (5 lines)

**New Modules:**
- ✅ `app/utils/provenance_utils.py` - Review action tracking (50 lines)

**Total Code Changes: ~110 lines** 🎯

## Quick Implementation for POC Demo

### **Step 1: Update Extraction Results (15 minutes)**
```python
# app/routes/agent_api.py - In generate_mock_extraction_results()
def generate_mock_extraction_results(job):
    doc_uri = f"https://docex.org/vocab/document/{job.filename.replace('.', '_')}"
    
    result = {
        "@context": {...},
        "@id": f"{doc_uri}/analysis",
        "analyzedDocument": doc_uri,  # 🔗 URI Link
        "extractionMetadata": {...},
        "stakeholders": [...],
        "reviewHistory": []  # 📋 Ready for provenance
    }
    return result
```

### **Step 2: Add Review Rationale Field (5 minutes)**
```html
<!-- In review_modal.html edit stakeholder form -->
<div class="form-group">
    <label for="changeRationale">Reason for Change (Optional):</label>
    <textarea id="changeRationale" placeholder="Why are you making this change?"></textarea>
</div>
```

### **Step 3: Capture Review Actions (10 minutes)**
```javascript
// In review.js - Update saveStakeholderEdit()
function saveStakeholderEdit() {
    // ... existing code ...
    
    // Add review action to history
    const reviewAction = {
        "@type": "ReviewAction",
        "timestamp": new Date().toISOString(),
        "action": "modified",
        "field": "name", 
        "oldValue": original_name,
        "newValue": new_name,
        "rationale": document.getElementById('changeRationale').value || "No reason provided"
    };
    
    // Add to current extraction data
    if (!ReviewState.currentData.reviewHistory) {
        ReviewState.currentData.reviewHistory = [];
    }
    ReviewState.currentData.reviewHistory.push(reviewAction);
    
    console.log('✅ Review action recorded:', reviewAction);
}
```

## Expected Results

### **Immediate Benefits:**
- ✅ **Clean Architecture**: Separate graphs linked by URIs  
- ✅ **Full Provenance**: Every review action tracked
- ✅ **Efficient Vector DB**: Optimal embedding strategy
- ✅ **Simple Implementation**: Minimal code changes
- ✅ **Demo Ready**: Working POC in 30 minutes

### **Technical Validation:**
```json
// Extraction graph will show:
{
  "@id": "docx:harvest_hearth_2024/analysis",
  "analyzedDocument": "docx:harvest_hearth_2024",
  "reviewHistory": [
    {
      "@type": "ReviewAction",
      "timestamp": "2025-08-16T14:30:00Z",
      "action": "modified",
      "rationale": "Added professional title for accuracy"
    }
  ]
}
```

## Consequences

### **Positive:**
- **Scalable**: Each document can have multiple analyses
- **Maintainable**: Clear separation of concerns
- **Compliant**: Full audit trail for research/legal requirements
- **Efficient**: Vector database optimized for each graph type
- **User-Friendly**: Optional graph combination for export

### **Risks & Mitigation:**
- **URI Consistency**: Mitigated by utility functions
- **Link Integrity**: Validated during file operations
- **Performance**: Minimal impact, separate graphs are more efficient

## Decision Rationale

The URI-based linking approach is superior because:
1. **No complex graph merging logic required**
2. **Natural RDF/JSON-LD linking pattern**
3. **Efficient vector database strategy**
4. **Clear data lifecycle and versioning**
5. **Minimal implementation complexity**

This approach transforms DocEX into a production-ready semantic research platform with full accountability while maintaining architectural simplicity.

## Success Metrics
- [ ] Every extraction links to source document via URI
- [ ] All review actions recorded in extraction graph
- [ ] Vector database contains both metadata and extraction embeddings
- [ ] Demo shows end-to-end provenance tracking
- [ ] POC validates approach for production deployment
