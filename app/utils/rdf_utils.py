"""
Enhanced RDF Utility Functions Module - JSON-LD Native

This module provides comprehensive utilities for creating, manipulating, and querying
RDF graphs using JSON-LD as the primary format, with full ontology integration.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from rdflib import Graph, Literal, RDF, URIRef, Namespace, BNode
from rdflib.namespace import DCTERMS, XSD, RDFS
from flask import current_app

try:
    import pyld
    from pyld import jsonld
    PYLD_AVAILABLE = True
except ImportError:
    PYLD_AVAILABLE = False
    print("Warning: pyld not available. Some JSON-LD features will be limited.")

# Define namespaces
DOCEX = Namespace("http://example.org/docex/")
STAKEHOLDER = Namespace("http://www.example.org/stakeholder-ontology#")
CONTENT = Namespace("http://www.w3.org/2011/content#")
PROV = Namespace("http://www.w3.org/ns/prov#")
SCHEMA = Namespace("http://schema.org/")

class JSONLDOntologyManager:
    """Manages JSON-LD ontology loading and context operations"""
    
    def __init__(self):
        self.ontology_context = None
        self.ontology_graph = None
        self.ontology_loaded = False
        
    def load_ontology(self) -> Dict[str, Any]:
        """Load JSON-LD ontology from file"""
        if self.ontology_loaded:
            return self.ontology_context
            
        try:
            # Load document meta ontology
            doc_ontology_path = Path(current_app.config['BASE_DIR']) / 'ontology' / 'document_meta_ontology.json'
            stakeholder_ontology_path = Path(current_app.config['BASE_DIR']) / 'ontology' / 'stakeholder_engagement_ontology.json'
            
            combined_context = {
                "@context": {}
            }
            
            # Load document meta ontology
            if doc_ontology_path.exists():
                with open(doc_ontology_path, 'r', encoding='utf-8') as f:
                    doc_ontology = json.load(f)
                    if "@context" in doc_ontology:
                        combined_context["@context"].update(doc_ontology["@context"])
                    current_app.logger.info(f"Loaded document meta ontology from {doc_ontology_path}")
            
            # Load stakeholder ontology if available
            if stakeholder_ontology_path.exists():
                with open(stakeholder_ontology_path, 'r', encoding='utf-8') as f:
                    stakeholder_ontology = json.load(f)
                    if "@context" in stakeholder_ontology:
                        combined_context["@context"].update(stakeholder_ontology["@context"])
                    current_app.logger.info(f"Loaded stakeholder ontology from {stakeholder_ontology_path}")
            
            self.ontology_context = combined_context["@context"]
            self.ontology_loaded = True
            
            current_app.logger.info(f"Combined ontology context loaded with {len(self.ontology_context)} terms")
            return self.ontology_context
            
        except Exception as e:
            current_app.logger.error(f"Error loading JSON-LD ontology: {str(e)}")
            # Fallback minimal context
            self.ontology_context = {
                "docex": "http://example.org/docex/",
                "stakeholder": "http://www.example.org/stakeholder-ontology#",
                "dcterms": "http://purl.org/dc/terms/",
                "schema": "http://schema.org/",
                "prov": "http://www.w3.org/ns/prov#"
            }
            return self.ontology_context
    
    def get_context(self) -> Dict[str, Any]:
        """Get the loaded ontology context"""
        if not self.ontology_loaded:
            return self.load_ontology()
        return self.ontology_context
    
    def extract_document_attributes(self) -> List[str]:
        """Extract document-related attributes from ontology"""
        context = self.get_context()
        doc_attributes = []
        
        for term, definition in context.items():
            if isinstance(definition, dict):
                if definition.get("@type") == "@id" and "docex:" in str(definition.get("@id", "")):
                    doc_attributes.append(term)
            elif isinstance(definition, str) and "docex:" in definition:
                doc_attributes.append(term)
                
        return doc_attributes
    
    def extract_stakeholder_attributes(self) -> List[str]:
        """Extract stakeholder-related attributes from ontology"""
        context = self.get_context()
        stakeholder_attributes = []
        
        for term, definition in context.items():
            if isinstance(definition, dict):
                if definition.get("@type") == "@id" and "stakeholder:" in str(definition.get("@id", "")):
                    stakeholder_attributes.append(term)
            elif isinstance(definition, str) and "stakeholder:" in definition:
                stakeholder_attributes.append(term)
                
        return stakeholder_attributes

# Global ontology manager instance
ontology_manager = JSONLDOntologyManager()

def initialize_graph() -> Graph:
    """Initialize a new RDF graph with JSON-LD support and common namespaces"""
    g = Graph()
    
    # Bind namespaces for better readability
    g.bind("docex", DOCEX)
    g.bind("stakeholder", STAKEHOLDER)
    g.bind("dcterms", DCTERMS)
    g.bind("content", CONTENT)
    g.bind("prov", PROV)
    g.bind("schema", SCHEMA)
    g.bind("rdfs", RDFS)
    
    return g

def create_jsonld_document_metadata(file_path: str, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create JSON-LD document metadata using ontology context"""
    
    # Get ontology context
    context = ontology_manager.get_context()
    
    # Create document ID
    doc_id = f"doc_{hashlib.md5(file_path.encode()).hexdigest()[:12]}"
    
    # Base JSON-LD structure
    jsonld_doc = {
        "@context": context,
        "@id": f"docex:{doc_id}",
        "@type": "docex:Document",
        "dcterms:title": file_metadata.get('name', ''),
        "dcterms:format": file_metadata.get('file_type', ''),
        "dcterms:extent": file_metadata.get('size', 0),
        "docex:filePath": file_path,
        "docex:documentID": doc_id
    }
    
    # Add timestamps
    if 'create_date' in file_metadata:
        try:
            create_date = datetime.strptime(file_metadata['create_date'], '%Y-%m-%d %H:%M:%S')
            jsonld_doc["dcterms:created"] = create_date.isoformat()
        except ValueError:
            pass
    
    if 'modified_date' in file_metadata:
        try:
            modified_date = datetime.strptime(file_metadata['modified_date'], '%Y-%m-%d %H:%M:%S')
            jsonld_doc["dcterms:modified"] = modified_date.isoformat()
        except ValueError:
            pass
    
    # Add file hash
    if file_metadata.get('file_hash'):
        jsonld_doc["docex:fileHash"] = file_metadata['file_hash']
    
    # Add processing metadata
    jsonld_doc["prov:generatedAtTime"] = datetime.now(timezone.utc).isoformat()
    jsonld_doc["prov:wasGeneratedBy"] = {
        "@id": "docex:DocEXSystem",
        "@type": "prov:Agent",
        "schema:name": "DocEX Document Processing System"
    }
    
    return jsonld_doc

