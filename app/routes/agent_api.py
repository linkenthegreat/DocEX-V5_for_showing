"""
Agent API Routes for Enhanced RDF Manager
Handles real extraction requests with multi-model AI agents
"""

print("🔍 Loading agent_api.py...")

from flask import Blueprint, jsonify, request, current_app, send_file
import os
import json
import time
import hashlib
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import traceback

# Import from extraction_utils instead of defining locally
from app.utils.extraction_utils import (
    ExtractionJob, extraction_jobs, job_counter,
    get_estimated_duration, get_model_for_priority,
    calculate_success_rate, calculate_avg_processing_time,
    run_extraction_job, calculate_extraction_cost
)
from app.utils.model_utils import (
    check_model_availability, get_recommended_priority, find_source_file
)

print("✅ All imports successful for agent_api.py")

# Create blueprint with proper configuration
agent_api_bp = Blueprint('agent_api', __name__, url_prefix='/api/agent')

print(f"✅ Agent API blueprint created: {agent_api_bp.name}")

# Simple test route to verify the blueprint works
@agent_api_bp.route('/test')
def test_endpoint():
    """Simple test endpoint to verify API is working"""
    return jsonify({
        "status": "success",
        "message": "Agent API is working!",
        "timestamp": datetime.now().isoformat()
    })

