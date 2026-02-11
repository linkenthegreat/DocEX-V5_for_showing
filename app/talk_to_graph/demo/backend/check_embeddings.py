"""Check what's embedded in the vector database"""
import sys
from pathlib import Path
import json

# Add project root to path
backend_dir = Path(__file__).parent
demo_dir = backend_dir.parent
talk_to_graph_dir = demo_dir.parent
app_dir = talk_to_graph_dir.parent
project_root = app_dir.parent
sys.path.insert(0, str(project_root))

from app.database_modules.vector_db_manager import DocEXVectorManager

print("="*60)
print("CHECKING VECTOR DATABASE STATUS")
print("="*60)

# Initialize vector manager
vm = DocEXVectorManager()

# Check collections
collections = vm.qdrant_client.get_collections()
print(f"\n📚 Collections found: {len(collections.collections)}")

for collection in collections.collections:
    print(f"\n{'='*60}")
    print(f"Collection: {collection.name}")
    print(f"{'='*60}")
    
    try:
        # Get collection info
        info = vm.qdrant_client.get_collection(collection.name)
        print(f"   Vectors: {info.vectors_count}")
        print(f"   Status: {info.status}")
        
        # Sample some points
        print(f"\n   Sampling 3 points...")
        scroll_result = vm.qdrant_client.scroll(
            collection_name=collection.name,
            limit=3,
            with_payload=True,
            with_vectors=False
        )
        
        points = scroll_result[0]
        for i, point in enumerate(points, 1):
            print(f"\n   Point {i}:")
            print(f"      ID: {point.id}")
            print(f"      Payload keys: {list(point.payload.keys())}")
            
            # Print payload details
            for key, value in point.payload.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"      {key}: {value[:100]}...")
                else:
                    print(f"      {key}: {value}")
        
    except Exception as e:
        print(f"   Error: {e}")

# Check JSON-LD files
print(f"\n{'='*60}")
print("JSON-LD FILES")
print(f"{'='*60}")

jsonld_dir = project_root / 'database' / 'jsonld'
jsonld_files = list(jsonld_dir.glob("*.json"))

print(f"\nFound {len(jsonld_files)} JSON-LD files:")

for jsonld_file in jsonld_files:
    print(f"\n   File: {jsonld_file.name}")
    
    try:
        with open(jsonld_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"      Title: {data.get('dcterms:title', 'N/A')}")
        print(f"      Format: {data.get('dcterms:format', 'N/A')}")
        
        # Check for stakeholders
        stakeholders = data.get('extractedStakeholders', [])
        print(f"      Stakeholders: {len(stakeholders)}")
        
        if stakeholders:
            print(f"      Sample stakeholders:")
            for sh in stakeholders[:3]:
                print(f"         - {sh.get('name', 'Unknown')}: {sh.get('role', 'N/A')}")
        
        # Check for paragraphs
        paragraphs = data.get('extractedParagraphs', [])
        print(f"      Paragraphs: {len(paragraphs)}")
        
    except Exception as e:
        print(f"      Error reading: {e}")

print(f"\n{'='*60}")
print("RECOMMENDATION")
print(f"{'='*60}")

# Check if we need to re-embed
if len(collections.collections) == 0:
    print("\n⚠️  No collections found!")
    print("   Run: POST http://localhost:5001/api/llm/embed")
elif any(c.name == 'document_paragraphs' for c in collections.collections):
    print("\n✅ document_paragraphs collection exists")
    print("   This collection should contain stakeholder information")
else:
    print("\n⚠️  document_paragraphs collection not found")
    print("   Re-embedding may be needed")