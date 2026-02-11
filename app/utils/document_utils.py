"""
Document Processing Utilities

This module provides functions for extracting and processing structured content 
from various document formats (PDF, DOCX, TXT), including paragraph and
sentence extraction with proper hierarchical organization.

Functions:
    extract_structured_content: Extract paragraphs from document files
    segment_sentences: Split paragraphs into sentences using NLP
    extract_file_content: Read file content based on file type
    sanitize_id: Generate safe IDs for paragraphs and sentences
    get_document_structure: Create complete document structure with IDs

The extracted document structures serve as the foundation for RDF graph
creation in the DocEX system.
"""

import os
import re
import mimetypes
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import nltk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

from flask import current_app

def extract_structured_content(file_path):
    """Extract structured content (paragraphs) from documents"""
    # Use the file_utils.py version to extract content
    from .file_utils import extract_file_content as get_content
    
    content = get_content(file_path)
    if content and (content.startswith("[Error") or content.startswith("[")):
        return {"paragraphs": [content], "success": False}
    
    # Split content into paragraphs (non-empty lines)
    paragraphs = [p for p in content.split('\n\n') if p.strip()]
    current_app.logger.info(f"Extracted {len(paragraphs)} paragraphs from {file_path}")
    
    return {
        "paragraphs": paragraphs,
        "success": True
    }

def extract_file_content(file_path):
    """Extract text content from a file based on its type"""
    # Delegate to the existing file_utils function
    from .file_utils import extract_file_content
    return extract_file_content(file_path)

def sanitize_id(text):
    """Convert text to a safe ID format"""
    # Replace spaces and special chars with underscores
    return re.sub(r'[^a-zA-Z0-9]', '_', text)

def segment_sentences(text):
    """Split text into sentences using NLTK"""
    if NLTK_AVAILABLE:
        try:
            # Download necessary NLTK data (run once)
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')
            
            # Split text into sentences
            sentences = nltk.sent_tokenize(text)
            return sentences
        except Exception as e:
            current_app.logger.error(f"Error in sentence segmentation: {str(e)}")
    
    # Fall back to simple splitting if NLTK fails or unavailable
    return [s.strip() + '.' for s in text.split('.') if s.strip()]

def get_document_structure(file_path):
    """Get complete document structure with paragraphs and sentences using structured IDs"""
    structured_content = extract_structured_content(file_path)
    
    if not structured_content["success"]:
        return structured_content
    
    # Generate document ID from filename (sanitized)
    filename = os.path.basename(file_path)
    doc_id = sanitize_id(os.path.splitext(filename)[0])
    
    # Add sentence segmentation to each paragraph
    document_structure = {
        "doc_id": doc_id,
        "file_path": file_path,
        "paragraphs": []
    }
    
    for i, paragraph in enumerate(structured_content["paragraphs"]):
        para_id = f"{doc_id}_para_{i+1}"
        sentences = segment_sentences(paragraph)
        
        sentences_with_ids = []
        for j, sentence in enumerate(sentences):
            sent_id = f"{para_id}_sent_{j+1}"
            sentences_with_ids.append({
                "id": sent_id,
                "text": sentence
            })
        
        document_structure["paragraphs"].append({
            "id": para_id,
            "text": paragraph,
            "sentences": sentences_with_ids
        })
    
    return document_structure

# Add missing functions that test expects (using existing file_utils)
def extract_pdf_content(file_path: str) -> str:
    """Extract text content from PDF file - delegates to file_utils"""
    from .file_utils import extract_file_content
    return extract_file_content(file_path)

def get_file_metadata(file_path: str) -> Dict[str, Any]:
    """Get comprehensive metadata from a file - delegates to file_utils"""
    from .file_utils import get_file_metadata
    return get_file_metadata(file_path)

def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """Calculate hash of a file - delegates to file_utils"""
    from .file_utils import calculate_file_hash
    return calculate_file_hash(file_path)

def validate_file_access(file_path: str) -> Dict[str, Any]:
    """Validate that a file can be accessed and processed"""
    file_path = Path(file_path)
    
    result = {
        'valid': False,
        'exists': False,
        'readable': False,
        'processable': False,
        'file_type': None,
        'size': 0,
        'errors': []
    }
    
    # Check existence
    if not file_path.exists():
        result['errors'].append(f"File does not exist: {file_path}")
        return result
    
    result['exists'] = True
    
    # Check readability
    try:
        stat_info = file_path.stat()
        result['size'] = stat_info.st_size
        result['readable'] = True
    except Exception as e:
        result['errors'].append(f"Cannot access file: {str(e)}")
        return result
    
    # Check file type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    result['file_type'] = mime_type
    
    # Check if processable
    processable_types = {
        'application/pdf',
        'text/plain',
        'text/markdown',
        'text/html',
        'application/json',
        'text/csv'
    }
    
    processable_extensions = {'.pdf', '.txt', '.md', '.html', '.json', '.csv', '.py', '.js'}
    
    if mime_type in processable_types or file_path.suffix.lower() in processable_extensions:
        result['processable'] = True
    else:
        result['errors'].append(f"Unsupported file type: {mime_type or 'unknown'}")
    
    # Overall validation
    result['valid'] = result['exists'] and result['readable'] and result['processable']
    
    return result