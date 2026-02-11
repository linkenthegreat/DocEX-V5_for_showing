"""
Main Routing Blueprint

This module defines the primary routes for the DocEX application, handling
file navigation, document processing, RDF management, and user interaction.

Blueprint:
    main_bp: Blueprint containing all main application routes

Key Routes:
    /: Root directory display
    /level_up: Navigate up one directory level
    /navigate: Directory navigation
    /preview: File content preview
    /upload_files: Upload and process files for RDF conversion
    /manage_triples: Manage RDF triples
    /view_ttl: View TTL file content
    /view_ttl_page: View TTL file content on a separate page
    /remove_ttl: Remove a TTL file
    /combine_ttl_files: Combine selected TTL files
    /view_combined_graph: View the combined RDF graph
    /sparql_query: Execute SPARQL queries on the RDF graph
    /create_test_graph: Create a test RDF graph
    /delete_ttl_file: Delete a TTL file and update metadata

This module implements the web interface for interacting with the DocEX document
processing and RDF graph capabilities.
"""
import pydoc
import os
import csv
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from datetime import datetime
import mimetypes
from ..utils.file_utils import (calculate_file_hash, get_existing_records, 
                               save_records_to_csv, get_file_metadata, 
                               extract_file_content, SELECTED_FILE_INFO)
from ..utils.rdf_utils import (initialize_graph, create_file_metadata_graph, 
                              add_file_content, save_graph_to_ttl, 
                              load_graph_from_ttl, ttl_exists, get_all_ttl_files,
                              convert_to_rdf)
from ..extraction.adapters.context_enhanced_llm_adapter import ContextEnhancedLLMAdapter
from ..config.vector_config import VectorConfig
from app.extraction.adapters.enhanced_jsonld_bridge import extract_stakeholders_enhanced

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def root():
    """Display files in current directory"""
    items = os.listdir(os.getcwd())
    file_list = []
    
    for item in items:
        item_path = os.path.join(os.getcwd(), item)
        try:
            file_info = get_file_metadata(item_path)
            file_list.append(file_info)
        except Exception as e:
            # Skip files that cause errors
            current_app.logger.error(f"Error processing {item}: {str(e)}")
            
    return render_template('v3_testing.html', 
                         current_working_directory=os.getcwd(), 
                         file_list=file_list)

@main_bp.route('/level_up')
def level_up():
    """Navigate up one directory level"""
    os.chdir('..')
    return redirect(url_for('main.root'))

@main_bp.route('/navigate/<path:subfolder>')
def navigate(subfolder):
    """Navigate to a subdirectory"""
    os.chdir(subfolder)
    return redirect(url_for('main.root'))

@main_bp.route('/preview/<path:filename>')
def preview(filename):
    """Preview file content"""
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.isfile(file_path):
        try:
            # Generate a safe filename for TTL storage
            safe_name = f"{os.getcwd()}_{filename}".replace(' ', '_').replace('\\', '_').replace('/', '_')
            
            # Check if we already have a TTL file with content
            if ttl_exists(safe_name):
                g = load_graph_from_ttl(safe_name)
                if g:
                    query = """
                        SELECT ?content
                        WHERE {
                            ?file <http://www.w3.org/2011/content#chars> ?content .
                        }
                    """
                    results = g.query(query)
                    content = next(iter(results), [None])[0]
                    
                    if content:
                        return render_template('preview.html', content=content, filename=filename)
            
            # If no TTL or no content in TTL, extract content directly
            content = extract_file_content(file_path)
            return render_template('preview.html', content=content, filename=filename)
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
    return redirect(url_for('main.root'))

