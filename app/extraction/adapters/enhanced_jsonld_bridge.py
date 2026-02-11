"""
Enhanced JSON-LD Bridge for DocEX
Connects JSON-LD metadata with stakeholder extraction using actual document data
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

def extract_stakeholders_from_jsonld_metadata(filename: str, jsonld_dir: str = None) -> Dict[str, Any]:
    """
    Extract stakeholders based on actual JSON-LD metadata file
    This replaces the test data approach with real document processing
    
    Args:
        filename: Name of the file to extract from
        jsonld_dir: Path to JSON-LD directory (passed from agent to avoid app context issues)
    """
    try:
        print(f"🔍 Starting extraction for filename: {filename}")
        
        # Use passed jsonld_dir or fallback to default path
        if not jsonld_dir:
            # Default path when running without Flask context
            current_dir = os.path.dirname(os.path.abspath(__file__))
            jsonld_dir = os.path.join(current_dir, '..', '..', '..', 'database', 'jsonld')
            jsonld_dir = os.path.abspath(jsonld_dir)
        
        # Look for the JSON-LD file
        jsonld_path = os.path.join(jsonld_dir, filename)
        
        # Try different file extensions if exact match not found
        if not os.path.exists(jsonld_path):
            # Try with .json extension
            if not filename.endswith('.json'):
                jsonld_path = os.path.join(jsonld_dir, f"{filename}.json")
            
            # Try without .ttl extension if present
            if not os.path.exists(jsonld_path) and filename.endswith('.ttl'):
                base_name = filename.replace('.ttl', '')
                jsonld_path = os.path.join(jsonld_dir, f"{base_name}.json")
        
        print(f"🔍 Looking for JSON-LD file at: {jsonld_path}")
        
        if not os.path.exists(jsonld_path):
            print(f"❌ JSON-LD file not found: {jsonld_path}")
            print(f"📁 Directory contents: {os.listdir(jsonld_dir) if os.path.exists(jsonld_dir) else 'Directory not found'}")
            return generate_error_result(filename, f"JSON-LD file not found: {jsonld_path}")
        
        # Load the JSON-LD metadata file
        with open(jsonld_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        print(f"✅ Successfully loaded JSON-LD metadata from: {jsonld_path}")
        
        # Extract document content and structure for stakeholder identification
        document_content = extract_document_content_from_metadata(metadata)
        document_structure = extract_document_structure_from_metadata(metadata)
        
        print(f"📄 Document content length: {len(document_content)} characters")
        print(f"📄 Document structure: {len(document_structure.get('paragraphs', []))} paragraphs")
        
        # Perform stakeholder extraction based on actual content
        stakeholders = perform_stakeholder_extraction(
            document_content=document_content,
            document_structure=document_structure,
            source_filename=filename,
            metadata=metadata
        )
        
        # Generate extraction results with provenance
        extraction_result = create_extraction_result(
            stakeholders=stakeholders,
            source_filename=filename,
            metadata=metadata
        )
        
        print(f"✅ Extraction completed: {len(stakeholders)} stakeholders found")
        return extraction_result
        
    except Exception as e:
        print(f"❌ Error in stakeholder extraction: {e}")
        import traceback
        traceback.print_exc()
        return generate_error_result(filename, str(e))

def extract_document_content_from_metadata(metadata: Dict[str, Any]) -> str:
    """Extract the actual document text content from JSON-LD metadata"""
    try:
        # Look for text content in various JSON-LD fields
        content_fields = [
            'docex:textContent',
            'textContent', 
            'content',
            'dcterms:description',
            'description',
            'fullText',
            'text'
        ]
        
        for field in content_fields:
            if field in metadata and metadata[field]:
                content = str(metadata[field])
                if len(content) > 50:  # Only use if it's substantial content
                    print(f"📄 Found content in field: {field} ({len(content)} chars)")
                    return content
        
        # If no direct content, try to extract from document structure
        paragraphs = metadata.get('docex:hasParagraph', [])
        if paragraphs:
            content_parts = []
            for para in paragraphs:
                if isinstance(para, dict):
                    para_text = para.get('docex:textContent') or para.get('textContent', '')
                    if para_text:
                        content_parts.append(para_text)
            
            if content_parts:
                combined_content = '\n'.join(content_parts)
                print(f"📄 Reconstructed content from {len(paragraphs)} paragraphs")
                return combined_content
        
        # Try to extract from any field that might contain text
        for key, value in metadata.items():
            if isinstance(value, str) and len(value) > 100 and any(word in value.lower() for word in ['stakeholder', 'community', 'organization', 'people', 'public']):
                print(f"📄 Found potential content in field: {key}")
                return value
        
        print("⚠️ No substantial text content found in metadata")
        return ""
        
    except Exception as e:
        print(f"❌ Error extracting content: {e}")
        return ""

def extract_document_structure_from_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract document structure information from JSON-LD metadata"""
    try:
        structure = {
            'paragraphs': [],
            'sentences': [],
            'word_count': 0,
            'paragraph_count': 0
        }
        
        # Extract paragraphs from JSON-LD structure
        paragraphs = metadata.get('docex:hasParagraph', [])
        if paragraphs:
            for i, para in enumerate(paragraphs):
                if isinstance(para, dict):
                    para_text = para.get('docex:textContent') or para.get('textContent', '')
                    if para_text:
                        para_info = {
                            'id': para.get('docex:paragraphID', f'para_{i}'),
                            'text': para_text,
                            'paragraph_number': para.get('docex:paragraphNumber', i + 1),
                            'word_count': para.get('docex:wordCount', len(para_text.split())),
                            'sentences': []
                        }
                        
                        # Extract sentences if available
                        sentences = para.get('docex:hasSentence', [])
                        for j, sent in enumerate(sentences):
                            if isinstance(sent, dict):
                                sent_text = sent.get('docex:textContent') or sent.get('textContent', '')
                                if sent_text:
                                    sent_info = {
                                        'id': sent.get('docex:sentenceID', f'sent_{i}_{j}'),
                                        'text': sent_text,
                                        'sentence_number': sent.get('docex:sentenceNumber', j + 1)
                                    }
                                    para_info['sentences'].append(sent_info)
                                    structure['sentences'].append(sent_info)
                        
                        structure['paragraphs'].append(para_info)
                        structure['word_count'] += para_info['word_count']
        
        structure['paragraph_count'] = len(structure['paragraphs'])
        
        print(f"📊 Extracted structure: {structure['paragraph_count']} paragraphs, {len(structure['sentences'])} sentences")
        return structure
        
    except Exception as e:
        print(f"❌ Error extracting structure: {e}")
        return {'paragraphs': [], 'sentences': [], 'word_count': 0, 'paragraph_count': 0}

