"""
Extraction Package

This package handles structured extraction of stakeholder information from documents
using various LLM providers with JSON-LD output format and reference anchoring.

Modules:
- models: Pydantic models for stakeholder extraction
- adapters: LLM provider-specific adapters (OpenAI, Ollama, etc.)
"""

__version__ = "1.0.0"

# Import only what we've implemented in Phase 1
from .models import (
    StakeholderExtraction, 
    ExtractedStakeholder, 
    DocumentReference,
    StakeholderType,
    InfluenceLevel,
    InterestLevel
)

__all__ = [
    "StakeholderExtraction",
    "ExtractedStakeholder", 
    "DocumentReference",
    "StakeholderType",
    "InfluenceLevel",
    "InterestLevel"
]