@main_bp.route('/upload_files', methods=['GET', 'POST'])
def upload_files():
    """Process selected files for RDF conversion"""
    from ..utils.file_utils import get_file_metadata, extract_file_content
    from ..utils.rdf_utils import convert_file_to_jsonld, save_jsonld_document, jsonld_to_rdf_graph, save_graph_to_ttl
    
    if request.method == 'GET':
        return render_template('upload.html')
    
    if request.method == 'POST':
        selected_files = request.form.getlist('selected_files')
        
        if not selected_files:
            flash('No files selected')
            return redirect(url_for('main.root'))
        
        existing_records = get_existing_records()
        new_records = []
        
        for filename in selected_files:
            try:
                # Get full path to the file
                file_path = os.path.join(os.getcwd(), filename)
                
                # Skip if file doesn't exist or is a directory
                if not os.path.isfile(file_path):
                    continue
                    
                # Get file metadata
                file_info = get_file_metadata(file_path)
                if not file_info:
                    continue
                
                # Add path to the metadata for RDF processing
                file_info['path'] = file_path
                
                # Extract content - needed for document structure
                file_info['content'] = extract_file_content(file_path)
                current_app.logger.info(f"Extracted content from {file_path}: {len(file_info.get('content', ''))} characters")
                
                # Convert to JSON-LD first (this includes document structure)
                current_app.logger.info(f"Converting {file_path} to JSON-LD")
                jsonld_doc = convert_file_to_jsonld(file_info)
                current_app.logger.info(f"Created JSON-LD document with {len(str(jsonld_doc))} characters")
                
                # Save JSON-LD document
                safe_name = f"{os.path.dirname(file_path).replace(':', '_')}__{os.path.basename(file_path)}"
                safe_name = safe_name.replace(' ', '_').replace('\\', '_').replace('/', '_').replace('.', '_')
                jsonld_path = save_jsonld_document(jsonld_doc, safe_name)
                current_app.logger.info(f"Saved JSON-LD to {jsonld_path}")
                
                # Convert JSON-LD to RDF graph
                current_app.logger.info(f"Converting JSON-LD to RDF graph")
                g = jsonld_to_rdf_graph(jsonld_doc)
                current_app.logger.info(f"Created RDF graph with {len(g)} triples")
                
                # Save as TTL file (for backward compatibility)
                ttl_path = save_graph_to_ttl(g, safe_name)
                current_app.logger.info(f"Saved TTL to {ttl_path}")
                
                # Add to records
                record_key = f"{file_info['directory']}/{file_info['name']}"
                existing_records[record_key] = {k: file_info[k] for k in SELECTED_FILE_INFO}
                new_records.append(file_info)
                
            except Exception as e:
                current_app.logger.error(f"Error processing {filename}: {str(e)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                flash(f"Error processing {filename}: {str(e)}")
                
        # Save updated records
        save_records_to_csv(list(existing_records.values()))
        
        flash(f'Successfully processed {len(new_records)} files')
        return redirect(url_for('main.root'))

@main_bp.route('/manage_triples')
def manage_triples():
    """Enhanced manage triples page with extraction interface"""
    try:
        # Use our enhanced function instead of the utils version
        ttl_files = get_ttl_files_info()
        return render_template('manage_triples_enhanced.html', ttl_files=ttl_files)
    except Exception as e:
        print(f"❌ Error in manage_triples: {e}")
        flash(f'Error loading RDF files: {str(e)}', 'error')
        return render_template('manage_triples_enhanced.html', ttl_files=[])

@main_bp.route('/view_ttl')
def view_ttl():
    """View the content of a TTL file"""
    from ..utils.rdf_utils import get_ttl_content
    
    filename = request.args.get('filename')
    if not filename:
        flash('No filename provided')
        return redirect(url_for('main.manage_triples'))
    
    content = get_ttl_content(filename)
    if content is None:
        flash(f'File {filename} not found')
        return redirect(url_for('main.manage_triples'))
    
    return content

@main_bp.route('/view_ttl_page')
def view_ttl_page():
    """Display TTL file content on a separate page"""
    filename = request.args.get('filename')
    if not filename:
        flash('No filename provided')
        return redirect(url_for('main.manage_triples'))
    
    from ..utils.rdf_utils import get_ttl_content
    content = get_ttl_content(filename)
    
    return render_template('view_ttl_content.html', 
                          filename=filename, 
                          content=content)

@main_bp.route('/remove_ttl', methods=['POST'])
def remove_ttl():
    """Remove TTL or JSON-LD files from database directories"""
    filename = request.form.get('filename')
    if not filename:
        flash('No filename provided', 'error')
        return redirect(url_for('main.manage_triples'))
    
    try:
        print(f"🔍 Delete request for filename: '{filename}'")
        
        # Use app config for directories
        triples_dir = current_app.config.get('TRIPLES_DIR')
        jsonld_dir = current_app.config.get('JSONLD_DIR')
        
        print(f"🔍 Using directories:")
        print(f"   - TTL: {triples_dir}")
        print(f"   - JSON-LD: {jsonld_dir}")
        
        files_removed = []
        
        # Check both directories for the file
        possible_paths = []
        
        if triples_dir and os.path.exists(triples_dir):
            ttl_path = os.path.join(triples_dir, filename)
            if os.path.exists(ttl_path):
                possible_paths.append(ttl_path)
        
        if jsonld_dir and os.path.exists(jsonld_dir):
            jsonld_path = os.path.join(jsonld_dir, filename)
            if os.path.exists(jsonld_path):
                possible_paths.append(jsonld_path)
        
        print(f"🔍 Found {len(possible_paths)} files to remove: {possible_paths}")
        
        for file_path in possible_paths:
            try:
                os.remove(file_path)
                files_removed.append(os.path.basename(file_path))
                print(f"✅ Successfully removed: {file_path}")
            except OSError as e:
                print(f"❌ Failed to remove {file_path}: {e}")
        
        if files_removed:
            flash(f'Successfully removed: {", ".join(files_removed)}', 'success')
        else:
            flash(f'No files found to remove for: {filename}', 'warning')
            
    except Exception as e:
        print(f"❌ Error in remove_ttl: {str(e)}")
        flash(f'Error removing file: {str(e)}', 'error')
    
    return redirect(url_for('main.manage_triples'))

@main_bp.route('/combine_ttl_files', methods=['POST'])
def combine_ttl_files():
    """Combine selected TTL files into a single graph"""
    selected_files = request.form.getlist('selected_ttls')
    print(f"Selected TTL files: {selected_files}")
    
    if not selected_files:
        flash('No files selected for combination', 'warning')
        return redirect(url_for('main.manage_triples'))
    
    try:
        # Use the correct triples directory
        app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
        triples_dir = os.path.join(app_dir, '..', 'database', 'triples')
        triples_dir = os.path.abspath(triples_dir)
        
        print(f"🔍 Using triples directory: {triples_dir}")
        
        if not os.path.exists(triples_dir):
            flash('Triples directory not found', 'error')
            return redirect(url_for('main.manage_triples'))
        
        combined_content = []
        namespaces = set()
        total_triples = 0
        
        for filename in selected_files:
            file_path = os.path.join(triples_dir, filename)
            print(f"🔍 Processing file: {file_path}")
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Extract namespaces (lines starting with @prefix)
                    lines = content.split('\n')
                    file_triples = []
                    
                    for line in lines:
                        line = line.strip()
                        if line.startswith('@prefix'):
                            namespaces.add(line)
                        elif line and not line.startswith('@') and not line.startswith('#'):
                            if line.endswith('.'):
                                file_triples.append(line)
                                total_triples += 1
                    
                    combined_content.extend(file_triples)
                    print(f"✅ Added {len(file_triples)} triples from {filename}")
                    
                except Exception as e:
                    print(f"❌ Error reading {filename}: {e}")
                    flash(f'Error reading {filename}: {str(e)}', 'error')
            else:
                print(f"⚠️ File not found: {file_path}")
                flash(f'File not found: {filename}', 'warning')
        
        if combined_content:
            # Create combined graph
            combined_graph = '\n'.join(sorted(namespaces)) + '\n\n'
            combined_graph += '\n'.join(combined_content)
            
            # Save to combined_graph.ttl in triples directory
            output_path = os.path.join(triples_dir, 'combined_graph.ttl')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(combined_graph)
            
            flash(f'Successfully combined {len(selected_files)} files into a graph with {total_triples} triples', 'success')
            print(f"✅ Combined graph saved to: {output_path}")
        else:
            flash('No valid content found in selected files', 'warning')
            
    except Exception as e:
        print(f"❌ Error in combine_ttl_files: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error combining files: {str(e)}', 'error')
    
    return redirect(url_for('main.manage_triples'))

@main_bp.route('/view_combined_graph')
def view_combined_graph():
    """View the combined graph"""
    triples_dir = current_app.config['TRIPLES_DIR']
    combined_path = os.path.join(triples_dir, "combined_graph.ttl")
    
    if not os.path.exists(combined_path):
        flash('Combined graph does not exist. Please combine TTL files first.')
        return redirect(url_for('main.manage_triples'))
    
    try:
        with open(combined_path, 'r') as f:
            content = f.read()
        return render_template('view_combined_graph.html', content=content)
    except Exception as e:
        flash(f'Error reading combined graph: {str(e)}')
        return redirect(url_for('main.manage_triples'))

@main_bp.route('/sparql_query', methods=['GET', 'POST'])
def sparql_query():
    """Run SPARQL query on the combined graph"""
    from ..utils.rdf_utils import execute_sparql_query
    
    query = None
    results = None
    result_headers = None
    error = None
    
    if request.method == 'POST':
        query = request.form.get('query', '')
        if query:
            try:
                current_app.logger.info(f"Processing SPARQL query: {query}")
                results, result_headers_or_error = execute_sparql_query(query)
                
                if results is None:
                    error = result_headers_or_error
                    current_app.logger.error(f"Query error: {error}")
                    flash(f"Query error: {error}")
                else:
                    result_headers = result_headers_or_error
                    current_app.logger.info(f"Query successful: {len(results)} results with headers {result_headers}")
                    
            except Exception as e:
                import traceback
                current_app.logger.error(f"Unexpected error in SPARQL query: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                error = f"Unexpected error: {str(e)}"
                flash(f"Query failed: {str(e)}")
    
    # Always check if combined graph exists and warn if not
    triples_dir = current_app.config['TRIPLES_DIR']
    combined_path = os.path.join(triples_dir, "combined_graph.ttl")
    combined_exists = os.path.exists(combined_path)
    
    if not combined_exists and not error:
        error = "No combined graph exists. Please combine TTL files first."
        flash(error)
    
    return render_template('sparql_query.html', 
                          query=query, 
                          results=results,
                          result_headers=result_headers,
                          error=error)

@main_bp.route('/create_test_graph')
def create_test_graph():
    """Create a test graph for SPARQL testing"""
    from ..utils.rdf_utils import create_test_graph
    
    try:
        test_path = create_test_graph()
        flash(f"Created test graph at {test_path}")
    except Exception as e:
        flash(f"Error creating test graph: {str(e)}")
    
    return redirect(url_for('main.manage_triples'))

@main_bp.route('/delete_ttl_file', methods=['POST'])
def delete_ttl_file():
    """Delete a TTL file and remove its corresponding metadata from the CSV"""
    from ..utils.rdf_utils import get_file_hash_from_ttl
    from ..utils.file_utils import SELECTED_FILE_INFO
    import csv
    
    filename = request.form.get('filename')
    
    if not filename:
        flash('No filename provided')
        return redirect(url_for('main.manage_triples'))
    
    file_path = os.path.join(current_app.config['TRIPLES_DIR'], filename)
    
    if not os.path.exists(file_path):
        flash(f'File not found: {filename}')
        return redirect(url_for('main.manage_triples'))
        
    try:
        # 1. Extract the hash before deleting the file
        file_hash = get_file_hash_from_ttl(filename)
        current_app.logger.info(f"Extracted hash from TTL file: {file_hash}")
        
        # 2. Delete the TTL file
        os.remove(file_path)
        current_app.logger.info(f"Deleted TTL file: {filename}")
        
        # 3. Update metadata CSV using the hash
        if file_hash:
            csv_path = current_app.config['CSV_FILE']
            
            if os.path.exists(csv_path):
                # Read existing records
                records = []
                removed = False
                
                with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        # Keep records that don't match our hash
                        if row.get('file_hash') != file_hash:
                            records.append(row)
                        else:
                            removed = True
                            current_app.logger.info(f"Removing CSV record with hash: {file_hash}, filename: {row.get('name')}")
                
                # Write back the filtered records
                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=SELECTED_FILE_INFO)
                    writer.writeheader()
                    writer.writerows(records)
                
                if removed:
                    flash(f'Successfully deleted {filename} and removed matching metadata')
                else:
                    flash(f'Deleted {filename}, but no matching metadata was found in CSV')
            else:
                flash(f'Deleted {filename}, but metadata CSV was not found')
        else:
            flash(f'Deleted {filename}, but could not extract hash for metadata removal')
            
    except Exception as e:
        current_app.logger.error(f"Error deleting {filename}: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash(f'Error deleting {filename}: {str(e)}')
    
    return redirect(url_for('main.manage_triples'))

# Create aliases for backward compatibility
@main_bp.route('/delete_triple', methods=['POST'])
def delete_triple():
    """Alias for delete_ttl_file"""
    return delete_ttl_file()

def get_existing_records():
    """Get existing records from the CSV file"""
    csv_path = current_app.config['CSV_FILE']
    records = {}
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                key = f"{row['directory']}/{row['name']}"
                records[key] = row
                
    return records

def save_records_to_csv(records):
    """Save records to the CSV file"""
    from ..utils.file_utils import SELECTED_FILE_INFO
    
    csv_path = current_app.config['CSV_FILE']
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=SELECTED_FILE_INFO)
        writer.writeheader()
        writer.writerows(records)

@main_bp.route('/api/agent/status')
def agent_status_api():
    """Basic agent status endpoint for UI integration"""
    try:
        # For now, return a simple mock status
        # This will be replaced with real agent integration in the next step
        return jsonify({
            "status": "ready",
            "model_availability": {
                "gpt4o": True,
                "deepseek": True,
                "llama": False  # Assume local model not running for now
            },
            "available_models_count": 2,
            "performance": {
                "total_extractions": 0,
                "success_rate": 1.0,
                "avg_processing_time": 120
            },
            "recommended_priority": "cost"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "error": str(e),
            "model_availability": {},
            "available_models_count": 0
        }), 500

def get_ttl_files_info():
    """Get information about TTL and JSON-LD files from database directories"""
    try:
        # Use Flask app config for directory paths
        triples_dir = current_app.config.get('TRIPLES_DIR')
        jsonld_dir = current_app.config.get('JSONLD_DIR')
        
        print(f"🔍 Looking for files in:")
        print(f"   - TTL: {triples_dir}")
        print(f"   - JSON-LD: {jsonld_dir}")
        
        files_info = []
        
        # Process TTL files from database/triples
        if os.path.exists(triples_dir):
            all_files = os.listdir(triples_dir)
            ttl_files = [f for f in all_files if f.endswith('.ttl') and not f.startswith('.')]
            print(f"🔍 TTL files found: {ttl_files}")
            
            for filename in ttl_files:
                file_path = os.path.join(triples_dir, filename)
                file_info = process_file_info(file_path, filename, 'TTL', 'triples')
                if file_info:
                    files_info.append(file_info)
        else:
            print(f"⚠️ TTL directory not found: {triples_dir}")
        
        # Process JSON-LD files from database/jsonld
        if os.path.exists(jsonld_dir):
            all_files = os.listdir(jsonld_dir)
            jsonld_files = [f for f in all_files if f.endswith(('.json', '.jsonld')) and not f.startswith('.')]
            print(f"🔍 JSON-LD files found: {jsonld_files}")
            
            for filename in jsonld_files:
                file_path = os.path.join(jsonld_dir, filename)
                file_info = process_file_info(file_path, filename, 'JSON-LD', 'jsonld')
                if file_info:
                    files_info.append(file_info)
        else:
            print(f"⚠️ JSON-LD directory not found: {jsonld_dir}")
        
        # Sort files by modification time (newest first)
        files_info.sort(key=lambda x: x.get('modified', ''), reverse=True)
        
        print(f"✅ Successfully processed {len(files_info)} total files")
        return files_info
        
    except Exception as e:
        print(f"❌ Error in get_ttl_files_info: {e}")
        import traceback
        traceback.print_exc()
        return []

def process_file_info(file_path, filename, file_type, directory_type):
    """Process individual file information"""
    try:
        print(f"🔍 Processing {file_type} file: '{filename}'")
        
        # Get file statistics
        stat_info = os.stat(file_path)
        file_size = stat_info.st_size
        modified_time = stat_info.st_mtime
        
        # Format file size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        # Format modification time
        from datetime import datetime
        modified_str = datetime.fromtimestamp(modified_time).strftime("%Y-%m-%d %H:%M")
        
        # Count triples/entities based on file type
        triples_count = 0
        extraction_status = 'pending'
        agent_model = None
        quality_score = 0.0
        stakeholder_count = 0
        
        try:
            if file_type == 'TTL':
                # Count triples in TTL files
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple triple counting (lines ending with .)
                    lines = content.split('\n')
                    triples_count = len([line for line in lines 
                                       if line.strip().endswith('.') and 
                                       not line.strip().startswith('@') and
                                       not line.strip().startswith('#')])
                extraction_status = 'complete'  # TTL files are already processed
            
            elif file_type == 'JSON-LD':
                # Handle JSON-LD files
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Count entities/stakeholders in JSON-LD
                if isinstance(data, dict):
                    # Check for stakeholders or entities
                    if 'stakeholders' in data:
                        stakeholder_count = len(data['stakeholders'])
                        triples_count = stakeholder_count * 5  # Approximate triples per stakeholder
                        extraction_status = 'complete'
                        
                        # Extract agent metadata if available
                        metadata = data.get('metadata', {})
                        agent_model = metadata.get('agent_model', 'Unknown')
                        quality_score = metadata.get('quality_score', 0.8)  # Default score
                        
                    elif '@graph' in data:
                        # Standard JSON-LD format
                        graph = data['@graph']
                        if isinstance(graph, list):
                            triples_count = len(graph)
                        else:
                            triples_count = 1
                        extraction_status = 'complete'
                    else:
                        # Single entity or other structure
                        triples_count = 1
                        extraction_status = 'complete'
                elif isinstance(data, list):
                    triples_count = len(data)
                    extraction_status = 'complete'
                    
        except Exception as content_error:
            print(f"⚠️ Could not analyze content of {filename}: {content_error}")
            triples_count = 0
            extraction_status = 'error'
        
        file_info = {
            'filename': filename,
            'size': size_str,
            'modified': modified_str,
            'triples': triples_count,
            'extraction_status': extraction_status,
            'agent_model': agent_model,
            'quality_score': quality_score,
            'quality_level': 'high' if quality_score > 0.8 else 'medium' if quality_score > 0.6 else 'low',
            'stakeholder_count': stakeholder_count,
            'user_reviewed': False,
            'file_type': file_type,
            'directory_type': directory_type
        }
        
        print(f"✅ File info created for: {filename} ({triples_count} triples, {extraction_status})")
        return file_info
        
    except OSError as e:
        print(f"❌ Error reading file {filename}: {e}")
        return None

@main_bp.route('/view_jsonld_page')
def view_jsonld_page():
    """Enhanced view page for JSON-LD files"""
    filename = request.args.get('filename')
    if not filename:
        flash('No filename provided', 'error')
        return redirect(url_for('main.manage_triples'))
    
    try:
        # Get JSON-LD directory
        jsonld_dir = current_app.config.get('JSONLD_DIR')
        if not jsonld_dir:
            app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
            jsonld_dir = os.path.join(app_dir, '..', 'database', 'jsonld')
        
        file_path = os.path.join(jsonld_dir, filename)
        
        if not os.path.exists(file_path):
            flash(f'File not found: {filename}', 'error')
            return redirect(url_for('main.manage_triples'))
        
        # Load JSON-LD content
        with open(file_path, 'r', encoding='utf-8') as f:
            jsonld_data = json.load(f)
        
        # Extract information for display
        stakeholders = jsonld_data.get('stakeholders', [])
        metadata = jsonld_data.get('metadata', {})
        
        # Try to convert to RDF for turtle display
        try:
            from rdflib import Graph
            g = Graph()
            jsonld_str = json.dumps(jsonld_data)
            g.parse(data=jsonld_str, format="json-ld")
            turtle_content = g.serialize(format="turtle")
            triple_count = len(g)
        except Exception as e:
            print(f"⚠️ RDF conversion failed: {e}")
            turtle_content = "RDF conversion not available"
            triple_count = "Unknown"
        
        return render_template('view_jsonld_content.html',
                             filename=filename,
                             file_type='JSON-LD',
                             content=turtle_content,
                             jsonld_content=json.dumps(jsonld_data, indent=2),
                             triple_count=triple_count,
                             stakeholder_count=len(stakeholders),
                             stakeholders=stakeholders[:5],  # First 5 for display
                             has_stakeholders=len(stakeholders) > 0,
                             metadata=metadata if metadata else None)
        
    except Exception as e:
        print(f"❌ Error viewing JSON-LD file: {e}")
        flash(f'Error loading file: {str(e)}', 'error')
        return redirect(url_for('main.manage_triples'))

# Keep your existing preview route but rename to avoid conflicts
@main_bp.route('/preview_legacy/<path:filename>')  # Renamed from /preview/<path:filename>
def preview_legacy(filename):
    """Legacy preview route for TTL files"""
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.isfile(file_path):
        try:
            # Your existing logic here...
            content = extract_file_content(file_path)
            return render_template('preview.html', content=content, filename=filename)
        except Exception as e:
            return f"Error reading file: {str(e)}"
    return redirect(url_for('main.root'))

# Add a proper TTL view route
@main_bp.route('/view_ttl_content')
def view_ttl_content():
    """View TTL file content with proper formatting"""
    filename = request.args.get('filename')
    if not filename:
        return redirect(url_for('main.manage_triples'))
    
    try:
        # Get the TTL file path
        triples_dir = current_app.config.get('TRIPLES_DIR')
        if not triples_dir:
            app_dir = current_app.config.get('APP_DIR', os.path.dirname(os.path.abspath(__file__)))
            triples_dir = os.path.join(app_dir, '..', 'database', 'triples')
            triples_dir = os.path.abspath(triples_dir)
        
        file_path = os.path.join(triples_dir, filename)
        
        if not os.path.exists(file_path):
            flash(f'TTL file not found: {filename}', 'error')
            return redirect(url_for('main.manage_triples'))
        
        # Read TTL content
        with open(file_path, 'r', encoding='utf-8') as f:
            ttl_content = f.read()
        
        # Count triples and namespaces
        lines = ttl_content.split('\n')
        triple_count = len([line for line in lines 
                           if line.strip().endswith('.') and 
                           not line.strip().startswith('@') and
                           not line.strip().startswith('#')])
        
        namespace_count = len([line for line in lines 
                              if line.strip().startswith('@prefix')])
        
        # Get file stats
        file_stats = os.stat(file_path)
        file_size = file_stats.st_size
        
        # Format file size
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        # Render with your existing template style
        return render_template('view_ttl_content.html',
                             filename=filename,
                             content=ttl_content,
                             file_type='Turtle (TTL)',
                             triple_count=triple_count,
                             namespace_count=namespace_count,
                             file_size=size_str,
                             has_content=bool(ttl_content.strip()))
        
    except Exception as e:
        flash(f'Error viewing TTL file: {str(e)}', 'error')
        return redirect(url_for('main.manage_triples'))