"""
Document Embedding Pipeline for DocEX
Handles embedding generation from JSON-LD documents
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class DocumentEmbedder:
    """Handles embedding generation from JSON-LD documents"""
    
    def __init__(self, vector_manager):
        self.vector_manager = vector_manager
    
    def embed_existing_jsonld_documents(self, jsonld_dir: str = None) -> Dict[str, Any]:
        """Process all existing JSON-LD documents into vector embeddings"""
        if not jsonld_dir:
            jsonld_dir = 'database/jsonld'  # Fallback path
        
        results = {
            'processed': 0,
            'errors': 0,
            'skipped': 0,
            'details': []
        }
        
        try:
            jsonld_files = self.discover_jsonld_documents(jsonld_dir)
            logger.info(f"Found {len(jsonld_files)} JSON-LD documents to process")
            
            for jsonld_file in jsonld_files:
                try:
                    doc = self.load_jsonld_document(jsonld_file)
                    if not doc:
                        results['skipped'] += 1
                        continue
                    
                    doc_id = doc.get('@id', os.path.basename(jsonld_file))
                    
                    # Store document-level embedding
                    success = self.vector_manager.store_document_embedding(doc_id, doc)
                    
                    if success:
                        results['processed'] += 1
                        results['details'].append({
                            'file': jsonld_file,
                            'doc_id': doc_id,
                            'status': 'success'
                        })
                    else:
                        results['errors'] += 1
                        results['details'].append({
                            'file': jsonld_file,
                            'doc_id': doc_id,
                            'status': 'error'
                        })
                    
                except Exception as e:
                    logger.error(f"Error processing {jsonld_file}: {e}")
                    results['errors'] += 1
                    results['details'].append({
                        'file': jsonld_file,
                        'status': 'error',
                        'error': str(e)
                    })
            
            logger.info(f"Embedding complete: {results['processed']} processed, {results['errors']} errors, {results['skipped']} skipped")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch embedding process: {e}")
            results['errors'] += 1
            return results
    
    def discover_jsonld_documents(self, jsonld_dir: str) -> List[str]:
        """Discover all JSON-LD files in directory"""
        jsonld_files = []
        
        if not os.path.exists(jsonld_dir):
            logger.warning(f"JSON-LD directory not found: {jsonld_dir}")
            return jsonld_files
        
        for file in os.listdir(jsonld_dir):
            if file.endswith('.json'):
                jsonld_files.append(os.path.join(jsonld_dir, file))
        
        return jsonld_files
    
    def load_jsonld_document(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load and validate JSON-LD document"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc = json.load(f)
            
            # Basic validation
            if '@context' in doc and '@id' in doc:
                return doc
            else:
                logger.warning(f"Invalid JSON-LD format in {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading JSON-LD document {file_path}: {e}")
            return None