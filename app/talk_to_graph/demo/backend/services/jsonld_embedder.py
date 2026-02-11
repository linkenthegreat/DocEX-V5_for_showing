"""Custom embedder for JSON-LD stakeholder data"""
import sys
from pathlib import Path
import json
from typing import List, Dict
import uuid

# Add project root to path
backend_dir = Path(__file__).parent.parent
demo_dir = backend_dir.parent
talk_to_graph_dir = demo_dir.parent
app_dir = talk_to_graph_dir.parent
project_root = app_dir.parent
sys.path.insert(0, str(project_root))

from app.database_modules.vector_db_manager import DocEXVectorManager
from qdrant_client.models import PointStruct

class JSONLDStakeholderEmbedder:
    """Embed stakeholder data from JSON-LD files into Qdrant"""
    
    def __init__(self, vector_manager: DocEXVectorManager = None):
        self.vector_manager = vector_manager or DocEXVectorManager()
        self.jsonld_dir = project_root / 'database' / 'jsonld'
        self.collection_name = 'stakeholder_data'
        
    def embed_all_stakeholders(self) -> Dict:
        """Embed all stakeholders from JSON-LD files"""
        print(f"📚 Embedding stakeholders from: {self.jsonld_dir}")
        
        # Ensure collection exists
        self._ensure_collection()
        
        jsonld_files = list(self.jsonld_dir.glob("*.json"))
        total_stakeholders = 0
        processed_files = 0
        errors = []
        
        for jsonld_file in jsonld_files:
            try:
                print(f"\n   Processing: {jsonld_file.name}")
                count = self._embed_single_file(jsonld_file)
                total_stakeholders += count
                processed_files += 1
                print(f"   ✅ Embedded {count} stakeholders")
                
            except Exception as e:
                error_msg = f"Error with {jsonld_file.name}: {str(e)}"
                print(f"   ❌ {error_msg}")
                errors.append(error_msg)
        
        print(f"\n🎉 Complete!")
        print(f"   Files processed: {processed_files}/{len(jsonld_files)}")
        print(f"   Total stakeholders: {total_stakeholders}")
        
        return {
            'success': True,
            'files_processed': processed_files,
            'total_files': len(jsonld_files),
            'total_stakeholders': total_stakeholders,
            'errors': errors
        }
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            self.vector_manager.qdrant_client.get_collection(self.collection_name)
            print(f"✅ Collection '{self.collection_name}' already exists")
        except:
            print(f"📦 Creating collection '{self.collection_name}'...")
            from qdrant_client.models import VectorParams, Distance
            
            self.vector_manager.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=384,  # all-MiniLM-L6-v2 dimension
                    distance=Distance.COSINE
                )
            )
            print(f"✅ Collection created")
    
    def _embed_single_file(self, jsonld_file: Path) -> int:
        """Embed stakeholders from a single JSON-LD file"""
        with open(jsonld_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        doc_title = data.get('dcterms:title', jsonld_file.stem)
        doc_format = data.get('dcterms:format', 'unknown')
        stakeholders = data.get('extractedStakeholders', [])
        
        if not stakeholders:
            print(f"      No stakeholders found")
            return 0
        
        points = []
        
        for idx, stakeholder in enumerate(stakeholders):
            # Create rich text representation
            text = self._create_stakeholder_text(stakeholder, doc_title)
            
            # Generate embedding
            embedding = self.vector_manager.embed_text(text)
            
            # Create point
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    'type': 'stakeholder',
                    'doc_title': doc_title,
                    'doc_format': doc_format,
                    'name': stakeholder.get('name', 'Unknown'),
                    'role': stakeholder.get('role', ''),
                    'stakeholder_type': stakeholder.get('stakeholderType', ''),
                    'organization': stakeholder.get('organization', ''),
                    'contact': stakeholder.get('contactInformation', ''),
                    'source_text': stakeholder.get('sourceText', ''),
                    'text': text,  # Full searchable text
                    'doc_id': jsonld_file.stem
                }
            )
            points.append(point)
        
        # Batch upload to Qdrant
        self.vector_manager.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return len(points)
    
    def _create_stakeholder_text(self, stakeholder: Dict, doc_title: str) -> str:
        """Create searchable text from stakeholder data"""
        parts = [f"Document: {doc_title}"]
        
        name = stakeholder.get('name', 'Unknown')
        parts.append(f"Stakeholder: {name}")
        
        if stakeholder.get('role'):
            parts.append(f"Role: {stakeholder['role']}")
        
        if stakeholder.get('stakeholderType'):
            parts.append(f"Type: {stakeholder['stakeholderType']}")
        
        if stakeholder.get('organization'):
            parts.append(f"Organization: {stakeholder['organization']}")
        
        if stakeholder.get('contactInformation'):
            parts.append(f"Contact: {stakeholder['contactInformation']}")
        
        if stakeholder.get('sourceText'):
            parts.append(f"Context: {stakeholder['sourceText']}")
        
        return "\n".join(parts)