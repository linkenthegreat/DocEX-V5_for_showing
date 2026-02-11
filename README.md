# DocEX-V5
Transforming DocEx tool with JSON-LD and Vector Database Integration

## Current Status: Phase 3 Vector Database Implementation 🚧

### ✅ Completed Foundations
- **JSON-LD Native Backend**: Rich document structure with semantic metadata
- **Agent-Based Architecture**: Model-capability-driven LLM extraction
- **Multi-Provider Support**: GitHub Models, OpenAI, Ollama integration
- **Dual Storage System**: JSON-LD + TTL formats for optimal compatibility

### 🚧 Current Implementation: Vector Database Integration
- **Vector Database**: Qdrant integration for semantic similarity search
- **Document Embeddings**: JSON-LD to vector conversion pipeline
- **Context-Aware Extraction**: Similar document patterns enhance LLM accuracy
- **Graph Evolution**: Multi-stage embedding strategy for comprehensive knowledge graphs

### 🎯 Enhanced Capabilities (In Development)
- **Semantic Search**: Find similar documents for extraction context
- **Context Visualization**: Human review interface with similarity explanations
- **Performance Optimization**: 15-25% improvement in extraction accuracy expected
- **Future-Proof Architecture**: Foundation for advanced AI/ML workflows

## Quick Start

### Prerequisites
- Python 3.9+
- Qdrant vector database (Docker recommended)
- Required API keys (OpenAI, GitHub Models)

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Start Qdrant (Docker)
docker run -p 6333:6333 qdrant/qdrant

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Usage
```bash
# Start the application
python run.py

# Access web interface
http://localhost:5000

# Vector database status
http://localhost:5000/vector/status
```

## Architecture Overview

### Core Components
- **Document Processing**: PDF/DOCX → JSON-LD with rich metadata
- **LLM Extraction**: Agent-based multi-provider stakeholder extraction
- **Vector Database**: Semantic similarity and context retrieval
- **Human Review**: Context-aware validation and correction interface
- **Knowledge Graphs**: RDF/SPARQL compatibility with semantic enhancement

### Data Flow
```
Documents → JSON-LD → Vector Embeddings → Context Retrieval →
Enhanced LLM Extraction → Human Review → Final Knowledge Graph
```

This represents a significant evolution from basic document processing to intelligent, context-aware semantic analysis.