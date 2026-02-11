"""Test script to verify embedding system works"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")

# Test imports
try:
    from app.embedding.document_embedder import DocumentEmbedder
    print("✅ Can import DocumentEmbedder")
except Exception as e:
    print(f"❌ Cannot import DocumentEmbedder: {e}")

try:
    from app.embedding.semantic_retriever import DocEXSemanticRetriever
    print("✅ Can import DocEXSemanticRetriever")
except Exception as e:
    print(f"❌ Cannot import SemanticRetriever: {e}")

# Test JSON-LD files
jsonld_dir = project_root / 'database' / 'jsonld'
print(f"\nJSON-LD directory: {jsonld_dir}")
print(f"Exists: {jsonld_dir.exists()}")

if jsonld_dir.exists():
    files = list(jsonld_dir.glob("*.json"))
    print(f"Found {len(files)} JSON-LD files:")
    for f in files:
        print(f"  - {f.name}")