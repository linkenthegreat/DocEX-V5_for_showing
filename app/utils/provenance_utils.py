"""
Provenance and URI utilities for DocEX
Handles URI generation and review action tracking
"""

import re
from datetime import datetime
from urllib.parse import quote
import uuid


def generate_document_uri(filename):
    """Generate consistent URI for documents"""
    # Clean filename for URI use
    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
    safe_name = re.sub(r'_+', '_', safe_name)  # Remove multiple underscores
    safe_name = safe_name.strip('_')  # Remove leading/trailing underscores
    
    return f"https://docex.org/vocab/document/{safe_name}"


def generate_analysis_uri(document_filename):
    """Generate URI for extraction analysis"""
    doc_uri = generate_document_uri(document_filename)
    return f"{doc_uri}/analysis"


def generate_review_action_id():
    """Generate unique ID for review actions"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"review_{timestamp}_{unique_id}"


def create_review_action(reviewer_id, action_type, stakeholder_data, original_data=None, rationale=None):
    """Create a review action object"""
    review_action = {
        "@type": "ReviewAction",
        "@id": generate_review_action_id(),
        "reviewer": reviewer_id or "user_unknown",
        "timestamp": datetime.now().isoformat(),
        "action": action_type,
        "rationale": rationale or "No reason provided"
    }
    
    # Add specific change details based on action type
    if action_type == "stakeholder_modified" and original_data:
        review_action["changes"] = []
        
        # Compare fields and record changes
        for field in ['name', 'stakeholderType', 'role', 'organization', 'contact']:
            old_val = original_data.get(field, '')
            new_val = stakeholder_data.get(field, '')
            
            if old_val != new_val:
                review_action["changes"].append({
                    "field": field,
                    "oldValue": old_val,
                    "newValue": new_val
                })
    
    elif action_type in ["stakeholder_approved", "stakeholder_rejected"]:
        review_action["stakeholderName"] = stakeholder_data.get("name", "Unknown")
        review_action["stakeholderType"] = stakeholder_data.get("stakeholderType", "UNKNOWN")
    
    return review_action


def add_provenance_to_extraction(extraction_data, review_actions):
    """Add provenance tracking to extraction JSON-LD"""
    if "reviewHistory" not in extraction_data:
        extraction_data["reviewHistory"] = []
    
    # Add new review actions
    if isinstance(review_actions, list):
        extraction_data["reviewHistory"].extend(review_actions)
    else:
        extraction_data["reviewHistory"].append(review_actions)
    
    # Update extraction metadata
    if "extractionMetadata" not in extraction_data:
        extraction_data["extractionMetadata"] = {}
    
    extraction_data["extractionMetadata"]["lastReviewed"] = datetime.now().isoformat()
    extraction_data["extractionMetadata"]["totalReviewActions"] = len(extraction_data["reviewHistory"])
    
    return extraction_data


def link_extraction_to_document(extraction_data, document_filename):
    """Add URI links between extraction and document"""
    doc_uri = generate_document_uri(document_filename)
    analysis_uri = generate_analysis_uri(document_filename)
    
    # Ensure proper JSON-LD structure
    if "@context" not in extraction_data:
        extraction_data["@context"] = {
            "@vocab": "https://docex.org/vocab/",
            "name": "http://schema.org/name",
            "email": "http://schema.org/email",
            "Stakeholder": "http://schema.org/Person",
            "Organization": "http://schema.org/Organization",
            "ReviewAction": "https://docex.org/vocab/ReviewAction"
        }
    
    # Add linking URIs
    extraction_data["@id"] = analysis_uri
    extraction_data["@type"] = "StakeholderExtraction"
    extraction_data["analyzedDocument"] = doc_uri
    
    return extraction_data


def create_metadata_link(metadata_data, document_filename, analysis_status="pending"):
    """Add analysis link to document metadata"""
    doc_uri = generate_document_uri(document_filename)
    analysis_uri = generate_analysis_uri(document_filename)
    
    # Ensure proper JSON-LD structure
    if "@context" not in metadata_data:
        metadata_data["@context"] = {
            "@vocab": "https://docex.org/vocab/",
            "name": "http://schema.org/name",
            "Document": "http://schema.org/CreativeWork"
        }
    
    # Add document URI and analysis link
    metadata_data["@id"] = doc_uri
    metadata_data["@type"] = "Document"
    
    if analysis_status == "completed":
        metadata_data["hasAnalysis"] = analysis_uri
        metadata_data["analysisStatus"] = "completed"
    else:
        metadata_data["analysisStatus"] = analysis_status
    
    return metadata_data


def validate_uri_linking(extraction_data, metadata_data):
    """Validate that extraction and metadata are properly linked"""
    try:
        extraction_uri = extraction_data.get("@id", "")
        document_uri = extraction_data.get("analyzedDocument", "")
        metadata_uri = metadata_data.get("@id", "")
        metadata_analysis = metadata_data.get("hasAnalysis", "")
        
        # Check basic structure
        if not extraction_uri or not document_uri or not metadata_uri:
            return False, "Missing required URI fields"
        
        # Check linking consistency
        if document_uri != metadata_uri:
            return False, f"Document URI mismatch: {document_uri} != {metadata_uri}"
        
        if metadata_analysis and metadata_analysis != extraction_uri:
            return False, f"Analysis URI mismatch: {metadata_analysis} != {extraction_uri}"
        
        return True, "URI linking validated successfully"
        
    except Exception as e:
        return False, f"URI validation error: {str(e)}"


# Export functions for global use
__all__ = [
    'generate_document_uri',
    'generate_analysis_uri', 
    'generate_review_action_id',
    'create_review_action',
    'add_provenance_to_extraction',
    'link_extraction_to_document',
    'create_metadata_link',
    'validate_uri_linking'
]