"""
Migration utilities for converting TTL files to JSON-LD format
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from rdflib import Graph
from flask import current_app
from .rdf_utils import initialize_graph, ontology_manager

def migrate_ttl_to_jsonld(ttl_filename: str) -> bool:
    """Migrate a single TTL file to JSON-LD format"""
    
    try:
        triples_dir = Path(current_app.config['TRIPLES_DIR'])
        jsonld_dir = Path(current_app.config.get('JSONLD_DIR', current_app.config['DATABASE_DIR'] + '/jsonld'))
        
        ttl_path = triples_dir / ttl_filename
        jsonld_path = jsonld_dir / ttl_filename.replace('.ttl', '.json')
        
        if not ttl_path.exists():
            current_app.logger.error(f"TTL file not found: {ttl_path}")
            return False
        
        # Load TTL into graph
        g = initialize_graph()
        g.parse(str(ttl_path), format="turtle")
        
        # Get ontology context
        context = ontology_manager.get_context()
        
        # Convert to JSON-LD
        jsonld_str = g.serialize(format="json-ld", context=context)
        jsonld_doc = json.loads(jsonld_str)
        
        # Ensure output directory exists
        jsonld_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON-LD
        with open(jsonld_path, 'w', encoding='utf-8') as f:
            json.dump(jsonld_doc, f, ensure_ascii=False, indent=2)
        
        current_app.logger.info(f"Migrated {ttl_filename} to {jsonld_path}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error migrating {ttl_filename}: {str(e)}")
        return False

def migrate_all_ttl_files() -> Dict[str, int]:
    """Migrate all TTL files to JSON-LD format"""
    
    triples_dir = Path(current_app.config['TRIPLES_DIR'])
    
    if not triples_dir.exists():
        return {"total": 0, "success": 0, "failed": 0}
    
    ttl_files = list(triples_dir.glob("*.ttl"))
    stats = {"total": len(ttl_files), "success": 0, "failed": 0}
    
    for ttl_path in ttl_files:
        if migrate_ttl_to_jsonld(ttl_path.name):
            stats["success"] += 1
        else:
            stats["failed"] += 1
    
    current_app.logger.info(f"Migration complete: {stats}")
    return stats