"""
Updated JSON-LD Extraction Bridge - Fixed to handle Pydantic models
"""
import logging
from typing import Dict, List, Any, Optional, Union
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class JSONLDExtractionBridge:
    """Bridge between JSON-LD documents and text-based extraction - Updated for Pydantic models"""
    
    def __init__(self, text_extraction_adapter):
        """Initialize with existing text-based extraction adapter"""
        self.text_adapter = text_extraction_adapter
        self.logger = logging.getLogger(__name__)
    
    async def extract_stakeholders_from_jsonld(
        self, 
        document_jsonld: Dict[str, Any], 
        provider: str = None
    ) -> Dict[str, Any]:
        """
        Extract stakeholders from JSON-LD document
        Returns structured result in JSON format
        """
        try:
            doc_id = document_jsonld.get('@id', 'unknown')
            doc_title = self._extract_document_title(document_jsonld)
            
            self.logger.info(f"Starting JSON-LD stakeholder extraction for: {doc_id}")
            
            # Extract text content from JSON-LD
            extracted_text = self._extract_text_from_jsonld(document_jsonld)
            
            if not extracted_text.strip():
                self.logger.warning(f"No text content found in JSON-LD document: {doc_id}")
                return self._create_empty_result(doc_id, doc_title, "No text content found")
            
            self.logger.info(f"Extracted {len(extracted_text)} characters of text from JSON-LD")
            
            # Call the appropriate text-based extraction method with required parameters
            extraction_result = await self._call_text_extraction(
                extracted_text, doc_id, doc_title, provider
            )
            
            # Convert result to structured format - NOW HANDLES PYDANTIC MODELS
            structured_result = self._process_extraction_result(
                extraction_result, document_jsonld, extracted_text
            )
            
            self.logger.info(f"JSON-LD extraction completed for: {doc_id}")
            return structured_result
            
        except Exception as e:
            self.logger.error(f"Error in JSON-LD stakeholder extraction: {e}")
            doc_id = document_jsonld.get('@id', 'unknown')
            doc_title = self._extract_document_title(document_jsonld)
            return self._create_error_result(doc_id, doc_title, str(e))
    
    def _extract_document_title(self, document_jsonld: Dict[str, Any]) -> str:
        """Extract document title from JSON-LD"""
        title_fields = ['docex:title', 'dcterms:title', 'title', '@title']
        
        for field in title_fields:
            title = document_jsonld.get(field, '')
            if title and title.strip():
                return title.strip()
        
        doc_id = document_jsonld.get('@id', '')
        if doc_id:
            return f"Document {doc_id}"
        
        return "Untitled Document"
    
    def _extract_text_from_jsonld(self, document_jsonld: Dict[str, Any]) -> str:
        """Extract all readable text from JSON-LD document"""
        text_parts = []
        
        try:
            # Check for direct text content field
            if 'docex:textContent' in document_jsonld:
                text_content = document_jsonld['docex:textContent']
                if text_content and text_content.strip():
                    text_parts.append(text_content)
                    self.logger.debug("Found direct text content in docex:textContent")
            
            # Extract title
            title = self._extract_document_title(document_jsonld)
            if title and title != "Untitled Document":
                text_parts.append(f"Document Title: {title}")
            
            # Extract paragraph content
            if 'docex:hasParagraph' in document_jsonld:
                paragraphs = document_jsonld['docex:hasParagraph']
                
                if isinstance(paragraphs, list):
                    self.logger.debug(f"Found {len(paragraphs)} paragraphs in JSON-LD")
                    
                    for i, para in enumerate(paragraphs):
                        para_text = para.get('docex:paragraphText', '')
                        if para_text and para_text.strip():
                            text_parts.append(f"Paragraph {i+1}: {para_text.strip()}")
                
                elif isinstance(paragraphs, dict):
                    para_text = paragraphs.get('docex:paragraphText', '')
                    if para_text and para_text.strip():
                        text_parts.append(f"Content: {para_text.strip()}")
            
            final_text = "\n\n".join(text_parts)
            self.logger.debug(f"Extracted text length: {len(final_text)} characters")
            
            return final_text
            
        except Exception as e:
            self.logger.error(f"Error extracting text from JSON-LD: {e}")
            return ""
    
    async def _call_text_extraction(
        self, 
        text: str, 
        document_id: str, 
        document_title: str, 
        provider: str = None
    ) -> Any:
        """Call the appropriate text-based extraction method with required parameters"""
        
        try:
            # Use provider-specific methods if available
            if provider == 'openai' and hasattr(self.text_adapter, 'extract_stakeholders_openai'):
                self.logger.info("Using OpenAI extraction")
                return await self.text_adapter.extract_stakeholders_openai(
                    text, document_id, document_title
                )
            
            elif provider == 'ollama' and hasattr(self.text_adapter, 'extract_stakeholders_ollama'):
                self.logger.info("Using Ollama extraction")
                return await self.text_adapter.extract_stakeholders_ollama(
                    text, document_id, document_title
                )
            
            elif provider == 'github' and hasattr(self.text_adapter, 'extract_stakeholders_github'):
                self.logger.info("Using GitHub extraction")
                return await self.text_adapter.extract_stakeholders_github(
                    text, document_id, document_title
                )
            
            elif hasattr(self.text_adapter, 'extract_stakeholders'):
                # Use default extraction method
                self.logger.info("Using default stakeholder extraction")
                return await self.text_adapter.extract_stakeholders(
                    text, document_id, document_title
                )
            
            else:
                raise AttributeError("No suitable extraction method found in text adapter")
                
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            raise
    
    def _process_extraction_result(
        self, 
        extraction_result: Any, 
        original_jsonld: Dict[str, Any], 
        extracted_text: str
    ) -> Dict[str, Any]:
        """Process and structure the extraction result - UPDATED FOR PYDANTIC MODELS"""
        
        doc_id = original_jsonld.get('@id', 'unknown')
        doc_title = self._extract_document_title(original_jsonld)
        
        try:
            stakeholders = []
            extraction_metadata = {}
            
            # Handle Pydantic StakeholderExtraction model (YOUR ACTUAL RESULT TYPE!)
            if hasattr(extraction_result, 'stakeholders') and hasattr(extraction_result, 'document_id'):
                self.logger.info("Processing Pydantic StakeholderExtraction model")
                
                # Extract stakeholders from Pydantic model
                pydantic_stakeholders = extraction_result.stakeholders
                
                for stakeholder in pydantic_stakeholders:
                    stakeholder_dict = {
                        "name": getattr(stakeholder, 'name', 'Unknown'),
                        "type": self._extract_stakeholder_type(stakeholder),
                        "role": getattr(stakeholder, 'role', None),
                        "organization": getattr(stakeholder, 'organization', None),
                        "concerns": getattr(stakeholder, 'concerns', []),
                        "responsibilities": getattr(stakeholder, 'responsibilities', []),
                        "collaborates_with": getattr(stakeholder, 'collaborates_with', []),
                        "influence_level": self._extract_enum_value(getattr(stakeholder, 'influence_level', None)),
                        "interest_level": self._extract_enum_value(getattr(stakeholder, 'interest_level', None)),
                        "confidence_score": getattr(stakeholder, 'confidence_score', 0.0),
                        "extraction_notes": getattr(stakeholder, 'extraction_notes', ''),
                        "references": self._extract_references(stakeholder)
                    }
                    stakeholders.append(stakeholder_dict)
                
                # Extract metadata from Pydantic model
                extraction_metadata = {
                    "total_stakeholders": len(stakeholders),
                    "extraction_method": getattr(extraction_result, 'extraction_method', 'unknown'),
                    "extraction_confidence": getattr(extraction_result, 'extraction_confidence', 0.0),
                    "provider_used": getattr(extraction_result, 'provider_used', 'unknown'),
                    "processing_time_seconds": getattr(extraction_result, 'processing_time_seconds', None),
                    "total_paragraphs": getattr(extraction_result, 'total_paragraphs', None),
                    "total_sentences": getattr(extraction_result, 'total_sentences', None),
                    "extracted_at": str(getattr(extraction_result, 'extracted_at', datetime.now())),
                    "original_result_type": str(type(extraction_result)),
                    "has_paragraphs": 'docex:hasParagraph' in original_jsonld,
                    "has_text_content": 'docex:textContent' in original_jsonld,
                    "status": "completed"
                }
            
            # Handle other result formats (fallback)
            elif isinstance(extraction_result, dict):
                if 'stakeholders' in extraction_result:
                    stakeholders = extraction_result['stakeholders']
                extraction_metadata = {
                    "total_stakeholders": len(stakeholders),
                    "extraction_method": "dict_format",
                    "status": "completed"
                }
            
            elif isinstance(extraction_result, str):
                try:
                    parsed_result = json.loads(extraction_result)
                    if isinstance(parsed_result, dict) and 'stakeholders' in parsed_result:
                        stakeholders = parsed_result['stakeholders']
                except json.JSONDecodeError:
                    pass
                extraction_metadata = {
                    "total_stakeholders": len(stakeholders),
                    "extraction_method": "string_parsed",
                    "status": "completed"
                }
            
            elif isinstance(extraction_result, list):
                stakeholders = extraction_result
                extraction_metadata = {
                    "total_stakeholders": len(stakeholders),
                    "extraction_method": "list_format",
                    "status": "completed"
                }
            
            # Create structured result
            structured_result = {
                "document_id": doc_id,
                "document_title": doc_title,
                "extraction_timestamp": datetime.now().isoformat(),
                "text_length": len(extracted_text),
                "stakeholders": stakeholders,
                "extraction_metadata": extraction_metadata
            }
            
            self.logger.info(f"Processed extraction result: {len(stakeholders)} stakeholders found")
            return structured_result
            
        except Exception as e:
            self.logger.error(f"Error processing extraction result: {e}")
            return self._create_error_result(doc_id, doc_title, f"Result processing error: {str(e)}")
    
    def _extract_stakeholder_type(self, stakeholder) -> str:
        """Extract stakeholder type from Pydantic enum"""
        try:
            stakeholder_type = getattr(stakeholder, 'stakeholder_type', None)
            if stakeholder_type:
                if hasattr(stakeholder_type, 'value'):
                    return stakeholder_type.value
                else:
                    return str(stakeholder_type)
            return 'Unknown'
        except:
            return 'Unknown'
    
    def _extract_enum_value(self, enum_field) -> str:
        """Extract value from Pydantic enum field"""
        try:
            if enum_field and hasattr(enum_field, 'value'):
                return enum_field.value
            elif enum_field:
                return str(enum_field)
            return None
        except:
            return None
    
    def _extract_references(self, stakeholder) -> Dict[str, Any]:
        """Extract document references from stakeholder"""
        try:
            references = {}
            
            name_ref = getattr(stakeholder, 'name_reference', None)
            if name_ref:
                references['name_reference'] = {
                    "document_id": getattr(name_ref, 'document_id', None),
                    "paragraph_number": getattr(name_ref, 'paragraph_number', None),
                    "sentence_number": getattr(name_ref, 'sentence_number', None),
                    "source_text": getattr(name_ref, 'source_text', None)
                }
            
            role_ref = getattr(stakeholder, 'role_reference', None)
            if role_ref:
                references['role_reference'] = {
                    "document_id": getattr(role_ref, 'document_id', None),
                    "paragraph_number": getattr(role_ref, 'paragraph_number', None),
                    "sentence_number": getattr(role_ref, 'sentence_number', None),
                    "source_text": getattr(role_ref, 'source_text', None)
                }
            
            return references
        except:
            return {}
    
    def _create_empty_result(self, doc_id: str, doc_title: str, reason: str) -> Dict[str, Any]:
        """Create empty result structure"""
        return {
            "document_id": doc_id,
            "document_title": doc_title,
            "extraction_timestamp": datetime.now().isoformat(),
            "text_length": 0,
            "stakeholders": [],
            "extraction_metadata": {
                "total_stakeholders": 0,
                "extraction_method": "jsonld_bridge",
                "status": "empty",
                "reason": reason
            }
        }
    
    def _create_error_result(self, doc_id: str, doc_title: str, error_message: str) -> Dict[str, Any]:
        """Create error result structure"""
        return {
            "document_id": doc_id,
            "document_title": doc_title,
            "extraction_timestamp": datetime.now().isoformat(),
            "text_length": 0,
            "stakeholders": [],
            "extraction_metadata": {
                "total_stakeholders": 0,
                "extraction_method": "jsonld_bridge",
                "status": "error",
                "error": error_message
            }
        }
    
    def get_extraction_summary(self, result: Dict[str, Any]) -> str:
        """Generate human-readable summary of extraction results"""
        
        doc_id = result.get('document_id', 'Unknown')
        doc_title = result.get('document_title', 'Untitled')
        stakeholder_count = len(result.get('stakeholders', []))
        text_length = result.get('text_length', 0)
        
        metadata = result.get('extraction_metadata', {})
        status = metadata.get('status', 'completed')
        
        if status == 'error':
            return f"Extraction failed for {doc_id}: {metadata.get('error', 'Unknown error')}"
        
        elif status == 'empty':
            return f"No content found in {doc_id}: {metadata.get('reason', 'Unknown reason')}"
        
        else:
            extraction_method = metadata.get('extraction_method', 'unknown')
            confidence = metadata.get('extraction_confidence', 0.0)
            provider = metadata.get('provider_used', 'unknown')
            
            return f"""Extraction Summary for {doc_id}:
- Document: {doc_title}
- Text processed: {text_length} characters
- Stakeholders found: {stakeholder_count}
- Status: {status}
- Method: {extraction_method}
- Provider: {provider}
- Confidence: {confidence}
- Has paragraphs: {metadata.get('has_paragraphs', False)}
- Has text content: {metadata.get('has_text_content', False)}"""