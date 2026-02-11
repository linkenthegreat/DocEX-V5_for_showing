"""
LLM Adapter for Structured Stakeholder Extraction

This module implements structured extraction using LLM providers with Pydantic
validation, supporting both OpenAI structured output and instructor for Ollama.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import re

from pydantic import ValidationError
import openai
from openai import OpenAI

from app.extraction.models import (
    StakeholderExtraction, 
    ExtractedStakeholder, 
    DocumentReference,
    StakeholderType,
    InfluenceLevel,
    InterestLevel
)
from app.llm.llm_client import LLMClient
from app.llm.github_models_processor import GitHubModelsProcessor
from app.config import Config
from app.llm.llm_providers.provider_factory import LLMProviderFactory


class StructuredExtractionAdapter:
    """
    Adapter for converting unstructured document text to structured stakeholder data
    using LLM providers with structured output capabilities.
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize logger
        import logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM client with specific parameters, not the whole config
        if hasattr(config, 'OLLAMA_BASE_URL'):
            base_url = config.OLLAMA_BASE_URL
        else:
            base_url = "http://localhost:11434"
            
        if hasattr(config, 'OLLAMA_MODEL'):
            model = config.OLLAMA_MODEL
        else:
            model = "llama3.1:8b-instruct-q8_0"
            
        self.llm_client = LLMClient(model=model, base_url=base_url)
        self.openai_client = None
        self.github_processor = None  # Use GitHubModelsProcessor instead of provider factory
        
        # Initialize OpenAI client if using structured output
        if hasattr(config, 'OPENAI_API_KEY') and config.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
        
        # Initialize GitHub Models processor
        try:
            from app.llm.github_models_processor import GitHubModelsProcessor
            self.github_processor = GitHubModelsProcessor()  # Uses correct constructor parameters
            self.logger.info(f"✅ GitHub Models processor initialized: {self.github_processor.get_available_models()}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize GitHub Models processor: {e}")
            self.github_processor = None
    
    def _create_extraction_prompt(self, document_text: str, document_title: str) -> str:
        """Create comprehensive prompt for stakeholder extraction"""
        
        return f"""You are an expert in stakeholder analysis. Extract all stakeholders mentioned in the following document, including their roles, relationships, and any mentioned concerns or responsibilities.

DOCUMENT TITLE: {document_title}

DOCUMENT TEXT:
{document_text}

EXTRACTION GUIDELINES:
1. Identify ALL stakeholders: individuals, groups, organizations
2. For each stakeholder, extract:
   - Name/identifier (required)
   - Role or position (if mentioned)
   - Type: Individual, Group, or Organizational stakeholder
   - Associated organization (if applicable)
   - Areas of concern or interest
   - Responsibilities mentioned
   - Other stakeholders they collaborate with
   - Influence level (if determinable): High, Medium, Low
   - Interest level (if determinable): High, Medium, Low

3. Provide EXACT text references for each extraction:
   - Include the exact sentence or phrase that mentions the stakeholder
   - Estimate paragraph and sentence numbers (1-based indexing)
   - Provide character positions if possible

4. Rate your confidence (0.0-1.0) for each stakeholder extraction

IMPORTANT: 
- Extract stakeholders even if only mentioned briefly
- Include collective stakeholders like "employees", "customers", "community"
- Don't make assumptions beyond what's stated in the document
- Provide conservative confidence scores for uncertain extractions

Focus on accuracy and completeness. If uncertain about a stakeholder's type or attributes, indicate lower confidence but still include the extraction."""

    def _segment_document(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Segment document into paragraphs and sentences with position tracking
        Returns: List of (paragraph_num, sentence_num, sentence_text)
        """
        paragraphs = text.split('\n\n')
        segments = []
        
        for para_idx, paragraph in enumerate(paragraphs, 1):
            if not paragraph.strip():
                continue
                
            # Simple sentence splitting (could be enhanced with spaCy/NLTK)
            sentences = re.split(r'[.!?]+\s*', paragraph.strip())
            
            for sent_idx, sentence in enumerate(sentences, 1):
                if sentence.strip():
                    segments.append((para_idx, sent_idx, sentence.strip()))
        
        return segments

    def _find_text_position(self, document_text: str, search_text: str) -> Tuple[Optional[int], Optional[int]]:
        """Find start and end positions of text in document"""
        start_pos = document_text.lower().find(search_text.lower())
        if start_pos == -1:
            return None, None
        return start_pos, start_pos + len(search_text)

    async def extract_stakeholders_openai(
        self, 
        document_text: str, 
        document_id: str,
        document_title: str
    ) -> StakeholderExtraction:
        """Extract stakeholders using OpenAI structured output"""
        
        if not self.openai_client:
            raise ValueError("OpenAI client not configured")
        
        prompt = self._create_extraction_prompt(document_text, document_title)
        
        try:
            # Use OpenAI's structured output feature
            response = self.openai_client.beta.chat.completions.parse(
                model="gpt-4o",  # or gpt-4o-mini for faster/cheaper extraction
                messages=[
                    {"role": "system", "content": "You are an expert stakeholder analyst. Extract stakeholders from documents with high precision."},
                    {"role": "user", "content": prompt}
                ],
                response_format=StakeholderExtraction,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            extraction = response.choices[0].message.parsed
            
            # Enrich with document metadata
            extraction.document_id = document_id
            extraction.document_title = document_title
            extraction.extraction_method = "OpenAI-structured"
            
            # Add reference positions where possible
            segments = self._segment_document(document_text)
            extraction = self._enrich_with_references(extraction, document_text, segments)
            
            return extraction
            
        except Exception as e:
            raise RuntimeError(f"OpenAI structured extraction failed: {str(e)}")

    async def extract_stakeholders_ollama(
        self,
        document_text: str,
        document_id: str, 
        document_title: str
    ) -> StakeholderExtraction:
        """Extract stakeholders using Ollama with instructor for structured output"""
        
        try:
            # For Ollama, we'll use a more structured prompt approach
            # since instructor integration might need additional setup
            
            prompt = self._create_extraction_prompt(document_text, document_title)
            
            # Add JSON schema guidance to prompt
            schema_prompt = f"""
{prompt}

RESPONSE FORMAT:
Respond with a valid JSON object matching this exact structure:
{{
  "document_id": "{document_id}",
  "document_title": "{document_title}",
  "stakeholders": [
    {{
      "name": "stakeholder name",
      "role": "role or null",
      "stakeholder_type": "stakeholder:IndividualStakeholder|stakeholder:GroupStakeholder|stakeholder:OrganizationalStakeholder",
      "organization": "organization or null",
      "concerns": ["concern1", "concern2"],
      "responsibilities": ["responsibility1"],
      "collaborates_with": ["other stakeholder names"],
      "influence_level": "stakeholder:HighInfluence|stakeholder:MediumInfluence|stakeholder:LowInfluence or null",
      "interest_level": "stakeholder:HighInterest|stakeholder:MediumInterest|stakeholder:LowInterest or null",
      "name_reference": {{
        "document_id": "{document_id}",
        "paragraph_number": 1,
        "sentence_number": 1,
        "source_text": "exact text mentioning stakeholder"
      }},
      "confidence_score": 0.95,
      "extraction_notes": "additional context"
    }}
  ],
  "extraction_confidence": 0.9,
  "extraction_method": "Ollama-structured"
}}

IMPORTANT: Return ONLY the JSON object, no additional text."""
            
            # Get response from Ollama
            result = self.llm_client.analyze_text(schema_prompt)
            
            # Check if there was an error
            if "error" in result:
                raise RuntimeError(f"LLM request failed: {result['error']}")
            
            # If the result is already parsed JSON, use it directly
            if isinstance(result, dict) and "error" not in result:
                raw_data = result
            else:
                # Otherwise extract JSON from response text
                response_text = str(result)
                json_text = self._extract_json_from_response(response_text)
                raw_data = json.loads(json_text)
            
            # Clean the data before validation
            cleaned_data = self._clean_extraction_data(raw_data)
            
            # Validate and create Pydantic model
            extraction = StakeholderExtraction.model_validate(cleaned_data)
            
            # Add metadata
            extraction.document_id = document_id
            extraction.document_title = document_title
            extraction.extraction_method = "Ollama-structured"
            extraction.extracted_at = datetime.now()
            
            return extraction
            
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"Failed to parse Ollama response as valid extraction: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Ollama extraction failed: {str(e)}")

    async def extract_stakeholders_github(
        self, 
        document_text: str, 
        document_id: str, 
        document_title: str
    ) -> StakeholderExtraction:
        """
        Extract stakeholders using GitHub Models processor - STANDARDIZED VERSION
        """
        if not self.github_processor:
            raise RuntimeError("GitHub Models processor not initialized")
        
        try:
            self.logger.info(f"Starting GitHub extraction for document: {document_id}")
            
            # Create system and user messages
            system_message = """You are an expert at analyzing documents and extracting stakeholder information. 
            Return your response as valid JSON with the following structure:
            {
                "stakeholders": [
                    {
                        "name": "stakeholder name",
                        "role": "their role or null",
                        "stakeholder_type": "INDIVIDUAL|GROUP|ORGANIZATIONAL",
                        "organization": "their organization or null",
                        "concerns": ["list", "of", "concerns"],
                        "responsibilities": ["list", "of", "responsibilities"],
                        "collaborates_with": ["other", "stakeholders"],
                        "influence_level": "HIGH|MEDIUM|LOW",
                        "interest_level": "HIGH|MEDIUM|LOW",
                        "confidence_score": 0.85,
                        "extraction_notes": "any relevant notes"
                    }
                ],
                "extraction_confidence": 0.9
            }"""
            
            # Create extraction prompt
            extraction_prompt = self._create_extraction_prompt(document_text, document_title)
            
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": extraction_prompt}
            ]
            
            # Use your GitHubModelsProcessor with DeepSeek model
            model = "deepseek/DeepSeek-V3-0324"  # Your configured model
            
            # Get structured JSON response
            parsed_response = self.github_processor.extract_structured_json(
                messages=messages,
                model=model
            )
            
            self.logger.info(f"GitHub extraction completed, response: {type(parsed_response)}")
            
            # Handle error responses
            if 'error' in parsed_response:
                raise Exception(f"GitHub API error: {parsed_response['error']}")
            
            # Validate that we have stakeholders
            if 'stakeholders' not in parsed_response:
                self.logger.warning(f"No stakeholders found in GitHub response for {document_id}")
                parsed_response = {"stakeholders": [], "extraction_confidence": 0.5}
            
            # Clean and validate stakeholder data before creating Pydantic models
            cleaned_data = self._clean_github_response(parsed_response, document_id, document_title)
            
            # Create StakeholderExtraction model
            result = StakeholderExtraction(**cleaned_data)
            
            self.logger.info(f"GitHub extraction successful: {len(result.stakeholders)} stakeholders found")
            return result
            
        except Exception as e:
            self.logger.error(f"GitHub extraction failed for {document_id}: {str(e)}")
            raise Exception(f"GitHub Models extraction failed: {str(e)}")

    def _extract_json_from_response(self, response_text: str) -> str:
        """Extract JSON object from LLM response text"""
        # Look for JSON object boundaries
        start_markers = ['{', '```json\n{', '```\n{']
        end_markers = ['}', '}\n```', '}\n```\n']
        
        for start_marker in start_markers:
            start_idx = response_text.find(start_marker)
            if start_idx != -1:
                # Find matching end marker
                for end_marker in end_markers:
                    end_idx = response_text.rfind(end_marker)
                    if end_idx > start_idx:
                        json_text = response_text[start_idx:end_idx + 1]
                        # Clean up any markdown formatting
                        json_text = json_text.replace('```json', '').replace('```', '').strip()
                        return json_text
        
        # Fallback: return entire response if no markers found
        return response_text.strip()

    def _create_github_extraction_prompt(self, document_text: str, document_title: str) -> str:
        """Create extraction prompt optimized for GitHub Models"""
        
        return f"""Extract all stakeholders from the following document and return a valid JSON object.

Document Title: {document_title}

Document Content:
{document_text}

Return a JSON object with this exact structure:
{{
    "document_id": "{document_title}",
    "document_title": "{document_title}",
    "stakeholders": [
        {{
            "name": "stakeholder name",
            "stakeholder_type": "stakeholder:GroupStakeholder|stakeholder:IndividualStakeholder|stakeholder:OrganizationalStakeholder",
            "role": "role description",
            "organization": "organization name if applicable",
            "concerns": ["concern1", "concern2"],
            "influence_level": "stakeholder:HighInfluence|stakeholder:MediumInfluence|stakeholder:LowInfluence",
            "interest_level": "stakeholder:HighInterest|stakeholder:MediumInterest|stakeholder:LowInterest",
            "confidence_score": 0.85,
            "name_reference": {{
                "document_id": "{document_title}",
                "source_text": "exact text from document",
                "start_position": 0,
                "end_position": 0
            }}
        }}
    ],
    "extraction_confidence": 0.85
}}

IMPORTANT: 
1. Return ONLY valid JSON, no other text
2. Use exact enum values as shown above
3. Set confidence_score between 0.0 and 1.0
4. Include source_text from the document for each stakeholder
5. Identify ALL stakeholders mentioned in the document"""

    def _enrich_with_references(
        self,
        extraction: StakeholderExtraction,
        document_text: str,
        segments: List[Tuple[int, int, str]]
    ) -> StakeholderExtraction:
        """Enhance extraction with better document references"""
        
        for stakeholder in extraction.stakeholders:
            if not stakeholder.name_reference:
                # Try to find reference for stakeholder name
                best_match = None
                best_score = 0
                
                for para_num, sent_num, sentence in segments:
                    # Simple fuzzy matching for stakeholder name in sentence
                    sentence_lower = sentence.lower()
                    name_lower = stakeholder.name.lower()
                    
                    if name_lower in sentence_lower:
                        # Calculate match quality
                        score = len(name_lower) / len(sentence_lower)
                        if score > best_score:
                            best_score = score
                            start_pos, end_pos = self._find_text_position(document_text, sentence)
                            
                            best_match = DocumentReference(
                                document_id=extraction.document_id,
                                paragraph_number=para_num,
                                sentence_number=sent_num,
                                start_position=start_pos,
                                end_position=end_pos,
                                source_text=sentence
                            )
                
                if best_match:
                    stakeholder.name_reference = best_match
        
        return extraction

    async def extract_stakeholders(
        self,
        document_text: str,
        document_id: str,
        document_title: str,
        prefer_openai: bool = True,
        provider: str = "auto"
    ) -> StakeholderExtraction:
        """
        Main extraction method with multi-provider fallback support
        Priority: OpenAI → GitHub Models → Ollama
        """
        start_time = datetime.now()
        last_error = None
        
        # Define fallback order based on preferences
        if provider == "github":
            providers = ["github"]
        elif provider == "ollama":
            providers = ["ollama"]
        elif provider == "openai":
            providers = ["openai"]
        else:  # auto fallback
            if prefer_openai and self.openai_client:
                providers = ["openai", "github", "ollama"]
            else:
                providers = ["github", "openai", "ollama"]
        
        for current_provider in providers:
            try:
                if current_provider == "openai" and self.openai_client:
                    self.logger.info(f"Attempting OpenAI extraction for {document_id}")
                    extraction = await self.extract_stakeholders_openai(
                        document_text, document_id, document_title
                    )
                elif current_provider == "github" and self.github_processor:  # Changed from self.github_provider
                    self.logger.info(f"Attempting GitHub Models extraction for {document_id}")
                    extraction = await self.extract_stakeholders_github(
                        document_text, document_id, document_title
                    )
                elif current_provider == "ollama":
                    self.logger.info(f"Attempting Ollama extraction for {document_id}")
                    extraction = await self.extract_stakeholders_ollama(
                        document_text, document_id, document_title
                    )
                else:
                    continue  # Skip unavailable providers
                
                # Add processing time and statistics
                processing_time = (datetime.now() - start_time).total_seconds()
                extraction.processing_time_seconds = processing_time
                extraction.provider_used = current_provider
                
                # Add document statistics
                segments = self._segment_document(document_text)
                extraction.total_sentences = len(segments)
                extraction.total_paragraphs = len(set(seg[0] for seg in segments))
                
                self.logger.info(f"Successfully extracted stakeholders using {current_provider} for {document_id}")
                return extraction
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"{current_provider} extraction failed for {document_id}: {str(e)}")
                continue
        
        # All providers failed
        raise RuntimeError(f"All providers failed for document {document_id}. Last error: {str(last_error)}")
    
    def _clean_extraction_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize extraction data before Pydantic validation"""
        cleaned = raw_data.copy()
        
        # Clean stakeholders array if present
        if "stakeholders" in cleaned and isinstance(cleaned["stakeholders"], list):
            for stakeholder in cleaned["stakeholders"]:
                if isinstance(stakeholder, dict):
                    # Clean stakeholder_type enum values
                    if "stakeholder_type" in stakeholder:
                        stype = stakeholder["stakeholder_type"]
                        if not str(stype).startswith("stakeholder:"):
                            # Map common values to proper enum format
                            if stype == "GroupStakeholder":
                                stakeholder["stakeholder_type"] = "stakeholder:GroupStakeholder"
                            elif stype == "IndividualStakeholder":
                                stakeholder["stakeholder_type"] = "stakeholder:IndividualStakeholder"
                            elif stype == "OrganizationalStakeholder":
                                stakeholder["stakeholder_type"] = "stakeholder:OrganizationalStakeholder"
                            else:
                                # Default to GroupStakeholder
                                stakeholder["stakeholder_type"] = "stakeholder:GroupStakeholder"
                    
                    # Clean influence_level enum values
                    if "influence_level" in stakeholder:
                        if stakeholder["influence_level"] == "stakeholder:null" or stakeholder["influence_level"] is None:
                            stakeholder["influence_level"] = "stakeholder:MediumInfluence"  # Default value
                        elif not stakeholder["influence_level"].startswith("stakeholder:"):
                            # Try to map common values
                            level = str(stakeholder["influence_level"]).lower()
                            if "high" in level:
                                stakeholder["influence_level"] = "stakeholder:HighInfluence"
                            elif "low" in level:
                                stakeholder["influence_level"] = "stakeholder:LowInfluence"
                            else:
                                stakeholder["influence_level"] = "stakeholder:MediumInfluence"
                    
                    # Clean interest_level enum values
                    if "interest_level" in stakeholder:
                        if stakeholder["interest_level"] == "stakeholder:null" or stakeholder["interest_level"] is None:
                            stakeholder["interest_level"] = "stakeholder:MediumInterest"  # Default value
                        elif not stakeholder["interest_level"].startswith("stakeholder:"):
                            # Try to map common values
                            level = str(stakeholder["interest_level"]).lower()
                            if "high" in level:
                                stakeholder["interest_level"] = "stakeholder:HighInterest"
                            elif "low" in level:
                                stakeholder["interest_level"] = "stakeholder:LowInterest"
                            else:
                                stakeholder["interest_level"] = "stakeholder:MediumInterest"
                    
                    # Clean name_reference if present
                    if "name_reference" in stakeholder and isinstance(stakeholder["name_reference"], dict):
                        name_ref = stakeholder["name_reference"]
                        # Ensure required fields have default values
                        if "start_position" not in name_ref or name_ref["start_position"] is None:
                            name_ref["start_position"] = 0
                        if "end_position" not in name_ref or name_ref["end_position"] is None:
                            name_ref["end_position"] = 0
                        if "document_id" not in name_ref:
                            name_ref["document_id"] = cleaned.get("document_id", "unknown")
        
        return cleaned

    def validate_extraction(self, extraction: StakeholderExtraction) -> Tuple[bool, List[str]]:
        """Validate extraction quality and return validation results"""
        issues = []
        
        # Check overall confidence
        if extraction.extraction_confidence < 0.6:
            issues.append(f"Low overall extraction confidence: {extraction.extraction_confidence:.2f}")
        
        # Check individual stakeholder confidence
        low_confidence = extraction.get_low_confidence_stakeholders(threshold=0.7)
        if low_confidence:
            issues.append(f"{len(low_confidence)} stakeholders below confidence threshold")
        
        # Check for missing references
        missing_refs = sum(1 for s in extraction.stakeholders if not s.name_reference)
        if missing_refs > 0:
            issues.append(f"{missing_refs} stakeholders missing source references")
        
        # Check for very short stakeholder names (potential errors)
        short_names = [s.name for s in extraction.stakeholders if len(s.name) < 3]
        if short_names:
            issues.append(f"Suspiciously short stakeholder names: {short_names}")
        
        is_valid = len(issues) == 0
        return is_valid, issues

    def _sanitize_stakeholder_data(self, stakeholder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize stakeholder data to handle None values that break Pydantic validation"""
        
        # Ensure extraction_notes is always a string
        if stakeholder_data.get('extraction_notes') is None:
            stakeholder_data['extraction_notes'] = ""  # Empty string instead of None
        
        # Ensure other string fields are not None
        string_fields = ['name', 'role', 'organization']
        for field in string_fields:
            if stakeholder_data.get(field) is None:
                stakeholder_data[field] = ""
        
        # Ensure list fields are not None
        list_fields = ['concerns', 'responsibilities', 'collaborates_with']
        for field in list_fields:
            if stakeholder_data.get(field) is None:
                stakeholder_data[field] = []
        
        return stakeholder_data

    def _clean_stakeholder_data(self, stakeholder_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean stakeholder data to ensure Pydantic validation passes"""
        
        # Remove None values for fields that have defaults, so Pydantic uses defaults
        fields_with_defaults = [
            'extraction_notes',  # Default: ""
            'role',              # Default: None (but explicitly allow)
            'organization',      # Default: None (but explicitly allow)
            'influence_level',   # Default: None (but explicitly allow)
            'interest_level',    # Default: None (but explicitly allow)
            'name_reference',    # Default: None (but explicitly allow)
            'role_reference',    # Default: None (but explicitly allow)
        ]
        
        cleaned_data = stakeholder_data.copy()
        
        # For extraction_notes specifically, convert None to empty string
        if cleaned_data.get('extraction_notes') is None:
            cleaned_data['extraction_notes'] = ""
        
        # For other fields, remove None values to let Pydantic use defaults
        for field in fields_with_defaults:
            if field in cleaned_data and cleaned_data[field] is None and field != 'extraction_notes':
                del cleaned_data[field]  # Let Pydantic use the default
        
        # Ensure list fields are never None
        list_fields = ['concerns', 'responsibilities', 'collaborates_with', 'concern_references']
        for field in list_fields:
            if cleaned_data.get(field) is None:
                cleaned_data[field] = []
        
        return cleaned_data

    def _sanitize_extraction_data(self, extraction_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize extraction data before creating Pydantic models"""
        
        if 'stakeholders' in extraction_dict and isinstance(extraction_dict['stakeholders'], list):
            sanitized_stakeholders = []
            
            for stakeholder in extraction_dict['stakeholders']:
                if isinstance(stakeholder, dict):
                    # Clean each stakeholder
                    clean_stakeholder = stakeholder.copy()
                    
                    # Fix extraction_notes - convert None to empty string
                    if clean_stakeholder.get('extraction_notes') is None:
                        clean_stakeholder['extraction_notes'] = ""
                    
                    # Ensure required fields have values
                    if not clean_stakeholder.get('name'):
                        clean_stakeholder['name'] = "Unknown Stakeholder"
                    
                    # Ensure confidence_score is present and valid
                    if 'confidence_score' not in clean_stakeholder or clean_stakeholder['confidence_score'] is None:
                        clean_stakeholder['confidence_score'] = 0.5  # Default reasonable confidence
                    
                    # Ensure lists are not None
                    list_fields = ['concerns', 'responsibilities', 'collaborates_with']
                    for field in list_fields:
                        if clean_stakeholder.get(field) is None:
                            clean_stakeholder[field] = []
                    
                    sanitized_stakeholders.append(clean_stakeholder)
            
            extraction_dict['stakeholders'] = sanitized_stakeholders
        
        return extraction_dict

    def _clean_github_response(self, parsed_response: dict, document_id: str, document_title: str) -> dict:
        """Clean GitHub response data to ensure Pydantic validation passes"""
        
        stakeholders = parsed_response.get('stakeholders', [])
        cleaned_stakeholders = []
        
        for stakeholder_data in stakeholders:
            if isinstance(stakeholder_data, dict):
                cleaned = stakeholder_data.copy()
                
                # Fix the extraction_notes issue!
                if cleaned.get('extraction_notes') is None:
                    cleaned['extraction_notes'] = ""
                
                # Ensure required fields
                if not cleaned.get('name') or not cleaned['name'].strip():
                    continue
                
                cleaned['name'] = cleaned['name'].strip()
                
                # Ensure confidence_score is valid
                if 'confidence_score' not in cleaned or cleaned['confidence_score'] is None:
                    cleaned['confidence_score'] = 0.7
                
                confidence = cleaned['confidence_score']
                if confidence < 0.3:
                    cleaned['confidence_score'] = 0.3
                elif confidence > 1.0:
                    cleaned['confidence_score'] = 1.0
                
                # Ensure lists are not None
                for field in ['concerns', 'responsibilities', 'collaborates_with']:
                    if cleaned.get(field) is None:
                        cleaned[field] = []
                
                # Add basic reference
                cleaned['name_reference'] = DocumentReference(
                    document_id=document_id,
                    paragraph_number=1,
                    sentence_number=1,
                    start_position=0,
                    end_position=0,
                    source_text=f"Extracted from: {cleaned['name']}"
                )
                
                cleaned_stakeholders.append(cleaned)
        
        return {
            "document_id": document_id,
            "document_title": document_title,
            "stakeholders": cleaned_stakeholders,
            "extraction_confidence": parsed_response.get('extraction_confidence', 0.8),
            "extraction_method": "GitHub-structured",
            "provider_used": "github"
        }


# Export main class
__all__ = ["StructuredExtractionAdapter"]