def get_context_around_name(text: str, name: str, context_length: int = 150) -> str:
    """Get context around a name mention in the text"""
    try:
        index = text.lower().find(name.lower())
        if index == -1:
            return f"Mentioned: {name}"
        
        start = max(0, index - context_length)
        end = min(len(text), index + len(name) + context_length)
        context = text[start:end].strip()
        
        # Clean up context
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
            
        return context
    except:
        return f"Mentioned: {name}"

def perform_stakeholder_extraction(document_content: str, document_structure: Dict[str, Any], 
                                 source_filename: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Perform actual stakeholder extraction using available methods
    Falls back gracefully if LLM components are not available
    """
    try:
        stakeholders = []
        
        if not document_content:
            print("⚠️ No content to extract from, creating placeholder")
            return create_placeholder_stakeholder(source_filename, metadata)
        
        print(f"🤖 Starting stakeholder extraction...")
        print(f"📄 Content length: {len(document_content)} characters")
        
        # Try to use LLM extraction if available
        try:
            stakeholders = try_llm_extraction(document_content, source_filename, metadata)
            if stakeholders:
                print(f"✅ LLM extraction successful: {len(stakeholders)} stakeholders")
                return stakeholders
        except Exception as e:
            print(f"⚠️ LLM extraction failed: {e}")
        
        # Fall back to enhanced pattern matching
        print("🔄 Using enhanced pattern matching extraction...")
        stakeholders = enhanced_pattern_extraction(document_content, source_filename, metadata)
        
        if not stakeholders:
            print("⚠️ No stakeholders found, creating fallback")
            stakeholders = create_placeholder_stakeholder(source_filename, metadata)
        
        print(f"✅ Final extraction result: {len(stakeholders)} stakeholders")
        return stakeholders
        
    except Exception as e:
        print(f"❌ Error in stakeholder extraction: {e}")
        import traceback
        traceback.print_exc()
        return create_placeholder_stakeholder(source_filename, metadata)

def try_llm_extraction(document_content: str, source_filename: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Attempt LLM extraction with proper error handling using existing adapters"""
    try:
        # Try the DataExtractionAgent first (THIS IS YOUR MAIN AI AGENT)
        try:
            from app.llm.ai_agents.data_extraction_agent import DataExtractionAgent
            
            print("🤖 Using DataExtractionAgent...")
            
            agent = DataExtractionAgent()
            
            # Use the CORRECT method name: extract_stakeholders (not extract_data)
            result = agent.extract_stakeholders(
                document_content=document_content,
                document_title=source_filename,
                priority="cost",  # or "quality" for better results
                # You can also specify strategy and model if needed
                # strategy="ollama_structured",
                # model="llama3.1:8b-instruct-q8_0"
            )
            
            if result.success and result.stakeholders:
                # Convert ExtractionResult to the format expected by process_llm_extraction_response
                stakeholders_data = []
                
                for stakeholder in result.stakeholders:
                    stakeholder_dict = {
                        "name": stakeholder.get('name', 'Unknown'),
                        "stakeholderType": stakeholder.get('stakeholderType', 'UNKNOWN'),
                        "role": stakeholder.get('role', 'Stakeholder'),
                        "organization": stakeholder.get('organization', 'Unknown'),
                        "confidenceScore": float(stakeholder.get('confidenceScore', result.extraction_confidence)),
                        "sourceText": f"AI Agent extracted: {stakeholder.get('name')}"
                    }
                    stakeholders_data.append(stakeholder_dict)
                
                processed_stakeholders = process_llm_extraction_response(stakeholders_data)
                if processed_stakeholders:
                    print(f"✅ DataExtractionAgent successful: {len(processed_stakeholders)} stakeholders")
                    print(f"📊 Used strategy: {result.strategy_used}, model: {result.model_used}")
                    print(f"💰 Cost: ${result.cost_estimate:.4f}, Time: {result.processing_time:.2f}s")
                    return processed_stakeholders
        
        except ImportError as e:
            print(f"⚠️ DataExtractionAgent not available: {e}")
        except Exception as e:
            print(f"⚠️ DataExtractionAgent error: {e}")
            import traceback
            traceback.print_exc()
        
        # Try the StructuredExtractionAdapter as backup
        try:
            from app.extraction.adapters.llm_adapter import StructuredExtractionAdapter
            from app.config import Config
            
            print("🔧 Using StructuredExtractionAdapter...")
            
            config = Config()
            llm_adapter = StructuredExtractionAdapter(config)
            
            # Use async extraction method
            import asyncio
            
            async def run_structured_extraction():
                try:
                    result = await llm_adapter.extract_stakeholders(
                        document_text=document_content,
                        document_id=source_filename,
                        document_title=source_filename,
                        provider="auto"
                    )
                    return result
                except Exception as e:
                    print(f"⚠️ StructuredExtractionAdapter failed: {e}")
                    return None
            
            # Run the async extraction
            extraction_result = asyncio.run(run_structured_extraction())
            
            if extraction_result and hasattr(extraction_result, 'stakeholders'):
                # Convert Pydantic model to dict format
                stakeholders_data = []
                
                for stakeholder in extraction_result.stakeholders:
                    stakeholder_dict = {
                        "name": stakeholder.name,
                        "stakeholderType": getattr(stakeholder.stakeholder_type, 'value', str(stakeholder.stakeholder_type)) if stakeholder.stakeholder_type else "UNKNOWN",
                        "role": stakeholder.role or "Stakeholder",
                        "organization": stakeholder.organization or "Unknown",
                        "confidenceScore": stakeholder.confidence_score or 0.8,
                        "sourceText": getattr(stakeholder.name_reference, 'source_text', f"Extracted: {stakeholder.name}") if hasattr(stakeholder, 'name_reference') and stakeholder.name_reference else f"Extracted: {stakeholder.name}"
                    }
                    stakeholders_data.append(stakeholder_dict)
                
                if stakeholders_data:
                    processed_stakeholders = process_llm_extraction_response(stakeholders_data)
                    if processed_stakeholders:
                        print(f"✅ StructuredExtractionAdapter successful: {len(processed_stakeholders)} stakeholders")
                        return processed_stakeholders
        
        except ImportError as e:
            print(f"⚠️ StructuredExtractionAdapter not available: {e}")
        except Exception as e:
            print(f"⚠️ StructuredExtractionAdapter error: {e}")
        
        # Try LocalLlamaClient directly as final fallback
        try:
            from app.llm.ai_agents.local_llama_client import LocalLlamaClient
            
            print("🦙 Using LocalLlamaClient directly...")
            
            client = LocalLlamaClient()
            result = client.extract_stakeholders_jsonld(
                document_content=document_content,
                document_title=source_filename,
                temperature=0.1
            )
            
            if result.get("success") and result.get("stakeholders"):
                stakeholders_data = []
                
                for stakeholder in result["stakeholders"]:
                    stakeholder_dict = {
                        "name": stakeholder.get('name', 'Unknown'),
                        "stakeholderType": stakeholder.get('stakeholderType', 'INDIVIDUAL'),
                        "role": stakeholder.get('role', 'Stakeholder'),
                        "organization": stakeholder.get('organization', 'Unknown'),
                        "confidenceScore": float(stakeholder.get('confidenceScore', 0.8)),
                        "sourceText": f"Local Llama extracted: {stakeholder.get('name')}"
                    }
                    stakeholders_data.append(stakeholder_dict)
                
                processed_stakeholders = process_llm_extraction_response(stakeholders_data)
                if processed_stakeholders:
                    print(f"✅ LocalLlamaClient successful: {len(processed_stakeholders)} stakeholders")
                    return processed_stakeholders
        
        except ImportError as e:
            print(f"⚠️ LocalLlamaClient not available: {e}")
        except Exception as e:
            print(f"⚠️ LocalLlamaClient error: {e}")
        
        print("⚠️ All LLM extraction methods failed")
        return []
        
    except Exception as e:
        print(f"❌ LLM extraction error: {e}")
        import traceback
        traceback.print_exc()
        return []

def parse_llm_text_response(response_text: str) -> List[Dict[str, Any]]:
    """Parse LLM text response to extract stakeholder information"""
    try:
        import re
        import json
        
        # Try to find JSON in the response
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            stakeholders_data = json.loads(json_str)
            return process_llm_extraction_response(stakeholders_data)
        
        # If no JSON, try to parse structured text
        stakeholders = []
        lines = response_text.split('\n')
        
        current_stakeholder = {}
        for line in lines:
            line = line.strip()
            if line.startswith('Name:'):
                if current_stakeholder:
                    stakeholders.append(current_stakeholder)
                current_stakeholder = {'name': line.replace('Name:', '').strip()}
            elif line.startswith('Type:'):
                current_stakeholder['stakeholderType'] = line.replace('Type:', '').strip().upper()
            elif line.startswith('Role:'):
                current_stakeholder['role'] = line.replace('Role:', '').strip()
            elif line.startswith('Organization:'):
                current_stakeholder['organization'] = line.replace('Organization:', '').strip()
        
        if current_stakeholder:
            stakeholders.append(current_stakeholder)
        
        return process_llm_extraction_response(stakeholders)
        
    except Exception as e:
        print(f"❌ Error parsing LLM text response: {e}")
        return []

def enhanced_pattern_extraction(document_content: str, source_filename: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Enhanced pattern-based extraction as fallback"""
    try:
        stakeholders = []
        
        # Enhanced patterns for better extraction
        import re
        
        patterns = {
            'person_titles': r'\b(?:Dr\.?|Mr\.?|Ms\.?|Mrs\.?|Prof\.?|Professor|Minister|CEO|Director|Manager|Chairman|President|Chief)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'organizations': r'\b([A-Z][A-Za-z\s&]+(?:Institute|University|Department|Ministry|Alliance|Corporation|Company|Ltd|Inc|Agency|Committee|Council|Association|Foundation|Society))\b',
            'emails': r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            'phone_numbers': r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        }
        
        # Extract using enhanced patterns
        titles_found = re.findall(patterns['person_titles'], document_content, re.IGNORECASE)
        orgs_found = re.findall(patterns['organizations'], document_content)
        emails_found = re.findall(patterns['emails'], document_content)
        phones_found = re.findall(patterns['phone_numbers'], document_content)
        
        print(f"🔍 Enhanced pattern matches:")
        print(f"  - {len(titles_found)} person titles")
        print(f"  - {len(orgs_found)} organizations")  
        print(f"  - {len(emails_found)} emails")
        print(f"  - {len(phones_found)} phone numbers")
        
        stakeholder_id = 1
        
        # Create stakeholders from person titles
        for i, name in enumerate(titles_found[:8]):  # Limit to 8
            if len(name.strip()) > 2:
                # Determine stakeholder type based on title
                stakeholder_type = "RESEARCHER" if any(title in document_content.lower() for title in ["dr.", "professor", "phd"]) else "PROFESSIONAL"
                
                # Find the full context around the name
                full_match_pattern = rf'\b(?:Dr\.?|Mr\.?|Ms\.?|Mrs\.?|Prof\.?|Professor|Minister|CEO|Director|Manager|Chairman|President|Chief)\s+{re.escape(name)}'
                title_match = re.search(full_match_pattern, document_content, re.IGNORECASE)
                full_name = title_match.group(0) if title_match else name
                
                stakeholder = {
                    "@type": "Stakeholder",
                    "@id": f"stakeholder_pattern_{stakeholder_id}_{name.lower().replace(' ', '_')}",
                    "name": full_name,
                    "stakeholderType": stakeholder_type,
                    "role": "Professional/Academic",
                    "confidenceScore": 0.7,
                    "extractionMethod": "enhanced-pattern-matching",
                    "sourceText": get_context_around_name(document_content, full_name, 200),
                    "organization": orgs_found[i % len(orgs_found)] if orgs_found else metadata.get('dcterms:publisher', 'Unknown Organization')
                }
                
                # Add contact information if available
                if emails_found and i < len(emails_found):
                    stakeholder["contact"] = emails_found[i]
                elif phones_found and i < len(phones_found):
                    phone_parts = phones_found[i]
                    if isinstance(phone_parts, tuple) and len(phone_parts) == 3:
                        stakeholder["contact"] = f"({phone_parts[0]}) {phone_parts[1]}-{phone_parts[2]}"
                
                stakeholders.append(stakeholder)
                stakeholder_id += 1
        
        # Add organizations as stakeholders
        for i, org in enumerate(orgs_found[:5]):
            if len(org.strip()) > 8:  # Filter out very short matches
                stakeholder = {
                    "@type": "Stakeholder",
                    "@id": f"stakeholder_org_{stakeholder_id}_{org.lower().replace(' ', '_').replace('&', 'and')}",
                    "name": org.strip(),
                    "stakeholderType": "ORGANIZATION",
                    "role": "Institutional Stakeholder",
                    "confidenceScore": 0.6,
                    "extractionMethod": "enhanced-pattern-matching",
                    "sourceText": get_context_around_name(document_content, org, 200),
                    "organization": org.strip()
                }
                
                # Try to associate email with organization
                for email in emails_found:
                    if any(word in email.lower() for word in org.lower().split() if len(word) > 3):
                        stakeholder["contact"] = email
                        break
                
                stakeholders.append(stakeholder)
                stakeholder_id += 1
        
        print(f"🎯 Enhanced pattern extraction: {len(stakeholders)} stakeholders")
        return stakeholders
        
    except Exception as e:
        print(f"❌ Error in enhanced pattern extraction: {e}")
        return []

def create_stakeholder_extraction_prompt(document_content: str, filename: str) -> str:
    """Create a detailed prompt for LLM stakeholder extraction"""
    
    # Truncate content if too long (LLMs have token limits)
    max_content_length = 4000
    if len(document_content) > max_content_length:
        content_preview = document_content[:max_content_length] + "...[truncated]"
    else:
        content_preview = document_content
    
    prompt = f"""
You are an expert stakeholder analyst. Extract all stakeholders from the following document.

DOCUMENT: {filename}

CONTENT:
{content_preview}

TASK: Identify and extract stakeholders from this document. For each stakeholder, provide:
- Name (person, organization, or entity)
- Type (INDIVIDUAL, ORGANIZATION, GOVERNMENT, COMMUNITY, etc.)
- Role or relationship to the document
- Any contact information if mentioned
- Confidence score (0.0-1.0) for how certain you are this is a stakeholder

OUTPUT FORMAT: Return a JSON array of stakeholder objects like this:
[
  {{
    "name": "Dr. Jane Smith",
    "stakeholderType": "INDIVIDUAL",
    "role": "Research Director",
    "organization": "University of Example",
    "contact": "jane.smith@example.edu",
    "confidenceScore": 0.9,
    "sourceText": "Dr. Jane Smith, Research Director at University of Example"
  }}
]

IMPORTANT:
- Only extract actual stakeholders (people, organizations involved)
- Ignore generic terms like "users", "customers" unless specifically named
- Include confidence scores based on how explicit the mention is
- Extract contact information when available
- Be thorough but accurate

STAKEHOLDERS:
"""
    
    return prompt

def process_llm_extraction_response(llm_stakeholders) -> List[Dict[str, Any]]:
    """Process and validate LLM extraction response"""
    processed_stakeholders = []
    
    try:
        if isinstance(llm_stakeholders, str):
            # Try to parse JSON if it's a string
            import json
            llm_stakeholders = json.loads(llm_stakeholders)
        
        if not isinstance(llm_stakeholders, list):
            print("⚠️ LLM response is not a list, wrapping it")
            llm_stakeholders = [llm_stakeholders] if llm_stakeholders else []
        
        stakeholder_id = 1
        for stakeholder_data in llm_stakeholders:
            if isinstance(stakeholder_data, dict) and 'name' in stakeholder_data:
                
                # Create properly formatted stakeholder
                processed_stakeholder = {
                    "@type": "Stakeholder",
                    "@id": f"stakeholder_llm_{stakeholder_id}_{stakeholder_data['name'].lower().replace(' ', '_')}",
                    "name": stakeholder_data.get('name', 'Unknown'),
                    "stakeholderType": stakeholder_data.get('stakeholderType', 'UNKNOWN'),
                    "role": stakeholder_data.get('role', 'Stakeholder'),
                    "confidenceScore": float(stakeholder_data.get('confidenceScore', 0.8)),
                    "extractionMethod": "llm-based",
                    "sourceText": stakeholder_data.get('sourceText', f"LLM identified: {stakeholder_data.get('name')}"),
                    "organization": stakeholder_data.get('organization', 'Unknown')
                }
                
                # Add contact if available
                if 'contact' in stakeholder_data:
                    processed_stakeholder['contact'] = stakeholder_data['contact']
                
                processed_stakeholders.append(processed_stakeholder)
                stakeholder_id += 1
                
    except Exception as e:
        print(f"❌ Error processing LLM response: {e}")
        print(f"Raw LLM response: {llm_stakeholders}")
    
    return processed_stakeholders

def create_placeholder_stakeholder(source_filename: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create a placeholder stakeholder when no extraction is possible"""
    return [{
        "@type": "Stakeholder", 
        "@id": "stakeholder_placeholder",
        "name": "Document Author/Publisher",
        "stakeholderType": "INDIVIDUAL",
        "role": "Content Creator",
        "confidenceScore": 0.4,
        "extractionMethod": "placeholder",
        "sourceText": f"Placeholder for document {source_filename} - content extraction methods not available",
        "organization": metadata.get('dcterms:publisher', metadata.get('publisher', 'Unknown Publisher'))
    }]

def create_extraction_result(stakeholders: List[Dict[str, Any]], source_filename: str, 
                           metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Create properly formatted extraction result"""
    
    # Generate URIs (fallback implementation without app context)
    safe_name = source_filename.replace('.', '_').replace(' ', '_').replace('-', '_')
    doc_uri = f"https://docex.org/vocab/document/{safe_name}"
    analysis_uri = f"{doc_uri}/analysis"
    
    extraction_result = {
        "@context": {
            "@vocab": "https://docex.org/vocab/",
            "name": "http://schema.org/name",
            "email": "http://schema.org/email",
            "Stakeholder": "http://schema.org/Person",
            "Organization": "http://schema.org/Organization",
            "ReviewAction": "https://docex.org/vocab/ReviewAction"
        },
        "@type": "StakeholderExtraction",
        "@id": analysis_uri,
        "analyzedDocument": doc_uri,
        "extractionMetadata": {
            "@type": "ExtractionMetadata",
            "sourceDocument": source_filename,
            "extractionStrategy": "hybrid-extraction",
            "agentModel": "DocEX Hybrid Extractor v1.0",
            "processingTime": 1.0,
            "extractionConfidence": 0.75,
            "qualityScore": 0.8,
            "extractionTimestamp": datetime.now().isoformat(),
            "basedOnMetadata": True,
            "extractorAgent": {
                "@type": "SoftwareAgent",
                "@id": "https://docex.org/vocab/agent/hybrid_extractor",
                "name": "DocEX Hybrid Stakeholder Extractor",
                "version": "1.0.0"
            }
        },
        "stakeholders": stakeholders,
        "extractionSummary": {
            "@type": "ExtractionSummary",
            "totalStakeholders": len(stakeholders),
            "averageConfidence": sum(s.get("confidenceScore", 0) for s in stakeholders) / len(stakeholders) if stakeholders else 0,
            "stakeholderTypes": list(set(s.get("stakeholderType", "UNKNOWN") for s in stakeholders)),
            "extractionMethod": stakeholders[0].get("extractionMethod", "unknown") if stakeholders else "none",
            "documentProcessed": True
        },
        "reviewHistory": []  # Ready for provenance tracking
    }
    
    return extraction_result

def generate_error_result(filename: str, error_message: str) -> Dict[str, Any]:
    """Generate error result when extraction fails"""
    safe_name = filename.replace('.', '_').replace(' ', '_')
    return {
        "@context": {"@vocab": "https://docex.org/vocab/"},
        "@type": "ExtractionError",
        "@id": f"https://docex.org/vocab/extraction/error_{safe_name}",
        "sourceDocument": filename,
        "errorMessage": error_message,
        "extractionTimestamp": datetime.now().isoformat(),
        "stakeholders": [],
        "extractionSummary": {
            "totalStakeholders": 0,
            "error": True,
            "errorDetails": error_message
        }
    }

# Main extraction function with app context compatibility
def extract_stakeholders_enhanced(filename: str, jsonld_dir: str = None) -> Dict[str, Any]:
    """
    Enhanced stakeholder extraction from JSON-LD metadata
    This is the main entry point for the extraction process
    """
    print(f"🚀 Starting enhanced stakeholder extraction for: {filename}")
    return extract_stakeholders_from_jsonld_metadata(filename, jsonld_dir)

# Alias for backward compatibility
def extract_stakeholders_from_metadata(filename: str, jsonld_dir: str = None) -> Dict[str, Any]:
    """Backward compatibility alias"""
    return extract_stakeholders_enhanced(filename, jsonld_dir)