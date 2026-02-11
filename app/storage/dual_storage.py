"""
Dual Storage Manager for JSON-LD and TTL formats

This module manages the dual storage architecture, providing a unified interface
for storing and retrieving stakeholder data in both JSON-LD and TTL formats.
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

from app.extraction.models import StakeholderExtraction
from app.extraction.adapters.format_converter import FormatConverter
from app.config import Config


class DualStorageManager:
    """
    Manages dual storage of extraction results in both JSON-LD and TTL formats
    with automatic synchronization and validation.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.converter = FormatConverter()
        
        # Storage paths - handle both DATABASE_PATH and DATABASE_DIR
        if hasattr(config, 'DATABASE_PATH'):
            database_path = Path(config.DATABASE_PATH)
        elif hasattr(config, 'DATABASE_DIR'):
            database_path = Path(config.DATABASE_DIR)
        else:
            raise ValueError("Config must have either DATABASE_PATH or DATABASE_DIR")
            
        self.ttl_storage_path = database_path / "triples"
        self.jsonld_storage_path = database_path / "jsonld"
        self.embeddings_storage_path = database_path / "embeddings"
        
        # Ensure directories exist
        self.ttl_storage_path.mkdir(parents=True, exist_ok=True)
        self.jsonld_storage_path.mkdir(parents=True, exist_ok=True)
        self.embeddings_storage_path.mkdir(parents=True, exist_ok=True)
    
    def store_extraction(
        self, 
        extraction: StakeholderExtraction,
        original_ttl_content: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Store extraction results in both formats
        Returns: Dictionary with file paths for both formats
        """
        
        # Generate consistent filenames
        doc_id_clean = self._sanitize_filename(extraction.document_id)
        base_filename = f"{doc_id_clean}_{extraction.extracted_at.strftime('%Y%m%d_%H%M%S')}"
        
        ttl_filepath = self.ttl_storage_path / f"{base_filename}.ttl"
        jsonld_filepath = self.jsonld_storage_path / f"{base_filename}.json"
        
        try:
            # Store JSON-LD format (primary for LLM processing)
            jsonld_data = self.converter.extraction_to_jsonld(extraction)
            with open(jsonld_filepath, 'w', encoding='utf-8') as f:
                json.dump(jsonld_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Store TTL format (for graph operations)
            ttl_content = self.converter.create_ttl_document(extraction, original_ttl_content)
            with open(ttl_filepath, 'w', encoding='utf-8') as f:
                f.write(ttl_content)
            
            # Validate storage consistency
            validation_result = self._validate_dual_storage(jsonld_filepath, ttl_filepath)
            if not validation_result["is_consistent"]:
                raise ValueError(f"Storage validation failed: {validation_result['issues']}")
            
            # Update storage index
            self._update_storage_index(extraction, str(jsonld_filepath), str(ttl_filepath))
            
            return {
                "jsonld_path": str(jsonld_filepath),
                "ttl_path": str(ttl_filepath),
                "document_id": extraction.document_id,
                "stored_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Cleanup on failure
            for filepath in [jsonld_filepath, ttl_filepath]:
                if filepath.exists():
                    filepath.unlink()
            raise RuntimeError(f"Failed to store extraction: {str(e)}")
    
    def retrieve_extraction(
        self, 
        document_id: str, 
        format_preference: str = "jsonld"
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Retrieve extraction by document ID
        Returns: (data, file_path) tuple, or (None, None) if not found
        """
        
        # Find files for this document
        jsonld_files = list(self.jsonld_storage_path.glob(f"{self._sanitize_filename(document_id)}_*.json"))
        ttl_files = list(self.ttl_storage_path.glob(f"{self._sanitize_filename(document_id)}_*.ttl"))
        
        if not jsonld_files and not ttl_files:
            return None, None
        
        try:
            if format_preference == "jsonld" and jsonld_files:
                # Return most recent JSON-LD file
                latest_file = max(jsonld_files, key=lambda f: f.stat().st_mtime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data, str(latest_file)
            
            elif format_preference == "ttl" and ttl_files:
                # Return most recent TTL file
                latest_file = max(ttl_files, key=lambda f: f.stat().st_mtime)
                with open(latest_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {"ttl_content": content}, str(latest_file)
            
            else:
                # Fallback to available format
                if jsonld_files:
                    latest_file = max(jsonld_files, key=lambda f: f.stat().st_mtime)
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return data, str(latest_file)
                elif ttl_files:
                    latest_file = max(ttl_files, key=lambda f: f.stat().st_mtime)
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    return {"ttl_content": content}, str(latest_file)
        
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve extraction for {document_id}: {str(e)}")
        
        return None, None
    
    def list_stored_documents(self) -> List[Dict[str, Any]]:
        """List all stored documents with metadata"""
        
        documents = []
        
        # Scan JSON-LD files for document inventory
        for jsonld_file in self.jsonld_storage_path.glob("*.json"):
            try:
                with open(jsonld_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract document metadata
                doc_metadata = data.get("docex:extractionMetadata", {})
                
                # Find corresponding TTL file
                ttl_file = self.ttl_storage_path / f"{jsonld_file.stem}.ttl"
                
                document_info = {
                    "document_id": doc_metadata.get("dcterms:source", jsonld_file.stem),
                    "title": doc_metadata.get("dcterms:title", "Unknown"),
                    "extracted_at": doc_metadata.get("dcterms:created"),
                    "total_stakeholders": doc_metadata.get("docex:totalStakeholders", 0),
                    "extraction_confidence": doc_metadata.get("docex:extractionConfidence"),
                    "jsonld_path": str(jsonld_file),
                    "ttl_path": str(ttl_file) if ttl_file.exists() else None,
                    "jsonld_size": jsonld_file.stat().st_size,
                    "ttl_size": ttl_file.stat().st_size if ttl_file.exists() else None
                }
                
                documents.append(document_info)
                
            except Exception as e:
                # Skip corrupted files but log the issue
                print(f"Warning: Could not read {jsonld_file}: {str(e)}")
                continue
        
        # Sort by extraction date (most recent first)
        documents.sort(key=lambda d: d.get("extracted_at", ""), reverse=True)
        
        return documents
    
    def synchronize_formats(self, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Synchronize JSON-LD and TTL formats for consistency
        If document_id is None, synchronizes all documents
        """
        
        results = {
            "synchronized": [],
            "failed": [],
            "total_processed": 0
        }
        
        if document_id:
            # Synchronize specific document
            documents = [doc for doc in self.list_stored_documents() 
                        if doc["document_id"] == document_id]
        else:
            # Synchronize all documents
            documents = self.list_stored_documents()
        
        results["total_processed"] = len(documents)
        
        for doc in documents:
            try:
                jsonld_path = doc["jsonld_path"]
                ttl_path = doc["ttl_path"]
                
                # Load JSON-LD data
                with open(jsonld_path, 'r', encoding='utf-8') as f:
                    jsonld_data = json.load(f)
                
                # Convert to TTL and update file
                if ttl_path:
                    ttl_content = self.converter.jsonld_to_ttl(jsonld_data, ttl_path)
                    
                    # Validate consistency
                    validation_result = self._validate_dual_storage(jsonld_path, ttl_path)
                    
                    results["synchronized"].append({
                        "document_id": doc["document_id"],
                        "jsonld_path": jsonld_path,
                        "ttl_path": ttl_path,
                        "validation": validation_result
                    })
                
            except Exception as e:
                results["failed"].append({
                    "document_id": doc["document_id"],
                    "error": str(e)
                })
        
        return results
    
    def delete_extraction(self, document_id: str) -> bool:
        """Delete extraction files for a document"""
        
        try:
            deleted_files = []
            
            # Find and delete JSON-LD files
            jsonld_files = list(self.jsonld_storage_path.glob(f"{self._sanitize_filename(document_id)}_*.json"))
            for file in jsonld_files:
                file.unlink()
                deleted_files.append(str(file))
            
            # Find and delete TTL files
            ttl_files = list(self.ttl_storage_path.glob(f"{self._sanitize_filename(document_id)}_*.ttl"))
            for file in ttl_files:
                file.unlink()
                deleted_files.append(str(file))
            
            # Remove from storage index
            self._remove_from_storage_index(document_id)
            
            return len(deleted_files) > 0
            
        except Exception as e:
            raise RuntimeError(f"Failed to delete extraction for {document_id}: {str(e)}")
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get storage statistics and health metrics"""
        
        stats = {
            "total_documents": 0,
            "total_jsonld_files": 0,
            "total_ttl_files": 0,
            "total_jsonld_size": 0,
            "total_ttl_size": 0,
            "orphaned_files": [],
            "consistency_issues": [],
            "last_updated": datetime.now().isoformat()
        }
        
        # Count JSON-LD files
        jsonld_files = list(self.jsonld_storage_path.glob("*.json"))
        stats["total_jsonld_files"] = len(jsonld_files)
        stats["total_jsonld_size"] = sum(f.stat().st_size for f in jsonld_files)
        
        # Count TTL files
        ttl_files = list(self.ttl_storage_path.glob("*.ttl"))
        stats["total_ttl_files"] = len(ttl_files)
        stats["total_ttl_size"] = sum(f.stat().st_size for f in ttl_files)
        
        # Check for orphaned files and consistency
        documents = self.list_stored_documents()
        stats["total_documents"] = len(documents)
        
        for doc in documents:
            # Check for orphaned TTL files
            if not doc["ttl_path"] or not Path(doc["ttl_path"]).exists():
                stats["orphaned_files"].append({
                    "type": "missing_ttl",
                    "document_id": doc["document_id"],
                    "jsonld_path": doc["jsonld_path"]
                })
            
            # Validate consistency where both files exist
            if doc["ttl_path"] and Path(doc["ttl_path"]).exists():
                try:
                    validation = self._validate_dual_storage(doc["jsonld_path"], doc["ttl_path"])
                    if not validation["is_consistent"]:
                        stats["consistency_issues"].append({
                            "document_id": doc["document_id"],
                            "issues": validation["issues"]
                        })
                except Exception as e:
                    stats["consistency_issues"].append({
                        "document_id": doc["document_id"],
                        "issues": [f"Validation failed: {str(e)}"]
                    })
        
        return stats
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem storage"""
        # Replace problematic characters
        sanitized = filename.replace(":", "_").replace("/", "_").replace("\\", "_")
        sanitized = sanitized.replace(" ", "_").replace("<", "_").replace(">", "_")
        sanitized = sanitized.replace("|", "_").replace("?", "_").replace("*", "_")
        return sanitized
    
    def _validate_dual_storage(self, jsonld_path: str, ttl_path: str) -> Dict[str, Any]:
        """Validate consistency between JSON-LD and TTL files"""
        
        validation_result = {
            "is_consistent": True,
            "issues": []
        }
        
        try:
            # Load both files
            with open(jsonld_path, 'r', encoding='utf-8') as f:
                jsonld_data = json.load(f)
            
            with open(ttl_path, 'r', encoding='utf-8') as f:
                ttl_content = f.read()
            
            # Basic consistency checks
            # 1. Check stakeholder count in JSON-LD
            jsonld_stakeholders = 0
            if "@graph" in jsonld_data:
                jsonld_stakeholders = len([
                    item for item in jsonld_data["@graph"]
                    if "@type" in item and any("Stakeholder" in str(t) for t in 
                        (item["@type"] if isinstance(item["@type"], list) else [item["@type"]]))
                ])
            
            # 2. Check stakeholder count in TTL (simple text-based check)
            ttl_stakeholder_lines = [line for line in ttl_content.split('\n') 
                                   if 'Stakeholder' in line and 'a ' in line]
            ttl_stakeholders = len(ttl_stakeholder_lines)
            
            # Allow for some variance due to metadata differences
            if abs(jsonld_stakeholders - ttl_stakeholders) > 1:
                validation_result["issues"].append(
                    f"Stakeholder count mismatch: JSON-LD={jsonld_stakeholders}, TTL={ttl_stakeholders}"
                )
                validation_result["is_consistent"] = False
            
            # 3. Check file timestamps (TTL should not be much older than JSON-LD)
            jsonld_mtime = Path(jsonld_path).stat().st_mtime
            ttl_mtime = Path(ttl_path).stat().st_mtime
            
            if abs(jsonld_mtime - ttl_mtime) > 300:  # 5 minutes tolerance
                validation_result["issues"].append("File timestamps suggest inconsistent updates")
                validation_result["is_consistent"] = False
        
        except Exception as e:
            validation_result["issues"].append(f"Validation error: {str(e)}")
            validation_result["is_consistent"] = False
        
        return validation_result
    
    def _update_storage_index(self, extraction: StakeholderExtraction, jsonld_path: str, ttl_path: str):
        """Update storage index with new extraction"""
        
        # Use the same database path logic
        if hasattr(self.config, 'DATABASE_PATH'):
            index_file = Path(self.config.DATABASE_PATH) / "storage_index.json"
        elif hasattr(self.config, 'DATABASE_DIR'):
            index_file = Path(self.config.DATABASE_DIR) / "storage_index.json"
        else:
            raise ValueError("Config must have either DATABASE_PATH or DATABASE_DIR")
        
        try:
            # Load existing index
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            else:
                index = {"documents": {}, "last_updated": None}
            
            # Update index entry
            index["documents"][extraction.document_id] = {
                "title": extraction.document_title,
                "extracted_at": extraction.extracted_at.isoformat(),
                "jsonld_path": jsonld_path,
                "ttl_path": ttl_path,
                "total_stakeholders": len(extraction.stakeholders),
                "extraction_confidence": extraction.extraction_confidence
            }
            index["last_updated"] = datetime.now().isoformat()
            
            # Save updated index
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, default=str)
        
        except Exception as e:
            # Index update failure shouldn't break storage
            print(f"Warning: Failed to update storage index: {str(e)}")
    
    def _remove_from_storage_index(self, document_id: str):
        """Remove document from storage index"""
        
        # Use the same database path logic
        if hasattr(self.config, 'DATABASE_PATH'):
            index_file = Path(self.config.DATABASE_PATH) / "storage_index.json"
        elif hasattr(self.config, 'DATABASE_DIR'):
            index_file = Path(self.config.DATABASE_DIR) / "storage_index.json"
        else:
            raise ValueError("Config must have either DATABASE_PATH or DATABASE_DIR")
        
        try:
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                
                if document_id in index.get("documents", {}):
                    del index["documents"][document_id]
                    index["last_updated"] = datetime.now().isoformat()
                    
                    with open(index_file, 'w', encoding='utf-8') as f:
                        json.dump(index, f, indent=2, default=str)
        
        except Exception as e:
            print(f"Warning: Failed to update storage index during deletion: {str(e)}")


# Export main class
__all__ = ["DualStorageManager"]
