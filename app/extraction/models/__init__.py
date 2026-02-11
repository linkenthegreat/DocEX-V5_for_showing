"""
Pydantic Models for Stakeholder Extraction

This module defines the data models used for structured extraction of stakeholder
information from documents, including reference anchoring and provenance tracking.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StakeholderType(str, Enum):
    """Types of stakeholders based on ontology"""
    INDIVIDUAL = "stakeholder:IndividualStakeholder"
    GROUP = "stakeholder:GroupStakeholder"
    ORGANIZATIONAL = "stakeholder:OrganizationalStakeholder"


class InfluenceLevel(str, Enum):
    """Stakeholder influence levels"""
    HIGH = "stakeholder:HighInfluence"
    MEDIUM = "stakeholder:MediumInfluence"
    LOW = "stakeholder:LowInfluence"


class InterestLevel(str, Enum):
    """Stakeholder interest levels"""
    HIGH = "stakeholder:HighInterest"
    MEDIUM = "stakeholder:MediumInterest"
    LOW = "stakeholder:LowInterest"


class DocumentReference(BaseModel):
    """Reference to specific location in source document"""
    document_id: str = Field(description="Unique document identifier")
    paragraph_number: Optional[int] = Field(default=None, description="Paragraph number (1-based)")
    sentence_number: Optional[int] = Field(default=None, description="Sentence number within paragraph")
    start_position: Optional[int] = Field(default=None, description="Character start position")
    end_position: Optional[int] = Field(default=None, description="Character end position")
    source_text: str = Field(description="Exact text that supports this extraction")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "891c6f7a3bae76a6f96a4ce18f9bef49",
                "paragraph_number": 2,
                "sentence_number": 1,
                "start_position": 150,
                "end_position": 280,
                "source_text": "Protecting the environment is everyone's responsibility including employees, contractors, and visitors."
            }
        }


class ExtractedStakeholder(BaseModel):
    """Individual stakeholder extracted from document"""
    name: str = Field(description="Stakeholder name or identifier")
    role: Optional[str] = Field(default=None, description="Role or position")
    stakeholder_type: StakeholderType = Field(description="Type of stakeholder")
    organization: Optional[str] = Field(default=None, description="Associated organization")
    
    # Relationships and attributes
    concerns: List[str] = Field(default=[], description="Areas of concern or interest")
    responsibilities: List[str] = Field(default=[], description="Responsibilities mentioned")
    collaborates_with: List[str] = Field(default=[], description="Other stakeholders they work with")
    
    # Influence and interest (if determinable)
    influence_level: Optional[InfluenceLevel] = Field(default=None, description="Assessed influence level")
    interest_level: Optional[InterestLevel] = Field(default=None, description="Assessed interest level")
    
    # Reference tracking
    name_reference: Optional[DocumentReference] = Field(default=None, description="Source of name extraction")
    role_reference: Optional[DocumentReference] = Field(default=None, description="Source of role extraction")
    concern_references: List[DocumentReference] = Field(default=[], description="Sources of concern mentions")
    
    # Quality metadata
    confidence_score: float = Field(
        ge=0.0, le=1.0, 
        description="AI confidence in extraction accuracy"
    )
    extraction_notes: str = Field(default="", description="Additional extraction context")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Stakeholder name cannot be empty')
        return v.strip()
    
    @validator('confidence_score')
    def confidence_reasonable(cls, v):
        if v < 0.3:
            raise ValueError('Confidence score too low - extraction may be unreliable')
        return v

    def to_jsonld(self) -> Dict[str, Any]:
        """Convert to JSON-LD format for storage and review"""
        base_id = self.name.lower().replace(' ', '_').replace('.', '_')
        
        jsonld = {
            "@id": f"stakeholder:{base_id}",
            "@type": self.stakeholder_type.value,
            "schema:name": self.name,
            "stakeholder:hasRole": self.role,
            "stakeholder:belongsToOrganization": self.organization,
            "stakeholder:hasConcern": self.concerns,
            "stakeholder:hasResponsibility": self.responsibilities,
            "stakeholder:collaboratesWith": self.collaborates_with,
            
            # Metadata
            "_extraction_metadata": {
                "confidence": self.confidence_score,
                "extracted_at": datetime.now().isoformat(),
                "extraction_notes": self.extraction_notes
            }
        }
        
        # Add influence/interest if available
        if self.influence_level:
            jsonld["stakeholder:hasInfluenceLevel"] = self.influence_level.value
        if self.interest_level:
            jsonld["stakeholder:hasInterestLevel"] = self.interest_level.value
            
        # Add provenance information
        if self.name_reference:
            jsonld["prov:wasDerivedFrom"] = {
                "@id": f"docex:reference/{self.name_reference.document_id}/p{self.name_reference.paragraph_number}s{self.name_reference.sentence_number}",
                "docex:sourceText": self.name_reference.source_text,
                "docex:startPosition": self.name_reference.start_position,
                "docex:endPosition": self.name_reference.end_position
            }
        
        return jsonld


class StakeholderExtraction(BaseModel):
    """Complete extraction result for a document"""
    document_id: str = Field(description="Source document identifier")
    document_title: str = Field(description="Document title or filename")
    stakeholders: List[ExtractedStakeholder] = Field(description="Extracted stakeholders")
    
    # Document-level metadata
    extraction_confidence: float = Field(
        ge=0.0, le=1.0,
        description="Overall confidence in document extraction"
    )
    extraction_method: str = Field(
        default="LLM-structured",
        description="Method used for extraction"
    )
    extracted_at: datetime = Field(default_factory=datetime.now)
    
    # Processing statistics
    total_paragraphs: Optional[int] = Field(default=None, description="Total paragraphs processed")
    total_sentences: Optional[int] = Field(default=None, description="Total sentences processed")
    processing_time_seconds: Optional[float] = Field(default=None, description="Processing duration")
    provider_used: Optional[str] = Field(default=None, description="LLM provider used for extraction")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "891c6f7a3bae76a6f96a4ce18f9bef49",
                "document_title": "Environmental Policy.pdf",
                "stakeholders": [
                    {
                        "name": "employees",
                        "role": "workers",
                        "stakeholder_type": "stakeholder:GroupStakeholder",
                        "concerns": ["environmental responsibility", "waste reduction"],
                        "confidence_score": 0.95
                    }
                ],
                "extraction_confidence": 0.92,
                "total_paragraphs": 5,
                "total_sentences": 25
            }
        }
    
    def to_jsonld(self) -> Dict[str, Any]:
        """Convert complete extraction to JSON-LD format"""
        return {
            "@context": {
                "stakeholder": "http://www.example.org/stakeholder-ontology#",
                "docex": "http://example.org/docex/",
                "prov": "http://www.w3.org/ns/prov#",
                "schema": "http://schema.org/",
                "dcterms": "http://purl.org/dc/terms/"
            },
            "@graph": [stakeholder.to_jsonld() for stakeholder in self.stakeholders],
            "docex:extractionMetadata": {
                "@type": "docex:ExtractionRecord",
                "dcterms:source": self.document_id,
                "dcterms:title": self.document_title,
                "docex:extractionConfidence": self.extraction_confidence,
                "docex:extractionMethod": self.extraction_method,
                "dcterms:created": self.extracted_at.isoformat(),
                "docex:totalStakeholders": len(self.stakeholders),
                "docex:totalParagraphs": self.total_paragraphs,
                "docex:totalSentences": self.total_sentences,
                "docex:processingTimeSeconds": self.processing_time_seconds
            }
        }
    
    def get_low_confidence_stakeholders(self, threshold: float = 0.7) -> List[ExtractedStakeholder]:
        """Get stakeholders below confidence threshold for review"""
        return [s for s in self.stakeholders if s.confidence_score < threshold]
    
    def get_embedding_texts(self) -> List[str]:
        """Generate texts optimized for embedding creation"""
        texts = []
        for stakeholder in self.stakeholders:
            embedding_text = f"Stakeholder: {stakeholder.name}"
            if stakeholder.role:
                embedding_text += f" | Role: {stakeholder.role}"
            if stakeholder.organization:
                embedding_text += f" | Organization: {stakeholder.organization}"
            if stakeholder.concerns:
                embedding_text += f" | Concerns: {', '.join(stakeholder.concerns)}"
            if stakeholder.name_reference:
                embedding_text += f" | Context: {stakeholder.name_reference.source_text}"
            texts.append(embedding_text)
        return texts


# Export main classes
__all__ = [
    "StakeholderType",
    "InfluenceLevel", 
    "InterestLevel",
    "DocumentReference",
    "ExtractedStakeholder",
    "StakeholderExtraction"
]
