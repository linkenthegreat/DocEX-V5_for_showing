"""
DataExtractor for testing LLM extraction capabilities
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

class DataExtractor:
    """Simple extraction service for testing LLM capabilities."""
    
    def __init__(self, model="llama3.1:8b-instruct-q8_0", base_url="http://localhost:11434", timeout=300):
        self.logger = logging.getLogger(__name__)
        from .llm_client import LLMClient
        self.client = LLMClient(model=model, base_url=base_url, timeout=timeout)
        
    def extract_from_text(self, text, extraction_type, output_format="json"):
        """Extract data from text using appropriate prompt template.
        
        Args:
            text: Document text to analyze
            extraction_type: Type of extraction (stakeholder_info, relationships, etc.)
            output_format: Format for extraction (json, csv, rdf)
        """
        # Use pathlib for cross-platform compatibility
        self.logger.info(f"Extracting {extraction_type} using {output_format} format")
        
        # Get project root directory for consistent path resolution
        project_root = Path(__file__).parent.parent.parent
        
        # Create a list of possible paths to check for the prompt file
        possible_paths = [
            # Correct spelling
            project_root / "prompt" / "data_extraction" / "ollama" / f"{output_format}_extraction" / f"{extraction_type}.txt"
            # Alternative spelling that might exist
        ]
        
        # Find the first valid prompt path
        prompt_path = None
        for path in possible_paths:
            if path.exists():
                prompt_path = path
                self.logger.info(f"Found prompt file at {prompt_path}")
                break
        
        if not prompt_path:
            error_msg = f"Prompt file not found for {extraction_type} with format {output_format}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()
            
            # Add the text to the prompt
            full_prompt = f"{prompt_template}\n\nDOCUMENT:\n{text}"
            
            # Get response from LLM
            self.logger.info(f"Sending document with {len(text)} chars to LLM for extraction")
            return self.client.analyze_text(full_prompt)
            
        except FileNotFoundError:
            error_msg = f"Prompt template not found: {prompt_path}"
            self.logger.error(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Error during extraction: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}
    
    def extract_from_file(self, file_path, extraction_type, output_format="json", start_page=None, end_page=None):
        """Extract information from specific pages of a document file"""
        from app.utils.document_processor import DocumentProcessor
        
        self.logger.info(f"Processing file {file_path} for {extraction_type} extraction")
        
        # Process the document with page range if specified
        doc_processor = DocumentProcessor()
        doc_result = doc_processor.extract_from_file(file_path, start_page, end_page)
        
        if "error" in doc_result:
            return doc_result
            
        # If document has tables, use smaller chunks
        if doc_result.get("has_tables", False):
            self.logger.info("Document contains tables - using smaller chunks for processing")
            
            # Extract text without tables first
            narrative_text = ""
            table_sections = []
            
            for page in doc_result["pages"]:
                page_text = page["text"]
                # Simple table detection
                if "|" in page_text or "\t\t" in page_text:
                    # Process table sections separately
                    table_sections.append(page_text)
                else:
                    narrative_text += page_text
            
            # Process narrative text first
            self.logger.info(f"Processing narrative text ({len(narrative_text)} chars)")
            narrative_result = self.extract_from_text(narrative_text, extraction_type, output_format)
            
            # Skip table processing if narrative text already produced good results
            # or add table processing here if needed
            
            extraction_result = narrative_result
        else:
            # Regular processing for non-table documents
            extraction_result = self.extract_from_text(doc_result["text"], extraction_type, output_format)
        
        # Add document metadata to the result
        result = {
            "file_info": {
                "path": str(file_path),
                "page_count": doc_result.get("page_count", 0),
                "pages_extracted": f"{start_page or 1}-{end_page or doc_result.get('page_count', 0)}",
                "has_tables": doc_result.get("has_tables", False),
                "has_images": doc_result.get("has_images", False),
            },
            "extraction": extraction_result
        }
        
        return result
