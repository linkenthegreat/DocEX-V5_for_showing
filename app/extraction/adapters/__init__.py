"""
Extraction Adapters Package

This package provides adapters for different extraction methods and format conversions:
- LLM Adapter: Structured extraction using OpenAI/Ollama with Pydantic validation
- Format Converter: Bidirectional JSON-LD ↔ TTL conversion utilities
"""

from .llm_adapter import StructuredExtractionAdapter
from .format_converter import FormatConverter

__all__ = ["StructuredExtractionAdapter", "FormatConverter"]