@agent_api_bp.route('/status')
def get_agent_status():
    """Get current agent system status"""
    try:
        model_status = check_model_availability()
        available_count = sum(1 for status in model_status.values() if status)
        system_status = "ready" if available_count > 0 else "error"
        
        return jsonify({
            "status": system_status,
            "model_availability": model_status,
            "available_models_count": available_count,
            "performance": {
                "total_extractions": len([j for j in extraction_jobs.values() if j.status == 'complete']),
                "success_rate": calculate_success_rate(),
                "avg_processing_time": calculate_avg_processing_time(),
                "active_jobs": len([j for j in extraction_jobs.values() if j.status in ['pending', 'running']])
            },
            "recommended_priority": get_recommended_priority(model_status),
            "cost_estimates": {
                "cost": {"model": "Local Llama 3.1 8B", "cost_per_doc": 0.0},
                "quality": {"model": "GPT-4o", "cost_per_doc": 0.008},
                "speed": {"model": "DeepSeek-V3", "cost_per_doc": 0.002},
                "privacy": {"model": "Local Llama 3.1 8B", "cost_per_doc": 0.0}
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting agent status: {e}")
        return jsonify({
            "status": "error", 
            "error": str(e),
            "model_availability": {},
            "available_models_count": 0
        }), 500

@agent_api_bp.route('/extract', methods=['POST'])
def start_extraction():
    """Start a new extraction job"""
    try:
        print("🚀 Extract endpoint called")
        
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        filename = data.get('filename')
        priority = data.get('priority', 'cost')
        use_context = data.get('use_context', True)
        detailed_output = data.get('detailed_output', True)
        
        if not filename:
            return jsonify({"error": "Filename is required"}), 400
        
        # Get app context configuration before starting background thread
        jsonld_dir = current_app.config.get('JSONLD_DIR')
        if not jsonld_dir:
            app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
            jsonld_dir = os.path.join(app_dir, '..', 'database', 'jsonld')
        
        # Create extraction job using the imported utilities
        import app.utils.extraction_utils as eu
        eu.job_counter += 1
        job_id = f"extract_{eu.job_counter}_{int(time.time())}"
        
        print(f"🔍 Creating job with ID: {job_id}")
        
        job = ExtractionJob(
            job_id=job_id,
            filename=filename,
            priority=priority,
            options={
                'use_context': use_context,
                'detailed_output': detailed_output,
                'jsonld_dir': jsonld_dir  # Pass directory to avoid app context issues
            }
        )
        
        eu.extraction_jobs[job_id] = job
        print(f"✅ Job created and stored: {job_id}")
        print(f"📊 Total jobs in storage: {len(eu.extraction_jobs)}")
        
        # Start extraction in background thread
        try:
            executor = ThreadPoolExecutor(max_workers=1)
            executor.submit(run_extraction_job, job)
            print(f"✅ Background job started for: {job_id}")
        except Exception as bg_error:
            print(f"❌ Error starting background job: {bg_error}")
            return jsonify({"error": f"Failed to start background job: {str(bg_error)}"}), 500
        
        return jsonify({
            "job_id": job_id,
            "status": "started",
            "estimated_duration": get_estimated_duration(priority),
            "model": get_model_for_priority(priority),
            "message": "Extraction job started successfully"
        })
        
    except Exception as e:
        print(f"❌ Error in start_extraction: {e}")
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@agent_api_bp.route('/extract/<job_id>/status')
def get_extraction_status(job_id):
    """Get status of a specific extraction job"""
    try:
        print(f"🔍 Looking for job: {job_id}")
        print(f"📊 Available jobs in memory: {list(extraction_jobs.keys())}")
        
        # First check in-memory jobs
        job = extraction_jobs.get(job_id)
        
        # If not in memory, check persistent storage
        if not job:
            print(f"🔍 Job not in memory, checking persistent storage...")
            from app.utils.persistent_jobs import persistent_job_manager
            job_data = persistent_job_manager.load_job(job_id)
            
            if job_data:
                print(f"✅ Job found in persistent storage")
                # Recreate job object and add to memory
                from app.utils.extraction_utils import ExtractionJob
                job = ExtractionJob(
                    job_id=job_data['job_id'],
                    filename=job_data['filename'],
                    priority=job_data['priority'],
                    options=job_data['options']
                )
                
                # Restore state
                job.status = job_data.get('status', 'pending')
                job.progress = job_data.get('progress', 0)
                job.current_step = job_data.get('current_step', 'Initializing...')
                job.substep = job_data.get('substep', '')
                job.start_time = job_data.get('start_time', time.time())
                job.model_used = job_data.get('model_used')
                job.cost_estimate = job_data.get('cost_estimate', 0.0)
                job.results = job_data.get('results')
                job.error = job_data.get('error')
                
                # Add back to memory
                extraction_jobs[job_id] = job
            else:
                print(f"❌ Job {job_id} not found in persistent storage either")
                return jsonify({"error": "Job not found"}), 404
        
        response = {
            "job_id": job_id,
            "status": job.status,
            "progress": job.progress,
            "current_step": job.current_step,
            "substep": job.substep,
            "elapsed_time": time.time() - job.start_time,
            "model_used": job.model_used,
            "cost_estimate": job.cost_estimate,
            "restored_from_persistence": job_id not in list(extraction_jobs.keys())[:1]  # Simple check
        }
        
        if job.status == 'complete' and job.results:
            response["results"] = job.results
        elif job.status == 'error' and job.error:
            response["error"] = job.error
            
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error getting extraction status: {e}")
        return jsonify({"error": str(e)}), 500

@agent_api_bp.route('/extract/<job_id>/results')
def get_extraction_results(job_id):
    """Get detailed results of a completed extraction job"""
    try:
        job = extraction_jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        if job.status != 'complete':
            return jsonify({"error": "Job not completed"}), 400
        
        return jsonify({
            "job_id": job_id,
            "filename": job.filename,
            "results": job.results,
            "metadata": {
                "priority": job.priority,
                "model_used": job.model_used,
                "processing_time": time.time() - job.start_time,
                "cost_estimate": job.cost_estimate,
                "extraction_timestamp": datetime.fromtimestamp(job.start_time).isoformat()
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting extraction results: {e}")
        return jsonify({"error": str(e)}), 500

def save_extraction_results(job):
    """Save extraction results to JSON-LD file, preserving existing document metadata"""
    try:
        if not job.results or not job.results.get('stakeholders'):
            raise ValueError("No extraction results to save")
        
        # Get JSON-LD directory
        jsonld_dir = current_app.config.get('JSONLD_DIR')
        if not jsonld_dir:
            app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
            jsonld_dir = os.path.join(app_dir, '..', 'database', 'jsonld')
            jsonld_dir = os.path.abspath(jsonld_dir)
        
        # Ensure directory exists
        os.makedirs(jsonld_dir, exist_ok=True)
        
        # Generate filename - try to find existing document metadata first
        safe_filename = job.filename.replace(' ', '_').replace('/', '_').replace('\\', '_')
        if not safe_filename.endswith('.json'):
            safe_filename += '.json'
        
        output_path = os.path.join(jsonld_dir, safe_filename)
        
        # Try to load existing document metadata first
        existing_document = None
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_document = json.load(f)
                print(f"📄 Found existing document metadata: {safe_filename}")
            except Exception as e:
                print(f"⚠️ Error loading existing document: {e}")
        
        # If no existing document, try to find the source file and create metadata
        if not existing_document:
            print(f"🔍 No existing metadata found, creating from source file...")
            from app.utils.model_utils import find_source_file
            from app.utils.rdf_utils import create_jsonld_document_metadata, enhance_jsonld_with_structure
            from app.utils.file_utils import get_file_metadata
            
            # Find the actual source file
            source_file_path = find_source_file(job.filename)
            if source_file_path and os.path.exists(source_file_path):
                print(f"✅ Found source file: {source_file_path}")
                
                # Get file metadata
                file_metadata = get_file_metadata(source_file_path)
                
                # Create document metadata
                existing_document = create_jsonld_document_metadata(source_file_path, file_metadata)
                
                # Add document structure
                existing_document = enhance_jsonld_with_structure(existing_document, source_file_path)
                
                print(f"✅ Created comprehensive document metadata")
            else:
                print(f"⚠️ Source file not found, creating minimal metadata")
                # Create minimal document structure
                existing_document = {
                    "@context": {
                        "docex": "http://example.org/docex/",
                        "dcterms": "http://purl.org/dc/terms/",
                        "prov": "http://www.w3.org/ns/prov#",
                        "schema": "http://schema.org/"
                    },
                    "@id": f"docex:doc_{hashlib.md5(job.filename.encode()).hexdigest()[:12]}",
                    "@type": "docex:Document",
                    "dcterms:title": job.filename,
                    "docex:filePath": job.filename,
                    "prov:generatedAtTime": datetime.now().isoformat()
                }
        
        # Now enhance the existing document with stakeholder extraction results
        
        # Merge contexts
        stakeholder_context = {
            "@vocab": "https://docex.org/vocab/",
            "stakeholder": "https://docex.org/vocab/stakeholder/",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "dcterms": "http://purl.org/dc/terms/"
        }
        
        # Update context
        if "@context" in existing_document:
            if isinstance(existing_document["@context"], dict):
                existing_document["@context"].update(stakeholder_context)
            else:
                existing_document["@context"] = [existing_document["@context"], stakeholder_context]
        else:
            existing_document["@context"] = stakeholder_context
        
        # Add extraction metadata as a separate entity
        extraction_metadata = {
            "@type": "StakeholderExtractionProcess",
            "@id": f"extraction:{job.job_id}",
            "dcterms:created": datetime.fromtimestamp(job.start_time).isoformat(),
            "extractionStrategy": job.results.get('extraction_metadata', {}).get('strategy', 'llm-based'),
            "agentModel": job.model_used or 'unknown',
            "processingTime": time.time() - job.start_time,
            "extractionConfidence": job.results.get('extraction_metadata', {}).get('confidence', 0.8),
            "qualityScore": job.results.get('extraction_metadata', {}).get('quality_score', 0.8),
            "costEstimate": job.cost_estimate,
            "extractionTimestamp": datetime.fromtimestamp(job.start_time).isoformat(),
            "priority": job.priority,
            "targetDocument": existing_document.get("@id"),
            "stakeholderCount": len(job.results.get('stakeholders', []))
        }
        
        # Add stakeholder extraction results to the document
        existing_document["stakeholderExtraction"] = extraction_metadata
        existing_document["extractedStakeholders"] = job.results.get('stakeholders', [])
        
        # Add processing provenance
        if "prov:wasGeneratedBy" not in existing_document:
            existing_document["prov:wasGeneratedBy"] = []
        elif not isinstance(existing_document["prov:wasGeneratedBy"], list):
            existing_document["prov:wasGeneratedBy"] = [existing_document["prov:wasGeneratedBy"]]
        
        existing_document["prov:wasGeneratedBy"].append({
            "@id": f"docex:StakeholderExtractionAgent",
            "@type": "prov:Agent",
            "schema:name": "DocEX AI Stakeholder Extraction Agent",
            "prov:actedOnBehalfOf": {
                "@id": "docex:DocEXSystem",
                "@type": "prov:Agent"
            }
        })
        
        # Update modification timestamp
        existing_document["dcterms:modified"] = datetime.now().isoformat()
        
        # Save the enhanced document
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(existing_document, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Enhanced extraction results saved to: {output_path}")
        print(f"📊 Document contains:")
        print(f"   - Original metadata: {'✅' if existing_document.get('docex:textContent') else '❌'}")
        print(f"   - Document structure: {'✅' if existing_document.get('docex:hasParagraph') else '❌'}")
        print(f"   - Stakeholder extraction: ✅ {len(job.results.get('stakeholders', []))} stakeholders")
        print(f"   - Extraction metadata: ✅")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error saving enhanced extraction results: {e}")
        import traceback
        traceback.print_exc()
        raise

# Add this helper function to create document metadata if source is found
def create_document_metadata_from_source(filename):
    """Create document metadata from source file if available"""
    try:
        from app.utils.model_utils import find_source_file
        from app.utils.rdf_utils import create_jsonld_document_metadata, enhance_jsonld_with_structure
        from app.utils.file_utils import get_file_metadata
        
        # Find the actual source file
        source_file_path = find_source_file(filename)
        if not source_file_path or not os.path.exists(source_file_path):
            return None
        
        print(f"✅ Creating metadata from source: {source_file_path}")
        
        # Get file metadata
        file_metadata = get_file_metadata(source_file_path)
        
        # Create document metadata
        jsonld_doc = create_jsonld_document_metadata(source_file_path, file_metadata)
        
        # Add document structure (paragraphs, sentences)
        jsonld_doc = enhance_jsonld_with_structure(jsonld_doc, source_file_path)
        
        return jsonld_doc
        
    except Exception as e:
        print(f"❌ Error creating document metadata: {e}")
        return None

@agent_api_bp.route('/extract/<job_id>/approve', methods=['POST'])
def approve_extraction(job_id):
    """Approve and save extraction results"""
    try:
        print(f"🔍 Approving extraction for job: {job_id}")
        
        job = extraction_jobs.get(job_id)
        if not job:
            # Try persistent storage
            from app.utils.persistent_jobs import persistent_job_manager
            job_data = persistent_job_manager.load_job(job_id)
            
            if job_data:
                # Recreate job object
                job = ExtractionJob(
                    job_id=job_data['job_id'],
                    filename=job_data['filename'],
                    priority=job_data['priority'],
                    options=job_data['options']
                )
                
                # Restore state
                job.status = job_data.get('status', 'pending')
                job.results = job_data.get('results')
                job.model_used = job_data.get('model_used')
                job.start_time = job_data.get('start_time', time.time())
                job.cost_estimate = job_data.get('cost_estimate', 0.0)
                
                extraction_jobs[job_id] = job
            else:
                return jsonify({"error": "Job not found"}), 404
        
        if job.status != 'complete':
            return jsonify({"error": f"Job not completed (status: {job.status})"}), 400
        
        if not job.results:
            return jsonify({"error": "No extraction results to approve"}), 400
        
        # Save results to JSON-LD file
        saved_path = save_extraction_results(job)
        
        # Also convert to TTL for compatibility
        try:
            convert_to_ttl(saved_path)
            print(f"✅ TTL conversion completed for {saved_path}")
        except Exception as ttl_error:
            print(f"⚠️ TTL conversion failed (but JSON-LD saved): {ttl_error}")
        
        return jsonify({
            "status": "approved",
            "saved_to": saved_path,
            "stakeholder_count": len(job.results.get('stakeholders', [])),
            "message": "Extraction results saved successfully"
        })
        
    except Exception as e:
        print(f"❌ Error approving extraction: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Approval error: {str(e)}"}), 500

def convert_to_ttl(jsonld_path):
    """Convert JSON-LD to TTL for compatibility"""
    try:
        from rdflib import Graph
        
        # Load JSON-LD
        g = Graph()
        g.parse(jsonld_path, format='json-ld')
        
        # Save as TTL
        ttl_path = jsonld_path.replace('.json', '.ttl').replace('jsonld', 'triples')
        
        # Ensure triples directory exists
        os.makedirs(os.path.dirname(ttl_path), exist_ok=True)
        
        g.serialize(destination=ttl_path, format='turtle')
        
        print(f"✅ TTL file created: {ttl_path}")
        return ttl_path
        
    except Exception as e:
        print(f"❌ TTL conversion error: {e}")
        raise

@agent_api_bp.route('/preview_jsonld/<path:filename>')
def preview_jsonld_file(filename):
    """Preview JSON-LD file content using existing preview.js format"""
    try:
        import urllib.parse
        import json
        
        # Decode the filename
        decoded_filename = urllib.parse.unquote(filename)
        print(f"🔍 Preview request for: '{decoded_filename}'")
        
        # Get JSON-LD directory from app config
        jsonld_dir = current_app.config.get('JSONLD_DIR')
        if not jsonld_dir:
            app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
            jsonld_dir = os.path.join(app_dir, '..', 'database', 'jsonld')
            jsonld_dir = os.path.abspath(jsonld_dir)
        
        # Build file path
        file_path = os.path.join(jsonld_dir, decoded_filename)
        print(f"🔍 Looking for file at: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return jsonify({"error": "File not found", "path": file_path}), 404
        
        # Load JSON-LD content
        with open(file_path, 'r', encoding='utf-8') as f:
            jsonld_data = json.load(f)
        
        # Extract stakeholders and metadata for your preview.js format
        stakeholders = jsonld_data.get('stakeholders', [])
        extraction_metadata = jsonld_data.get('extractionMetadata', {})
        
        # Generate turtle preview using your existing format
        turtle_preview = generate_turtle_preview_for_existing(jsonld_data, decoded_filename)
        
        # Format data to match your existing preview.js expectations
        preview_data = {
            "filename": decoded_filename,
            "format": "JSON-LD",
            "triple_count": estimate_triple_count(jsonld_data),
            "stakeholder_count": len(stakeholders),
            "has_metadata": bool(extraction_metadata),
            "stakeholders": stakeholders,  # Full stakeholder list for your system
            "metadata": extraction_metadata,  # Your extraction metadata
            "turtle_preview": turtle_preview,
            "jsonld_preview": json.dumps(jsonld_data, indent=2)
        }
        
        print(f"✅ Preview generated for {decoded_filename}: {len(stakeholders)} stakeholders")
        return jsonify(preview_data)
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error for {filename}: {e}")
        return jsonify({"error": f"Invalid JSON file: {str(e)}"}), 400
    except Exception as e:
        print(f"❌ Error previewing file {filename}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Preview error: {str(e)}"}), 500

def generate_turtle_preview_for_existing(jsonld_data, filename):
    """Generate comprehensive turtle preview including document structure"""
    turtle_lines = [
        "@prefix docex: <http://example.org/docex/> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix foaf: <http://xmlns.com/foaf/0.1/> .",
        "@prefix prov: <http://www.w3.org/ns/prov#> .",
        "",
        f"# Generated from: {filename}",
        f"# Timestamp: {datetime.now().isoformat()}",
        ""
    ]
    
    # Add document metadata
    doc_id = jsonld_data.get("@id", "docex:unknown")
    turtle_lines.extend([
        f"{doc_id} a docex:Document ;",
        f'    dcterms:title "{jsonld_data.get("dcterms:title", "Unknown")}" ;'
    ])
    
    if jsonld_data.get("dcterms:format"):
        turtle_lines.append(f'    dcterms:format "{jsonld_data["dcterms:format"]}" ;')
    
    if jsonld_data.get("docex:textContent"):
        content_preview = jsonld_data["docex:textContent"][:100] + "..." if len(jsonld_data["docex:textContent"]) > 100 else jsonld_data["docex:textContent"]
        turtle_lines.append(f'    docex:textContent "{content_preview}" ;')
    
    if jsonld_data.get("docex:paragraphCount"):
        turtle_lines.append(f'    docex:paragraphCount {jsonld_data["docex:paragraphCount"]} ;')
    
    if jsonld_data.get("docex:sentenceCount"):
        turtle_lines.append(f'    docex:sentenceCount {jsonld_data["docex:sentenceCount"]} ;')
    
    # Remove last semicolon and add period for document
    if turtle_lines[-1].endswith(" ;"):
        turtle_lines[-1] = turtle_lines[-1][:-2] + " ."
    
    turtle_lines.append("")
    
    # Add stakeholder triples (from extractedStakeholders or stakeholders)
    stakeholders = jsonld_data.get('extractedStakeholders', jsonld_data.get('stakeholders', []))
    if stakeholders:
        turtle_lines.append("# Extracted Stakeholders")
        for i, stakeholder in enumerate(stakeholders[:5]):  # Limit for preview
            stakeholder_id = f"stakeholder_{i+1}"
            turtle_lines.extend([
                f"docex:{stakeholder_id} a docex:Stakeholder ;",
                f'    rdfs:label "{stakeholder.get("name", "Unknown")}" ;',
                f'    docex:stakeholderType "{stakeholder.get("stakeholderType", "UNKNOWN")}" ;',
                f'    docex:role "{stakeholder.get("role", "")}" ;'
            ])
            
            if stakeholder.get("organization"):
                turtle_lines.append(f'    docex:organization "{stakeholder["organization"]}" ;')
            
            if stakeholder.get("confidenceScore"):
                turtle_lines.append(f'    docex:confidenceScore {stakeholder["confidenceScore"]} ;')
            
            # Remove last semicolon and add period
            if turtle_lines[-1].endswith(" ;"):
                turtle_lines[-1] = turtle_lines[-1][:-2] + " ."
            
            turtle_lines.append("")
    
    # Add extraction metadata
    extraction_meta = jsonld_data.get('stakeholderExtraction', {})
    if extraction_meta:
        turtle_lines.extend([
            "# Stakeholder Extraction Process",
            f'{extraction_meta.get("@id", "docex:extraction")} a docex:StakeholderExtractionProcess ;',
            f'    dcterms:created "{extraction_meta.get("dcterms:created", "")}" ;',
            f'    docex:agentModel "{extraction_meta.get("agentModel", "unknown")}" ;',
            f'    docex:stakeholderCount {extraction_meta.get("stakeholderCount", 0)} ;',
            f'    docex:qualityScore {extraction_meta.get("qualityScore", 0.0)} .',
            ""
        ])
    
    return "\n".join(turtle_lines)

def estimate_triple_count(jsonld_data):
    """Estimate comprehensive RDF triple count"""
    count = 0
    
    # Document metadata triples
    count += 5  # Basic document metadata
    
    # Document structure triples
    paragraphs = jsonld_data.get('docex:hasParagraph', [])
    for para in paragraphs:
        count += 4  # Paragraph metadata
        sentences = para.get('docex:hasSentence', [])
        count += len(sentences) * 3  # Sentence triples
    
    # Stakeholder triples
    stakeholders = jsonld_data.get('extractedStakeholders', jsonld_data.get('stakeholders', []))
    for stakeholder in stakeholders:
        count += 4  # Basic stakeholder triples
        if stakeholder.get('organization'):
            count += 1
        if stakeholder.get('confidenceScore'):
            count += 1
    
    # Extraction metadata triples
    if jsonld_data.get('stakeholderExtraction'):
        count += 6
    
    return count

@agent_api_bp.route('/load_jsonld/<path:filename>')
def load_jsonld_file(filename):
    """Load complete JSON-LD file for download"""
    try:
        import urllib.parse
        
        # Decode the filename
        decoded_filename = urllib.parse.unquote(filename)
        
        # Get JSON-LD directory
        jsonld_dir = current_app.config.get('JSONLD_DIR')
        if not jsonld_dir:
            app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
            jsonld_dir = os.path.join(app_dir, '..', 'database', 'jsonld')
            jsonld_dir = os.path.abspath(jsonld_dir)
        
        file_path = os.path.join(jsonld_dir, decoded_filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        # Return the file for download
        return send_file(file_path, 
                        as_attachment=True, 
                        download_name=decoded_filename,
                        mimetype='application/ld+json')
        
    except Exception as e:
        print(f"❌ Error loading JSON-LD file {filename}: {e}")
        return jsonify({"error": str(e)}), 500

@agent_api_bp.route('/debug')
def debug_agent_api():
    """Debug endpoint to check API status"""
    try:
        return jsonify({
            "status": "working",
            "message": "Agent API blueprint is properly registered",
            "available_routes": [
                "/api/agent/test",
                "/api/agent/debug", 
                "/api/agent/status",
                "/api/agent/extract"
            ],
            "current_jobs": len(extraction_jobs),
            "active_jobs": list(extraction_jobs.keys()),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@agent_api_bp.route('/preview_ttl/<path:filename>')
def preview_ttl_file(filename):
    """Preview TTL file content for UI display"""
    try:
        import urllib.parse
        
        # Decode the filename
        decoded_filename = urllib.parse.unquote(filename)
        print(f"🔍 TTL Preview request for: '{decoded_filename}'")
        
        # Get triples directory from app config
        triples_dir = current_app.config.get('TRIPLES_DIR')
        if not triples_dir:
            app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
            triples_dir = os.path.join(app_dir, '..', 'database', 'triples')
            triples_dir = os.path.abspath(triples_dir)
        
        # Build file path
        file_path = os.path.join(triples_dir, decoded_filename)
        print(f"🔍 Looking for TTL file at: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"❌ TTL file not found: {file_path}")
            return jsonify({"error": "TTL file not found", "path": file_path}), 404
        
        # Load TTL content
        with open(file_path, 'r', encoding='utf-8') as f:
            ttl_content = f.read()
        
        # Get file stats
        file_stats = os.stat(file_path)
        file_size = file_stats.st_size
        modified_time = datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        
        # Format file size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        # Count triples
        lines = ttl_content.split('\n')
        triple_count = len([line for line in lines 
                           if line.strip().endswith('.') and 
                           not line.strip().startswith('@') and
                           not line.strip().startswith('#')])
        
        # Count namespaces
        namespace_count = len([line for line in lines 
                              if line.strip().startswith('@prefix')])
        
        # Create preview data
        preview_data = {
            "filename": decoded_filename,
            "file_size": size_str,
            "modified": modified_time,
            "triple_count": triple_count,
            "namespace_count": namespace_count,
            "content_preview": ttl_content[:2000] + "..." if len(ttl_content) > 2000 else ttl_content,
            "full_content": ttl_content
        }
        
        print(f"✅ TTL Preview generated for {decoded_filename}: {triple_count} triples")
        return jsonify(preview_data)
        
    except Exception as e:
        print(f"❌ Error previewing TTL file {filename}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"TTL preview error: {str(e)}"}), 500

@agent_api_bp.route('/get_file_content/<path:filename>')
def get_file_content(filename):
    """Get full file content for modal display"""
    try:
        import urllib.parse
        import json
        
        # Decode the filename
        decoded_filename = urllib.parse.unquote(filename)
        print(f"🔍 Full content request for: '{decoded_filename}'")
        
        # Determine file type and directory
        if decoded_filename.endswith(('.json', '.jsonld')):
            # JSON-LD file
            jsonld_dir = current_app.config.get('JSONLD_DIR')
            if not jsonld_dir:
                app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
                jsonld_dir = os.path.join(app_dir, '..', 'database', 'jsonld')
                jsonld_dir = os.path.abspath(jsonld_dir)
            
            file_path = os.path.join(jsonld_dir, decoded_filename)
            
            if not os.path.exists(file_path):
                return jsonify({"error": "JSON-LD file not found"}), 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            return jsonify({
                "filename": decoded_filename,
                "content": json.dumps(content, indent=2, ensure_ascii=False),
                "content_type": "json",
                "stakeholder_count": len(content.get('stakeholders', [])) if isinstance(content, dict) else 0
            })
        
        elif decoded_filename.endswith('.ttl'):
            # TTL file
            triples_dir = current_app.config.get('TRIPLES_DIR')
            if not triples_dir:
                app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
                triples_dir = os.path.join(app_dir, '..', 'database', 'triples')
                triples_dir = os.path.abspath(triples_dir)
            
            file_path = os.path.join(triples_dir, decoded_filename)
            
            if not os.path.exists(file_path):
                return jsonify({"error": "TTL file not found"}), 404
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count triples
            lines = content.split('\n')
            triple_count = len([line for line in lines 
                               if line.strip().endswith('.') and 
                               not line.strip().startswith('@') and
                               not line.strip().startswith('#')])
            
            return jsonify({
                "filename": decoded_filename,
                "content": content,
                "content_type": "turtle",
                "triple_count": triple_count
            })
        
        else:
            return jsonify({"error": "Unsupported file type"}), 400
        
    except Exception as e:
        print(f"❌ Error getting file content for {filename}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Content retrieval error: {str(e)}"}), 500

@agent_api_bp.route('/extract/<job_id>/edit', methods=['GET', 'POST'])
def edit_extraction_results(job_id):
    """Get or update extraction results for editing"""
    try:
        job = extraction_jobs.get(job_id)
        
        if not job:
            # Try persistent storage
            from app.utils.persistent_jobs import persistent_job_manager
            job_data = persistent_job_manager.load_job(job_id)
            
            if job_data:
                # Recreate job object
                job = ExtractionJob(
                    job_id=job_data['job_id'],
                    filename=job_data['filename'],
                    priority=job_data['priority'],
                    options=job_data['options']
                )
                
                # Restore state
                job.status = job_data.get('status', 'pending')
                job.results = job_data.get('results')
                job.model_used = job_data.get('model_used')
                job.start_time = job_data.get('start_time', time.time())
                job.cost_estimate = job_data.get('cost_estimate', 0.0)
                
                extraction_jobs[job_id] = job
            else:
                return jsonify({"error": "Job not found"}), 404
        
        if request.method == 'GET':
            # Return current extraction results for editing
            if job.status != 'complete':
                return jsonify({"error": "Job not completed"}), 400
            
            return jsonify({
                "job_id": job_id,
                "filename": job.filename,
                "stakeholders": job.results.get('stakeholders', []) if job.results else [],
                "extraction_metadata": job.results.get('extraction_metadata', {}) if job.results else {},
                "editable": True
            })
        
        elif request.method == 'POST':
            # Update extraction results with edited data
            edited_data = request.get_json()
            
            if not edited_data:
                return jsonify({"error": "No edited data provided"}), 400
            
            # Update job results with edited stakeholders
            if not job.results:
                job.results = {}
            
            job.results['stakeholders'] = edited_data.get('stakeholders', [])
            
            # Save updated results to persistent storage
            job.save()
            
            return jsonify({
                "status": "updated",
                "message": "Extraction results updated successfully",
                "stakeholder_count": len(job.results.get('stakeholders', []))
            })
        
    except Exception as e:
        print(f"❌ Error in edit_extraction_results: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Edit error: {str(e)}"}), 500