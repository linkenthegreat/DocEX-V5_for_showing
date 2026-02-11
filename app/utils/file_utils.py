"""
File System Utilities

This module provides helper functions for file operations, metadata extraction,
and file system navigation required by the DocEX application.

Functions:
    - calculate_file_hash: Computes the MD5 hash of a file.
    - get_file_metadata: Retrieves metadata for a given file or directory.
    - get_existing_records: Reads existing records from a CSV file.
    - save_records_to_csv: Saves file metadata records to a CSV file.
    - extract_file_content: Extracts text content from various file types (PDF, DOCX, etc.).
    - ensure_database_structure: Ensures the database directories and files exist.
    - initialize_csv_file: Creates a new CSV file with headers.

This module supports the file management and navigation features of the
DocEX system and provides essential file metadata for RDF representation.
"""

import os
import csv
import hashlib
import mimetypes
from datetime import datetime
from flask import current_app

# Define file information fields as a constant
SELECTED_FILE_INFO = ['name', 'is_dir', 'size', 'access_date', 'create_date', 'modified_date', 
                     'file_type', 'directory', 'file_hash']

def calculate_file_hash(file_path):
    """Calculate MD5 hash of a file"""
    if not os.path.isfile(file_path):
        return None
    
    # For large files, read in chunks to avoid memory issues
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            md5.update(chunk)
    return md5.hexdigest()

def get_file_metadata(file_path):
    """Get comprehensive metadata for a file"""
    if not os.path.exists(file_path):
        return None
    
    item_stat = os.stat(file_path)
    current_hash = calculate_file_hash(file_path) if os.path.isfile(file_path) else None
    
    return {
        'name': os.path.basename(file_path),
        'is_dir': os.path.isdir(file_path),
        'size': item_stat.st_size,
        'access_date': datetime.fromtimestamp(item_stat.st_atime).strftime('%Y-%m-%d %H:%M:%S'),
        'create_date': datetime.fromtimestamp(item_stat.st_birthtime).strftime('%Y-%m-%d %H:%M:%S'),
        'modified_date': datetime.fromtimestamp(item_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'file_type': mimetypes.guess_type(file_path)[0] or 'Unknown',
        'directory': os.path.dirname(file_path),
        'file_hash': current_hash
    }

def get_existing_records():
    """Read existing records from the CSV file"""
    csv_file = current_app.config['CSV_FILE']
    records = {}
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                key = f"{row['directory']}/{row['name']}"
                records[key] = row
    
    return records

def save_records_to_csv(records):
    """Save records to CSV file"""
    csv_file = current_app.config['CSV_FILE']
    
    # Make sure directory exists
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)
    
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=SELECTED_FILE_INFO)
        writer.writeheader()
        for record in records:
            writer.writerow(record)

def extract_file_content(file_path):
    """Extract text content from a file based on its type"""
    if not os.path.exists(file_path):
        return "File does not exist"
    
    file_type = mimetypes.guess_type(file_path)[0]
    
    try:
        current_app.logger.info(f"Extracting content from {file_path} (type: {file_type})")
        
        # Text files
        if file_type and (file_type.startswith('text/') or file_type == 'application/json'):
            with open(file_path, 'r', errors='ignore') as file:
                return file.read()
        
        # PDF files
        elif file_type == 'application/pdf':
            try:
                current_app.logger.info(f"Attempting to extract text from PDF: {file_path}")
                
                from PyPDF2 import PdfReader
                
                # Open the PDF file
                reader = PdfReader(file_path)
                current_app.logger.info(f"PDF opened successfully, pages: {len(reader.pages)}")
                
                # Extract text from all pages
                text = ""
                for i, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
                        else:
                            current_app.logger.warning(f"No text extracted from page {i+1}")
                    except Exception as page_error:
                        current_app.logger.error(f"Error extracting text from page {i+1}: {str(page_error)}")
                
                if not text.strip():
                    current_app.logger.warning("PDF appears to contain no extractable text (may be scanned/image-based)")
                    return "[PDF contains no extractable text. The PDF may be scanned or image-based.]"
                    
                return text
                
            except ImportError:
                current_app.logger.error("PyPDF2 package is not installed")
                return "[PDF extraction requires PyPDF2 package]"
                
            except Exception as e:
                current_app.logger.error(f"Error processing PDF {file_path}: {str(e)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                return f"[Error extracting PDF content: {str(e)}]"
        
        # DOCX files
        elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            try:
                from docx import Document
                doc = Document(file_path)
                return "\n\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
            except ImportError:
                return "[DOCX extraction requires python-docx package]"
            except Exception as e:
                current_app.logger.error(f"Error extracting DOCX content: {str(e)}")
                return f"[Error extracting DOCX content: {str(e)}]"
        
        # DOC files (old MS Word format)
        elif file_type == 'application/msword':
            return "[DOC extraction requires additional libraries - consider converting to DOCX]"
        
        # Image files
        elif file_type and file_type.startswith('image/'):
            return "[Image file - content extraction requires OCR]"
        
        # Other file types
        else:
            return f"[Content extraction not supported for {file_type}]"
            
    except Exception as e:
        current_app.logger.error(f"Error extracting content: {str(e)}")
        return f"Error extracting content: {str(e)}"

def ensure_database_structure():
    """Ensure database directories and files exist"""
    # Get paths from config
    csv_file = current_app.config['CSV_FILE']
    database_dir = current_app.config['DATABASE_DIR']
    triples_dir = current_app.config['TRIPLES_DIR']
    
    # Create directories
    os.makedirs(database_dir, exist_ok=True)
    os.makedirs(triples_dir, exist_ok=True)
    
    # Initialize CSV file if it doesn't exist
    if not os.path.exists(csv_file):
        initialize_csv_file()
    
    return True

def initialize_csv_file():
    """Create a new CSV file with headers"""
    csv_file = current_app.config['CSV_FILE']
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=SELECTED_FILE_INFO)
        writer.writeheader()
    return csv_file