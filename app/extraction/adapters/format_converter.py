"""
Format Conversion Utilities for JSON-LD ↔ TTL

This module provides utilities for converting between JSON-LD and TTL formats
while maintaining semantic consistency and preserving provenance information.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import rdflib
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, RDFS, XSD, DCTERMS
try:
    from pyld import jsonld
except ImportError:
    # Fallback implementation if pyld not available
    jsonld = None

from app.extraction.models import StakeholderExtraction, ExtractedStakeholder


class FormatConverter:
    """
    Bidirectional converter between JSON-LD and TTL formats for stakeholder data
    """
    
    def __init__(self, context_file: str = None):
        """Initialize converter with JSON-LD context"""
        if context_file is None:
            # Find project root and set context file path
            project_root = Path(__file__).parent.parent.parent.parent
            context_file = project_root / "contexts" / "stakeholder_context.json"
        
        self.context_file = str(context_file)
        self.context = self._load_context()
        
        # Define namespaces
        self.STAKEHOLDER = Namespace("http://www.example.org/stakeholder-ontology#")
        self.DOCEX = Namespace("http://example.org/docex/")
        self.PROV = Namespace("http://www.w3.org/ns/prov#")
        self.SCHEMA = Namespace("http://schema.org/")
        
    def _load_context(self) -> Dict[str, Any]:
        """Load JSON-LD context from file"""
        try:
            with open(self.context_file, 'r', encoding='utf-8') as f:
                context_doc = json.load(f)
                return context_doc.get("@context", {})
        except FileNotFoundError:
            # Fallback to basic context if file not found
            return {
                "stakeholder": "http://www.example.org/stakeholder-ontology#",
                "docex": "http://example.org/docex/",
                "prov": "http://www.w3.org/ns/prov#",
                "schema": "http://schema.org/"
            }
    
    def extraction_to_jsonld(self, extraction: StakeholderExtraction) -> Dict[str, Any]:
        """Convert StakeholderExtraction to JSON-LD format"""
        
        # Use the built-in method from the model
        jsonld_data = extraction.to_jsonld()
        
        # Ensure proper context
        if "@context" not in jsonld_data:
            jsonld_data["@context"] = self.context
        
        return jsonld_data
    
    def jsonld_to_ttl(
        self, 
        jsonld_data: Dict[str, Any], 
        output_file: Optional[str] = None
    ) -> str:
        """Convert JSON-LD data to TTL format"""
        
        try:
            if jsonld is None:
                # Fallback implementation without pyld
                return self._simple_jsonld_to_ttl(jsonld_data, output_file)
            
            # Expand JSON-LD to get fully qualified IRIs
            expanded = jsonld.expand(jsonld_data)
            
            # Create RDF graph
            graph = Graph()
            
            # Bind namespaces for cleaner output
            graph.bind("stakeholder", self.STAKEHOLDER)
            graph.bind("docex", self.DOCEX)
            graph.bind("prov", self.PROV)
            graph.bind("schema", self.SCHEMA)
            graph.bind("dcterms", DCTERMS)
            
            # Convert expanded JSON-LD to RDF
            if expanded:
                self._add_jsonld_to_graph(graph, expanded)
            
            # Serialize to TTL
            ttl_content = graph.serialize(format='turtle')
            
            # Write to file if specified
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(ttl_content)
            
            return ttl_content
            
        except Exception as e:
            raise ValueError(f"Failed to convert JSON-LD to TTL: {str(e)}")
    
    def _simple_jsonld_to_ttl(
        self, 
        jsonld_data: Dict[str, Any], 
        output_file: Optional[str] = None
    ) -> str:
        """Simple JSON-LD to TTL conversion without pyld dependency"""
        
        graph = Graph()
        
        # Bind namespaces
        graph.bind("stakeholder", self.STAKEHOLDER)
        graph.bind("docex", self.DOCEX)
        graph.bind("prov", self.PROV)
        graph.bind("schema", self.SCHEMA)
        graph.bind("dcterms", DCTERMS)
        
        # Process @graph array if present
        if "@graph" in jsonld_data:
            for item in jsonld_data["@graph"]:
                self._add_simple_item_to_graph(graph, item, jsonld_data.get("@context", {}))
        else:
            self._add_simple_item_to_graph(graph, jsonld_data, jsonld_data.get("@context", {}))
        
        # Serialize to TTL
        ttl_content = graph.serialize(format='turtle')
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(ttl_content)
        
        return ttl_content
        ttl_content = graph.serialize(format='turtle')
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(ttl_content)
        
        return ttl_content
    
    def _add_simple_item_to_graph(self, graph: Graph, item: Dict[str, Any], context: Dict[str, Any]):
        """Add JSON-LD item to graph using simple expansion"""
        
        if "@id" not in item:
            return
        
        subject = URIRef(self._expand_term(item["@id"], context))
        
        # Add type
        if "@type" in item:
            type_val = item["@type"]
            if isinstance(type_val, list):
                for t in type_val:
                    graph.add((subject, RDF.type, URIRef(self._expand_term(t, context))))
            else:
                graph.add((subject, RDF.type, URIRef(self._expand_term(type_val, context))))
        
        # Add properties
        for prop, value in item.items():
            if prop.startswith("@"):
                continue
            
            predicate = URIRef(self._expand_term(prop, context))
            
            if isinstance(value, list):
                for v in value:
                    self._add_value_to_graph(graph, subject, predicate, v, context)
            else:
                self._add_value_to_graph(graph, subject, predicate, value, context)
    
    def _add_value_to_graph(self, graph: Graph, subject: URIRef, predicate: URIRef, value: Any, context: Dict[str, Any]):
        """Add value to graph with appropriate type handling"""
        
        if isinstance(value, dict):
            if "@id" in value:
                obj = URIRef(self._expand_term(value["@id"], context))
                graph.add((subject, predicate, obj))
            elif "@value" in value:
                literal_val = value["@value"]
                if "@type" in value:
                    datatype = URIRef(self._expand_term(value["@type"], context))
                    graph.add((subject, predicate, Literal(literal_val, datatype=datatype)))
                else:
                    graph.add((subject, predicate, Literal(literal_val)))
        else:
            graph.add((subject, predicate, Literal(value)))
    
    def _expand_term(self, term: str, context: Dict[str, Any]) -> str:
        """Simple term expansion using context"""
        
        if ":" in term:
            prefix, local = term.split(":", 1)
            if prefix in context:
                namespace = context[prefix]
                if isinstance(namespace, str):
                    return namespace + local
                elif isinstance(namespace, dict) and "@id" in namespace:
                    return namespace["@id"] + local
        
        if term in context:
            expanded = context[term]
            if isinstance(expanded, str):
                return expanded
            elif isinstance(expanded, dict) and "@id" in expanded:
                return expanded["@id"]
        
        # Return as-is if no expansion found
        return term
    
    def ttl_to_jsonld(
        self, 
        ttl_content: str, 
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convert TTL content to JSON-LD format"""
        
        try:
            # Parse TTL into RDF graph
            graph = Graph()
            graph.parse(data=ttl_content, format='turtle')
            
            # Convert to JSON-LD
            jsonld_data = self._graph_to_jsonld(graph)
            
            # Apply context
            compacted = jsonld.compact(jsonld_data, self.context)
            
            # Write to file if specified
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(compacted, f, indent=2, ensure_ascii=False)
            
            return compacted
            
        except Exception as e:
            raise ValueError(f"Failed to convert TTL to JSON-LD: {str(e)}")
    
    def _add_jsonld_to_graph(self, graph: Graph, expanded_data: List[Dict[str, Any]]):
        """Add expanded JSON-LD data to RDF graph"""
        
        for item in expanded_data:
            # Handle nested @graph structure
            if "@graph" in item:
                for graph_item in item["@graph"]:
                    self._process_single_item(graph, graph_item)
            else:
                self._process_single_item(graph, item)
    
    def _process_single_item(self, graph: Graph, item: Dict[str, Any]):
        """Process a single JSON-LD item"""
        if "@id" in item:
            subject = URIRef(item["@id"])
        else:
            subject = BNode()
        
        # Add type information
        if "@type" in item:
            types = item["@type"] if isinstance(item["@type"], list) else [item["@type"]]
            for type_uri in types:
                graph.add((subject, RDF.type, URIRef(type_uri)))
        
        # Add properties
        for prop, values in item.items():
            if prop.startswith("@"):
                continue
            
            predicate = URIRef(prop)
            value_list = values if isinstance(values, list) else [values]
            
            for value in value_list:
                if isinstance(value, dict):
                    if "@id" in value:
                        # Object property
                        graph.add((subject, predicate, URIRef(value["@id"])))
                    elif "@value" in value:
                        # Data property with type
                        literal_value = value["@value"]
                        if "@type" in value:
                            datatype = URIRef(value["@type"])
                            graph.add((subject, predicate, Literal(literal_value, datatype=datatype)))
                        else:
                            graph.add((subject, predicate, Literal(literal_value)))
                else:
                    # Simple literal
                    graph.add((subject, predicate, Literal(value)))
    
    def _graph_to_jsonld(self, graph: Graph) -> Dict[str, Any]:
        """Convert RDF graph to JSON-LD format"""
        
        # Serialize graph to JSON-LD
        jsonld_str = graph.serialize(format='json-ld')
        return json.loads(jsonld_str)
    
    def create_ttl_document(
        self, 
        extraction: StakeholderExtraction,
        original_ttl_content: Optional[str] = None
    ) -> str:
        """
        Create complete TTL document with extraction results
        Preserves original document metadata if provided
        """
        
        # Convert extraction to JSON-LD first
        jsonld_data = self.extraction_to_jsonld(extraction)
        
        # Convert to TTL
        extraction_ttl = self.jsonld_to_ttl(jsonld_data)
        
        # If original TTL exists, merge with new extraction
        if original_ttl_content:
            ttl_content = self._merge_ttl_content(original_ttl_content, extraction_ttl)
        else:
            ttl_content = extraction_ttl
        
        # Add document-level metadata
        ttl_content = self._add_document_metadata(ttl_content, extraction)
        
        return ttl_content
    
    def _merge_ttl_content(self, original_ttl: str, extraction_ttl: str) -> str:
        """Merge original document TTL with extraction results"""
        
        # Parse both graphs
        original_graph = Graph()
        original_graph.parse(data=original_ttl, format='turtle')
        
        extraction_graph = Graph()
        extraction_graph.parse(data=extraction_ttl, format='turtle')
        
        # Merge graphs
        merged_graph = original_graph + extraction_graph
        
        # Bind namespaces
        for prefix, namespace in extraction_graph.namespaces():
            merged_graph.bind(prefix, namespace)
        
        return merged_graph.serialize(format='turtle')
    
    def _add_document_metadata(self, ttl_content: str, extraction: StakeholderExtraction) -> str:
        """Add document-level metadata to TTL content"""
        
        # Parse existing graph
        graph = Graph()
        graph.parse(data=ttl_content, format='turtle')
        
        # Create document URI
        doc_hash = hashlib.md5(extraction.document_id.encode()).hexdigest()
        doc_uri = URIRef(f"docex:document/{doc_hash}")
        
        # Add document metadata
        graph.add((doc_uri, RDF.type, self.DOCEX.Document))
        graph.add((doc_uri, DCTERMS.identifier, Literal(extraction.document_id)))
        graph.add((doc_uri, DCTERMS.title, Literal(extraction.document_title)))
        graph.add((doc_uri, DCTERMS.created, Literal(extraction.extracted_at, datatype=XSD.dateTime)))
        
        # Add extraction metadata
        extraction_uri = URIRef(f"docex:extraction/{doc_hash}/{int(extraction.extracted_at.timestamp())}")
        graph.add((extraction_uri, RDF.type, self.DOCEX.ExtractionRecord))
        graph.add((extraction_uri, self.DOCEX.extractionConfidence, Literal(extraction.extraction_confidence, datatype=XSD.decimal)))
        graph.add((extraction_uri, self.DOCEX.extractionMethod, Literal(extraction.extraction_method)))
        graph.add((extraction_uri, self.DOCEX.totalStakeholders, Literal(len(extraction.stakeholders), datatype=XSD.integer)))
        graph.add((extraction_uri, self.PROV.wasGeneratedBy, doc_uri))
        
        if extraction.processing_time_seconds:
            graph.add((extraction_uri, self.DOCEX.processingTimeSeconds, 
                      Literal(extraction.processing_time_seconds, datatype=XSD.decimal)))
        
        return graph.serialize(format='turtle')
    
    def validate_conversion(self, original_data: Any, converted_data: Any) -> Dict[str, Any]:
        """Validate that conversion preserves semantic meaning"""
        
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "errors": []
        }
        
        try:
            # If converting from StakeholderExtraction, check stakeholder count
            if isinstance(original_data, StakeholderExtraction):
                original_count = len(original_data.stakeholders)
                
                # Count stakeholders in converted JSON-LD
                if isinstance(converted_data, dict) and "@graph" in converted_data:
                    converted_count = len([
                        item for item in converted_data["@graph"] 
                        if "@type" in item and any("Stakeholder" in t for t in 
                            (item["@type"] if isinstance(item["@type"], list) else [item["@type"]]))
                    ])
                    
                    if original_count != converted_count:
                        validation_results["errors"].append(
                            f"Stakeholder count mismatch: {original_count} → {converted_count}"
                        )
                        validation_results["is_valid"] = False
            
            # Additional semantic validation could be added here
            
        except Exception as e:
            validation_results["errors"].append(f"Validation failed: {str(e)}")
            validation_results["is_valid"] = False
        
        return validation_results
    
    def batch_convert_directory(
        self, 
        source_dir: str, 
        target_dir: str,
        source_format: str = "jsonld",
        target_format: str = "ttl"
    ) -> Dict[str, Any]:
        """Convert all files in directory from one format to another"""
        
        source_path = Path(source_dir)
        target_path = Path(target_dir)
        target_path.mkdir(exist_ok=True)
        
        results = {
            "converted": [],
            "failed": [],
            "total_files": 0
        }
        
        # Find source files
        if source_format == "jsonld":
            source_files = list(source_path.glob("*.json")) + list(source_path.glob("*.jsonld"))
        elif source_format == "ttl":
            source_files = list(source_path.glob("*.ttl"))
        else:
            raise ValueError(f"Unsupported source format: {source_format}")
        
        results["total_files"] = len(source_files)
        
        for source_file in source_files:
            try:
                # Determine target filename
                if target_format == "ttl":
                    target_file = target_path / f"{source_file.stem}.ttl"
                elif target_format == "jsonld":
                    target_file = target_path / f"{source_file.stem}.json"
                else:
                    raise ValueError(f"Unsupported target format: {target_format}")
                
                # Convert file
                with open(source_file, 'r', encoding='utf-8') as f:
                    if source_format == "jsonld":
                        source_data = json.load(f)
                        converted_content = self.jsonld_to_ttl(source_data, str(target_file))
                    elif source_format == "ttl":
                        source_content = f.read()
                        converted_data = self.ttl_to_jsonld(source_content, str(target_file))
                
                results["converted"].append({
                    "source": str(source_file),
                    "target": str(target_file),
                    "size": source_file.stat().st_size
                })
                
            except Exception as e:
                results["failed"].append({
                    "source": str(source_file),
                    "error": str(e)
                })
        
        return results


# Export main class
__all__ = ["FormatConverter"]