def enhance_jsonld_with_structure(jsonld_doc: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Add document structure to JSON-LD document"""
    
    try:
        from .document_utils import get_document_structure
        
        current_app.logger.info(f"Adding document structure to JSON-LD for {file_path}")
        
        # Get document structure
        document_structure = get_document_structure(file_path)
        
        # Add structure to JSON-LD
        paragraphs = []
        para_count = len(document_structure.get("paragraphs", []))
        total_sentences = 0
        
        for para_index, para in enumerate(document_structure.get("paragraphs", [])):
            para_data = {
                "@id": f"docex:{para['id']}",
                "@type": "docex:DocumentParagraph",
                "docex:paragraphID": para["id"],
                "docex:paragraphNumber": para_index + 1,
                "docex:textContent": para["text"],
                "docex:characterCount": len(para["text"]),
                "docex:wordCount": len(para["text"].split())
            }
            
            # Add sentences
            sentences = []
            for sent_index, sentence in enumerate(para.get("sentences", [])):
                sent_data = {
                    "@id": f"docex:{sentence['id']}",
                    "@type": "docex:DocumentSentence",
                    "docex:sentenceID": sentence["id"],
                    "docex:sentenceNumber": sent_index + 1,
                    "docex:textContent": sentence["text"],
                    "docex:characterCount": len(sentence["text"]),
                    "docex:wordCount": len(sentence["text"].split())
                }
                sentences.append(sent_data)
                total_sentences += 1
            
            if sentences:
                para_data["docex:hasSentence"] = sentences
                para_data["docex:sentenceCount"] = len(sentences)
            
            paragraphs.append(para_data)
        
        # Add paragraphs to document
        if paragraphs:
            jsonld_doc["docex:hasParagraph"] = paragraphs
            jsonld_doc["docex:paragraphCount"] = para_count
            jsonld_doc["docex:sentenceCount"] = total_sentences
        
        current_app.logger.info(f"Added {para_count} paragraphs and {total_sentences} sentences to JSON-LD")
        
    except Exception as e:
        current_app.logger.error(f"Error adding document structure: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
    
    return jsonld_doc

def jsonld_to_rdf_graph(jsonld_doc: Dict[str, Any]) -> Graph:
    """Convert JSON-LD document to RDF Graph"""
    
    g = initialize_graph()
    
    try:
        # Serialize JSON-LD as string and parse into graph
        jsonld_str = json.dumps(jsonld_doc, ensure_ascii=False, indent=2)
        g.parse(data=jsonld_str, format="json-ld")
        
        current_app.logger.info(f"Converted JSON-LD to RDF graph with {len(g)} triples")
        
    except Exception as e:
        current_app.logger.error(f"Error converting JSON-LD to RDF: {str(e)}")
        # Fallback: manually add core triples
        doc_uri = URIRef(jsonld_doc.get("@id", ""))
        if doc_uri:
            g.add((doc_uri, RDF.type, DOCEX.Document))
            if jsonld_doc.get("dcterms:title"):
                g.add((doc_uri, DCTERMS.title, Literal(jsonld_doc["dcterms:title"])))
    
    return g

def save_jsonld_document(jsonld_doc: Dict[str, Any], filename: str) -> str:
    """Save JSON-LD document to file"""
    
    jsonld_dir = Path(current_app.config.get('JSONLD_DIR', current_app.config['DATABASE_DIR'] + '/jsonld'))
    jsonld_dir.mkdir(parents=True, exist_ok=True)
    
    jsonld_path = jsonld_dir / f"{filename}.json"
    
    try:
        with open(jsonld_path, 'w', encoding='utf-8') as f:
            json.dump(jsonld_doc, f, ensure_ascii=False, indent=2)
        
        current_app.logger.info(f"Saved JSON-LD document to {jsonld_path}")
        return str(jsonld_path)
        
    except Exception as e:
        current_app.logger.error(f"Error saving JSON-LD document: {str(e)}")
        raise

def load_jsonld_document(filename: str) -> Optional[Dict[str, Any]]:
    """Load JSON-LD document from file"""
    
    jsonld_dir = Path(current_app.config.get('JSONLD_DIR', current_app.config['DATABASE_DIR'] + '/jsonld'))
    jsonld_path = jsonld_dir / f"{filename}.json"
    
    if not jsonld_path.exists():
        return None
    
    try:
        with open(jsonld_path, 'r', encoding='utf-8') as f:
            jsonld_doc = json.load(f)
        
        current_app.logger.info(f"Loaded JSON-LD document from {jsonld_path}")
        return jsonld_doc
        
    except Exception as e:
        current_app.logger.error(f"Error loading JSON-LD document: {str(e)}")
        return None

def get_all_jsonld_files() -> List[Dict[str, Any]]:
    """Get a list of all JSON-LD files with their details"""
    
    jsonld_dir = Path(current_app.config.get('JSONLD_DIR', current_app.config['DATABASE_DIR'] + '/jsonld'))
    
    if not jsonld_dir.exists():
        return []
    
    result = []
    for file_path in sorted(jsonld_dir.glob("*.json")):
        try:
            file_stats = file_path.stat()
            file_size = file_stats.st_size
            modified_time = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # Try to load and count entities
            with open(file_path, 'r', encoding='utf-8') as f:
                jsonld_doc = json.load(f)
            
            # Count entities (documents, stakeholders, etc.)
            entity_count = 1  # The document itself
            if "@graph" in jsonld_doc:
                entity_count = len(jsonld_doc["@graph"])
            elif isinstance(jsonld_doc, list):
                entity_count = len(jsonld_doc)
            
            result.append({
                'filename': file_path.name,
                'size': file_size,
                'modified': modified_time,
                'entities': entity_count,
                'format': 'JSON-LD'
            })
            
        except Exception as e:
            current_app.logger.error(f"Error reading JSON-LD file {file_path.name}: {str(e)}")
            result.append({
                'filename': file_path.name,
                'size': 0,
                'modified': 'Unknown',
                'entities': 'Error',
                'format': 'JSON-LD'
            })
    
    return result

def execute_sparql_on_jsonld(query_string: str, jsonld_files: List[str] = None) -> tuple:
    """Execute SPARQL query on JSON-LD files"""
    
    jsonld_dir = Path(current_app.config.get('JSONLD_DIR', current_app.config['DATABASE_DIR'] + '/jsonld'))
    
    if jsonld_files is None:
        # Get all JSON-LD files
        jsonld_files = [f.name for f in jsonld_dir.glob("*.json")]
    
    if not jsonld_files:
        return None, "No JSON-LD files found"
    
    try:
        # Create combined graph from JSON-LD files
        combined_graph = initialize_graph()
        
        for filename in jsonld_files:
            jsonld_path = jsonld_dir / filename
            if jsonld_path.exists():
                try:
                    current_app.logger.info(f"Loading JSON-LD file: {jsonld_path}")
                    combined_graph.parse(str(jsonld_path), format="json-ld")
                    current_app.logger.info(f"Loaded {filename}, graph now has {len(combined_graph)} triples")
                except Exception as e:
                    current_app.logger.error(f"Error loading JSON-LD file {filename}: {str(e)}")
        
        if len(combined_graph) == 0:
            return [], "No data loaded from JSON-LD files"
        
        # Execute SPARQL query
        current_app.logger.info(f"Executing SPARQL query on {len(combined_graph)} triples")
        results = combined_graph.query(query_string)
        
        # Process results
        result_list = []
        vars_list = [str(var) for var in results.vars] if results.vars else []
        
        for row in results:
            row_dict = {}
            for j, var in enumerate(vars_list):
                try:
                    value = row[j] if j < len(row) else None
                    row_dict[var] = str(value) if value is not None else ''
                except Exception as e:
                    current_app.logger.error(f"Error extracting value for {var}: {e}")
                    row_dict[var] = f"[ERROR: {str(e)}]"
            result_list.append(row_dict)
        
        current_app.logger.info(f"Query returned {len(result_list)} results")
        return result_list, vars_list
        
    except Exception as e:
        current_app.logger.error(f"SPARQL query error: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return None, f"Error executing query: {str(e)}"

def convert_file_to_jsonld(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert file data to JSON-LD format with full metadata and structure"""
    
    file_path = file_data.get('path')
    
    # Create base JSON-LD document
    jsonld_doc = create_jsonld_document_metadata(file_path, file_data)
    
    # Add file content if available
    content = file_data.get('content', '')
    if content and not content.startswith('[Error'):
        jsonld_doc["docex:textContent"] = content
        
        # Check if this is a document type we can structure
        file_type = file_data.get('file_type', '')
        is_document = (
            file_type and (
                file_type.endswith('/pdf') or 
                file_type.endswith('/msword') or 
                file_type.endswith('officedocument.wordprocessingml.document') or
                file_type.endswith('/plain') or 
                file_type.endswith('/markdown')
            )
        )
        
        # Add document structure
        if is_document:
            jsonld_doc = enhance_jsonld_with_structure(jsonld_doc, file_path)
    
    return jsonld_doc

# ===== BACKWARD COMPATIBILITY FUNCTIONS FOR V4 PRINT =====

def create_file_metadata_ggraph(file_path: str, file_metadata: Dict[str, Any]) -> Graph:
    """Create file metadata graph (backward compatibility function)"""
    try:
        # Create JSON-LD document first
        jsonld_doc = create_jsonld_document_metadata(file_path, file_metadata)
        
        # Convert to RDF graph
        graph = jsonld_to_rdf_graph(jsonld_doc)
        
        current_app.logger.info(f"Created metadata graph with {len(graph)} triples for {file_path}")
        return graph
        
    except Exception as e:
        current_app.logger.error(f"Error creating metadata graph: {str(e)}")
        # Return empty graph as fallback
        return initialize_graph()

def create_file_metadata_graph(file_path: str, file_metadata: Dict[str, Any]) -> Graph:
    """Alias for create_file_metadata_ggraph (backward compatibility)"""
    return create_file_metadata_ggraph(file_path, file_metadata)

def add_file_content(g: Graph, file_uri: URIRef, content: str) -> Graph:
    """Add file content to the graph (backward compatibility)"""
    if content:
        g.add((file_uri, CONTENT.chars, Literal(content)))
    return g

def add_ffile_content(g: Graph, file_uri: URIRef, content: str) -> Graph:
    """Add file content to the graph (backward compatibility - typo version)"""
    return add_file_content(g, file_uri, content)

def merge_graphs(graphs: List[Graph]) -> Graph:
    """Merge multiple RDF graphs into one (backward compatibility)"""
    merged_graph = initialize_graph()
    
    for g in graphs:
        if g:
            merged_graph += g
    
    return merged_graph

def ttl_exists(filename: str) -> bool:
    """Check if a TTL/JSON-LD file exists (backward compatibility)"""
    # Check both TTL and JSON-LD locations
    triples_dir = Path(current_app.config['TRIPLES_DIR'])
    jsonld_dir = Path(current_app.config.get('JSONLD_DIR', current_app.config['DATABASE_DIR'] + '/jsonld'))
    
    ttl_path = triples_dir / f"{filename}.ttl"
    jsonld_path = jsonld_dir / f"{filename}.json"
    
    return ttl_path.exists() or jsonld_path.exists()

def get_document_ttl_content(filename: str) -> Optional[str]:
    """Get document content in TTL format (backward compatibility)"""
    try:
        # Load JSON-LD document
        jsonld_doc = load_jsonld_document(filename.replace('.ttl', '').replace('.jsonld', ''))
        if not jsonld_doc:
            return None
        
        # Convert to RDF graph and serialize as TTL
        graph = jsonld_to_rdf_graph(jsonld_doc)
        ttl_content = graph.serialize(format="turtle")
        
        return ttl_content
        
    except Exception as e:
        current_app.logger.error(f"Error getting TTL content: {str(e)}")
        return None

def get_ttl_content(filename: str) -> Optional[str]:
    """Get the raw content of a TTL file (backward compatibility)"""
    # First try to get from JSON-LD and convert
    ttl_content = get_document_ttl_content(filename)
    if ttl_content:
        return ttl_content
    
    # Fallback to actual TTL file if it exists
    triples_dir = Path(current_app.config['TRIPLES_DIR'])
    file_path = triples_dir / filename
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        current_app.logger.error(f"Error reading TTL file {filename}: {str(e)}")
        return f"Error reading file: {str(e)}"

def remove_ttl_file(filename: str) -> bool:
    """Remove a TTL/JSON-LD file (backward compatibility)"""
    success = False
    
    # Try to remove TTL file
    triples_dir = Path(current_app.config['TRIPLES_DIR'])
    ttl_path = triples_dir / filename
    
    if ttl_path.exists():
        try:
            ttl_path.unlink()
            success = True
        except Exception as e:
            current_app.logger.error(f"Error removing TTL file {filename}: {str(e)}")
    
    # Try to remove corresponding JSON-LD file
    jsonld_dir = Path(current_app.config.get('JSONLD_DIR', current_app.config['DATABASE_DIR'] + '/jsonld'))
    jsonld_filename = filename.replace('.ttl', '.json')
    jsonld_path = jsonld_dir / jsonld_filename
    
    if jsonld_path.exists():
        try:
            jsonld_path.unlink()
            success = True
        except Exception as e:
            current_app.logger.error(f"Error removing JSON-LD file {jsonld_filename}: {str(e)}")
    
    return success

def combine_ttl_files(selected_files: List[str]) -> tuple:
    """Combine multiple TTL/JSON-LD files into a single graph (backward compatibility)"""
    jsonld_dir = Path(current_app.config.get('JSONLD_DIR', current_app.config['DATABASE_DIR'] + '/jsonld'))
    triples_dir = Path(current_app.config['TRIPLES_DIR'])
    
    combined_graph = initialize_graph()
    
    for filename in selected_files:
        # Try JSON-LD first
        jsonld_filename = filename.replace('.ttl', '.json').replace('.jsonld', '.json')
        jsonld_path = jsonld_dir / jsonld_filename
        
        if jsonld_path.exists():
            try:
                current_app.logger.info(f"Loading JSON-LD file: {jsonld_path}")
                combined_graph.parse(str(jsonld_path), format="json-ld")
                current_app.logger.info(f"Successfully loaded {jsonld_filename}, graph now has {len(combined_graph)} triples")
            except Exception as e:
                current_app.logger.error(f"Error loading JSON-LD file {jsonld_filename}: {str(e)}")
        else:
            # Fallback to TTL file
            ttl_path = triples_dir / filename
            if ttl_path.exists():
                try:
                    current_app.logger.info(f"Loading TTL file: {ttl_path}")
                    combined_graph.parse(str(ttl_path), format="turtle")
                    current_app.logger.info(f"Successfully loaded {filename}, graph now has {len(combined_graph)} triples")
                except Exception as e:
                    current_app.logger.error(f"Error loading TTL file {filename}: {str(e)}")
    
    # Save the combined graph
    combined_path = triples_dir / "combined_graph.ttl"
    triples_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        combined_graph.serialize(destination=str(combined_path), format="turtle")
        current_app.logger.info(f"Saved combined graph to {combined_path} with {len(combined_graph)} triples")
    except Exception as e:
        current_app.logger.error(f"Error saving combined graph: {str(e)}")
    
    return combined_graph, str(combined_path)

def execute_sparql_query(query_string: str, selected_files: List[str] = None) -> tuple:
    """Execute SPARQL query (backward compatibility wrapper)"""
    # Convert TTL filenames to JSON-LD if needed
    if selected_files:
        jsonld_files = []
        for filename in selected_files:
            if filename.endswith('.ttl'):
                jsonld_files.append(filename.replace('.ttl', '.json'))
            elif filename.endswith('.jsonld'):
                jsonld_files.append(filename.replace('.jsonld', '.json'))
            else:
                jsonld_files.append(filename)
        return execute_sparql_on_jsonld(query_string, jsonld_files)
    else:
        return execute_sparql_on_jsonld(query_string, selected_files)

def save_graph_to_ttl(g: Graph, filename: str) -> str:
    """Save RDF graph to TTL file (backward compatibility)"""
    triples_dir = Path(current_app.config['TRIPLES_DIR'])
    triples_dir.mkdir(parents=True, exist_ok=True)
    
    ttl_path = triples_dir / f"{filename}.ttl"
    g.serialize(destination=str(ttl_path), format="turtle")
    
    return str(ttl_path)

def get_all_ttl_files():
    """Get TTL files (backward compatibility) - now includes JSON-LD files"""
    ttl_files = []
    jsonld_files = get_all_jsonld_files()
    
    # Convert JSON-LD file info to TTL-like format for compatibility
    for jsonld_file in jsonld_files:
        ttl_files.append({
            'filename': jsonld_file['filename'].replace('.json', '.jsonld'),
            'size': jsonld_file['size'],
            'modified': jsonld_file['modified'],
            'triples': jsonld_file['entities'],
            'format': 'JSON-LD'
        })
    
    # Also include actual TTL files if they exist
    triples_dir = Path(current_app.config['TRIPLES_DIR'])
    if triples_dir.exists():
        for ttl_path in sorted(triples_dir.glob("*.ttl")):
            try:
                file_stats = ttl_path.stat()
                file_size = file_stats.st_size
                modified_time = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # Try to count triples
                try:
                    g = initialize_graph()
                    g.parse(str(ttl_path), format="turtle")
                    triple_count = len(g)
                except Exception:
                    triple_count = "Error"
                    
                ttl_files.append({
                    'filename': ttl_path.name,
                    'size': file_size,
                    'modified': modified_time,
                    'triples': triple_count,
                    'format': 'TTL'
                })
            except Exception as e:
                current_app.logger.error(f"Error reading TTL file {ttl_path.name}: {str(e)}")
    
    return ttl_files

def load_graph_from_ttl(filename: str) -> Optional[Graph]:
    """Load an RDF graph from a TTL/JSON-LD file (backward compatibility)"""
    # Try JSON-LD first
    jsonld_filename = filename.replace('.ttl', '').replace('.jsonld', '')
    jsonld_doc = load_jsonld_document(jsonld_filename)
    if jsonld_doc:
        return jsonld_to_rdf_graph(jsonld_doc)
    
    # Fallback to TTL file
    triples_dir = Path(current_app.config['TRIPLES_DIR'])
    ttl_path = triples_dir / filename
    
    if not ttl_path.exists():
        return None
    
    g = initialize_graph()
    try:
        g.parse(str(ttl_path), format="turtle")
        return g
    except Exception as e:
        current_app.logger.error(f"Error loading TTL file {filename}: {str(e)}")
        return None

def convert_to_rdf(file_data: Dict[str, Any]) -> Graph:
    """Convert file data to RDF (backward compatibility)"""
    jsonld_doc = convert_file_to_jsonld(file_data)
    return jsonld_to_rdf_graph(jsonld_doc)

def get_file_hash_from_ttl(filename: str) -> Optional[str]:
    """Extract the file hash from a TTL/JSON-LD file (backward compatibility)"""
    # Try JSON-LD first
    jsonld_filename = filename.replace('.ttl', '').replace('.jsonld', '')
    jsonld_doc = load_jsonld_document(jsonld_filename)
    if jsonld_doc:
        return jsonld_doc.get('docex:fileHash')
    
    # Fallback to TTL file
    triples_dir = Path(current_app.config['TRIPLES_DIR'])
    file_path = triples_dir / filename
    
    if not file_path.exists():
        return None
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for the docex:hash property in the TTL file
        import re
        hash_match = re.search(r'docex:hash\s+"([^"]+)"', content)
        return hash_match.group(1) if hash_match else None
        
    except Exception as e:
        current_app.logger.error(f"Error reading hash from TTL {filename}: {str(e)}")
        return None

def create_test_graph() -> str:
    """Create a test graph with some sample triples (backward compatibility)"""
    triples_dir = Path(current_app.config['TRIPLES_DIR'])
    triples_dir.mkdir(parents=True, exist_ok=True)
    test_path = triples_dir / "test_graph.ttl"
    
    # Create a simple graph with a few triples
    g = initialize_graph()
    
    # Add some sample data
    g.add((URIRef("http://example.org/person/1"), RDF.type, URIRef("http://example.org/Person")))
    g.add((URIRef("http://example.org/person/1"), URIRef("http://example.org/name"), Literal("Alice")))
    g.add((URIRef("http://example.org/person/1"), URIRef("http://example.org/age"), Literal(30)))
    
    g.add((URIRef("http://example.org/person/2"), RDF.type, URIRef("http://example.org/Person")))
    g.add((URIRef("http://example.org/person/2"), URIRef("http://example.org/name"), Literal("Bob")))
    g.add((URIRef("http://example.org/person/2"), URIRef("http://example.org/age"), Literal(25)))
    
    # Save it
    g.serialize(destination=str(test_path), format="turtle")
    
    return str(test_path)

def initialize_ontology():
    """Initialize ontology (enhanced for JSON-LD)"""
    context = ontology_manager.load_ontology()
    
    # Create RDF graph from JSON-LD context for compatibility
    ontology_graph = initialize_graph()
    
    # Add basic ontology information
    ontology_graph.add((DOCEX.Document, RDF.type, RDFS.Class))
    ontology_graph.add((DOCEX.DocumentParagraph, RDF.type, RDFS.Class))
    ontology_graph.add((DOCEX.DocumentSentence, RDF.type, RDFS.Class))
    
    current_app.logger.info(f"Initialized JSON-LD ontology with {len(context)} context terms")
    
    return DOCEX, ontology_graph

def validate_jsonld_format(jsonld_data):
    """
    Validate that the provided data is proper JSON-LD format
    Returns (is_valid, error_message)
    """
    try:
        # Check for required JSON-LD properties
        if not isinstance(jsonld_data, dict):
            return False, "JSON-LD must be a dictionary/object"
        
        # Check for @context
        if "@context" not in jsonld_data:
            return False, "Missing required @context property"
        
        # Check for @type or @id (at least one should be present)
        if "@type" not in jsonld_data and "@id" not in jsonld_data:
            return False, "Missing both @type and @id properties"
        
        # Try to parse with rdflib to validate structure
        try:
            from rdflib import Graph
            import json
            
            g = Graph()
            jsonld_str = json.dumps(jsonld_data)
            g.parse(data=jsonld_str, format="json-ld")
            
            # If we get here, it's valid JSON-LD
            return True, f"Valid JSON-LD with {len(g)} triples"
            
        except Exception as parse_error:
            return False, f"JSON-LD parsing error: {str(parse_error)}"
            
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def convert_legacy_json_to_jsonld(legacy_data, source_filename):
    """
    Convert legacy JSON extraction results to proper JSON-LD format
    """
    try:
        base_uri = "https://docex.org/vocab/"
        doc_id = source_filename.replace('.', '_').replace(' ', '_').replace('&', '_')
        
        # Handle legacy stakeholders array
        stakeholders_data = []
        legacy_stakeholders = legacy_data.get('stakeholders', [])
        
        for i, stakeholder in enumerate(legacy_stakeholders):
            stakeholder_id = f"stakeholder_{i}_{stakeholder.get('name', 'unknown').lower().replace(' ', '_')}"
            
            jsonld_stakeholder = {
                "@type": "Stakeholder",
                "@id": f"{base_uri}{stakeholder_id}",
                "name": stakeholder.get("name", "Unknown"),
                "stakeholderType": stakeholder.get("stakeholderType", "UNKNOWN"),
                "role": stakeholder.get("role", ""),
                "confidenceScore": stakeholder.get("confidenceScore", 0.5),
                "extractionMethod": stakeholder.get("extractionMethod", "unknown")
            }
            
            # Add organization if present
            if stakeholder.get("organization"):
                org_id = f"org_{stakeholder['organization'].lower().replace(' ', '_')}"
                jsonld_stakeholder["affiliatedWith"] = {
                    "@type": "Organization",
                    "@id": f"{base_uri}{org_id}",
                    "name": stakeholder["organization"]
                }
            
            # Add mentions if source text present
            if stakeholder.get("sourceText"):
                jsonld_stakeholder["mentions"] = [{
                    "@type": "Mention",
                    "text": stakeholder["sourceText"],
                    "confidence": stakeholder.get("confidenceScore", 0.5)
                }]
            
            # Add contact info if present
            if stakeholder.get("contact"):
                jsonld_stakeholder["contactInfo"] = {
                    "@type": "ContactInfo",
                    "email": stakeholder["contact"]
                }
                
            stakeholders_data.append(jsonld_stakeholder)
        
        # Create proper JSON-LD structure
        jsonld_result = {
            "@context": {
                "@vocab": f"{base_uri}",
                "name": "http://schema.org/name",
                "email": "http://schema.org/email", 
                "affiliatedWith": "http://schema.org/affiliation",
                "Stakeholder": "http://schema.org/Person",
                "Organization": "http://schema.org/Organization",
                "Mention": f"{base_uri}Mention",
                "ContactInfo": "http://schema.org/ContactPoint"
            },
            "@type": "StakeholderExtraction",
            "@id": f"{base_uri}extraction/{doc_id}",
            "extractionMetadata": {
                "@type": "ExtractionMetadata",
                **legacy_data.get('metadata', {}),
                "sourceDocument": source_filename,
                "conversionTimestamp": datetime.now().isoformat(),
                "convertedFromLegacy": True
            },
            "stakeholders": stakeholders_data,
            "extractionSummary": {
                "@type": "ExtractionSummary",
                "totalStakeholders": len(stakeholders_data),
                "averageConfidence": sum(s["confidenceScore"] for s in stakeholders_data) / len(stakeholders_data) if stakeholders_data else 0
            }
        }
        
        return jsonld_result
        
    except Exception as e:
        print(f"❌ Error converting legacy JSON to JSON-LD: {e}")
        raise