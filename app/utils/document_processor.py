"""
DocumentProcessor for extracting text and structure from document files
"""
import os
from pathlib import Path
import logging
import fitz  # PyMuPDF

class DocumentProcessor:
    """Extracts text and identifies basic structure elements from document files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_from_file(self, file_path, start_page=None, end_page=None):
        """Extract text and structure from a document file based on its extension"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}
            
        ext = file_path.suffix.lower()
        
        if ext == ".pdf":
            return self.extract_from_pdf(file_path, start_page, end_page)
        elif ext == ".docx":
            return self.extract_from_docx(file_path)
        else:
            self.logger.warning(f"Unsupported file format: {ext}")
            return {"error": f"Unsupported file format: {ext}"}
    
    def extract_from_pdf(self, file_path, start_page=None, end_page=None):
        """Extract text and detect tables/images from specific PDF pages
        
        Args:
            file_path: Path to the PDF file
            start_page: First page to extract (1-indexed, optional)
            end_page: Last page to extract (1-indexed, optional)
        """
        self.logger.info(f"Extracting text from {file_path}{' pages '+str(start_page)+'-'+str(end_page) if start_page else ''}")
        result = {
            "text": "",
            "pages": [],
            "has_tables": False,
            "has_images": False,
            "page_count": 0,
            "metadata": {},
            "extracted_range": {"start": start_page, "end": end_page} if start_page else None
        }
        
        try:
            doc = fitz.open(file_path)
            result["page_count"] = len(doc)
            result["metadata"] = self._extract_pdf_metadata(doc)
            
            # Adjust page range to valid numbers
            if start_page is not None:
                start_idx = max(0, min(start_page - 1, len(doc) - 1))  # Convert 1-indexed to 0-indexed
            else:
                start_idx = 0
                
            if end_page is not None:
                end_idx = max(start_idx, min(end_page - 1, len(doc) - 1))  # Convert 1-indexed to 0-indexed
            else:
                end_idx = len(doc) - 1
            
            # Process only the specified page range
            for page_idx in range(start_idx, end_idx + 1):
                page = doc[page_idx]
                page_text = page.get_text()
                result["text"] += page_text
                
                # Basic image detection
                images = page.get_images()
                if images:
                    result["has_images"] = True
                
                # Basic table detection
                if self._detect_table_in_text(page_text):
                    result["has_tables"] = True
                
                # Add page details
                result["pages"].append({
                    "page_num": page_idx + 1,  # Convert back to 1-indexed
                    "text": page_text,
                    "image_count": len(images)
                })
            
            extracted_pages = end_idx - start_idx + 1
            self.logger.info(f"Successfully extracted {extracted_pages} pages from {file_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"PDF extraction failed: {str(e)}")
            return {"error": f"PDF extraction failed: {str(e)}"}
    
    def extract_from_docx(self, file_path):
        """Extract text from DOCX"""
        self.logger.warning("DOCX extraction not yet implemented")
        return {"error": "DOCX extraction not yet implemented"}
    
    def _extract_pdf_metadata(self, doc):
        """Extract metadata from PDF document"""
        metadata = {}
        for key, value in doc.metadata.items():
            if value:  # Only include non-empty values
                metadata[key] = value
        return metadata
    
    def _detect_table_in_text(self, text):
        """Simple heuristic to detect tables in text"""
        # Look for common table indicators
        table_indicators = [
            # Multiple lines with consistent pipe or tab separators
            any(line.count("|") >= 3 for line in text.split("\n")),
            # Repeated tab characters
            "\t\t" in text,
            # Grid-like structures with dashes and plus signs
            "+--+" in text or "+--" in text or "--+" in text,
            # Multiple sequential spaces (potential alignment)
            any(line.count("    ") >= 3 for line in text.split("\n"))
        ]
        
        return any(table_indicators)
    
    def _process_tables(self, text):
        """Convert detected tables to a more LLM-friendly format"""
        import re
        
        # Simple detection of table-like structures
        table_patterns = [
            # Multiple lines with pipe separators
            r'([^\n]+\|[^\n]+\n){3,}',
            # Lines with multiple sequential spaces (potential alignment)
            r'([^\n]+\s{3,}[^\n]+\n){3,}'
        ]
        
        for pattern in table_patterns:
            tables = re.finditer(pattern, text)
            for table_match in tables:
                table_text = table_match.group(0)
                
                # Convert to markdown table format
                try:
                    processed_table = self._convert_to_markdown_table(table_text)
                    # Replace the original table with the markdown version
                    text = text.replace(table_text, "\n" + processed_table + "\n")
                except Exception as e:
                    self.logger.warning(f"Failed to process table: {e}")
        
        return text

    def _convert_to_markdown_table(self, table_text):
        """Convert detected table to markdown format"""
        lines = table_text.strip().split('\n')
        
        # Try to determine delimiter based on content
        if '|' in lines[0]:
            delimiter = '|'
        else:
            # Assume space-aligned table, convert to pipe table
            lines = [' | '.join(line.split()) for line in lines]
            delimiter = '|'
        
        # Add markdown table formatting
        if len(lines) > 1:
            # Insert separator row after header
            max_cols = max(line.count(delimiter) for line in lines) + 1
            separator = '| ' + ' | '.join(['---'] * max_cols) + ' |'
            lines.insert(1, separator)
        
        # Ensure all lines have proper markdown table formatting
        formatted_lines = []
        for line in lines:
            if not line.startswith('|'):
                line = '| ' + line
            if not line.endswith('|'):
                line = line + ' |'
            formatted_lines.append(line)
        
        return "\n".join(formatted_lines)