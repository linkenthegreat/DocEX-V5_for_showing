"""JSON-LD loader for the demo - standalone implementation"""
from rdflib import Graph, Namespace
from pathlib import Path
import json

class JSONLDLoader:
    """Load JSON-LD files into RDF graph"""
    
    def __init__(self):
        # Get path to database/jsonld directory
        backend_dir = Path(__file__).parent.parent
        demo_dir = backend_dir.parent
        talk_to_graph_dir = demo_dir.parent
        app_dir = talk_to_graph_dir.parent
        project_root = app_dir.parent
        
        self.jsonld_dir = project_root / 'database' / 'jsonld'
        print(f"📂 JSON-LD directory: {self.jsonld_dir}")
        
        # Define namespaces
        self.VOCAB = Namespace("http://example.org/vocab#")
        self.DCTERMS = Namespace("http://purl.org/dc/terms/")
        self.DOCEX = Namespace("https://docex.org/vocab/")
        
    def load_all_jsonld(self) -> Graph:
        """Load all JSON-LD files into a single RDF graph"""
        graph = Graph()
        
        # Bind namespaces
        graph.bind("vocab", self.VOCAB)
        graph.bind("dcterms", self.DCTERMS)
        graph.bind("docex", self.DOCEX)
        
        jsonld_files = list(self.jsonld_dir.glob("*.json"))
        print(f"📚 Found {len(jsonld_files)} JSON-LD files")
        
        for jsonld_file in jsonld_files:
            try:
                print(f"   Loading {jsonld_file.name}...")
                
                # Parse JSON-LD directly with rdflib
                with open(jsonld_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Convert JSON-LD to string and parse
                import json as json_module
                jsonld_str = json_module.dumps(json_data)
                graph.parse(data=jsonld_str, format='json-ld')
                
            except Exception as e:
                print(f"   ⚠️  Error loading {jsonld_file.name}: {e}")
                # Try alternative parsing method
                try:
                    graph.parse(str(jsonld_file), format='json-ld')
                except Exception as e2:
                    print(f"   ❌ Failed completely: {e2}")
                    continue
        
        print(f"✅ Loaded {len(graph)} triples total")
        return graph
    
    def get_jsonld_files(self):
        """Get list of all JSON-LD files"""
        return list(self.jsonld_dir.glob("*.json"))