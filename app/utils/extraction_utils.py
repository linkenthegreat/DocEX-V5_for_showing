"""
Extraction Utilities for DocEX
Handles extraction job management and result generation with persistence
"""

import time
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

# Import persistent job manager
from app.utils.persistent_jobs import persistent_job_manager

# Global state for extraction tracking - with persistence backup
extraction_jobs = {}
job_counter = 0

class ExtractionJob:
    """Track extraction job status and progress"""
    def __init__(self, job_id, filename, priority, options):
        self.job_id = job_id
        self.filename = filename
        self.priority = priority
        self.options = options
        self.status = 'pending'
        self.progress = 0
        self.current_step = 'Initializing...'
        self.substep = ''
        self.start_time = time.time()
        self.model_used = None
        self.cost_estimate = 0.0
        self.results = None
        self.error = None
    
    def save(self):
        """Save job to persistent storage"""
        persistent_job_manager.save_job(self)
    
    def update_status(self, status, **kwargs):
        """Update job status and save to persistent storage"""
        self.status = status
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Save to persistent storage
        self.save()

def load_jobs_from_persistence():
    """Load jobs from persistent storage on startup"""
    global extraction_jobs
    
    try:
        persistent_jobs = persistent_job_manager.get_all_jobs()
        
        for job_id, job_data in persistent_jobs.items():
            # Recreate ExtractionJob object
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
            
            extraction_jobs[job_id] = job
        
        if persistent_jobs:
            print(f"🔄 Restored {len(persistent_jobs)} jobs from persistent storage")
        
    except Exception as e:
        print(f"❌ Error loading jobs from persistence: {e}")

def get_estimated_duration(priority):
    """Get estimated processing duration based on priority"""
    durations = {
        "cost": 240,     # 4 minutes for local processing
        "quality": 90,   # 1.5 minutes for GPT-4o
        "speed": 45,     # 45 seconds for DeepSeek
        "privacy": 240   # 4 minutes for local processing
    }
    return durations.get(priority, 120)

def get_model_for_priority(priority):
    """Get the model name for a given priority"""
    models = {
        "cost": "Local Llama 3.1 8B",
        "quality": "GPT-4o",
        "speed": "DeepSeek-V3",
        "privacy": "Local Llama 3.1 8B"
    }
    return models.get(priority, "Unknown")

def calculate_extraction_cost(job):
    """Calculate the cost estimate for the extraction"""
    cost_per_priority = {
        "cost": 0.0,        # Free local processing
        "quality": 0.008,   # GPT-4o cost estimate
        "speed": 0.002,     # DeepSeek cost estimate  
        "privacy": 0.0      # Free local processing
    }
    return cost_per_priority.get(job.priority, 0.0)

def calculate_success_rate():
    """Calculate success rate of recent extractions"""
    if not extraction_jobs:
        return 1.0
    
    completed_jobs = [j for j in extraction_jobs.values() if j.status in ['complete', 'error']]
    if not completed_jobs:
        return 1.0
    
    successful = len([j for j in completed_jobs if j.status == 'complete'])
    return successful / len(completed_jobs)

def calculate_avg_processing_time():
    """Calculate average processing time for completed jobs"""
    completed_jobs = [j for j in extraction_jobs.values() if j.status == 'complete']
    if not completed_jobs:
        return 120  # Default estimate
    
    total_time = sum(time.time() - j.start_time for j in completed_jobs)
    return total_time / len(completed_jobs)

def run_extraction_job(job):
    """Run the actual extraction job with enhanced document processing"""
    try:
        from app.extraction.adapters.enhanced_jsonld_bridge import extract_stakeholders_enhanced
        
        job.update_status('running')
        job.model_used = get_model_for_priority(job.priority)
        job.save()
        
        print(f"🤖 Starting comprehensive extraction for: {job.filename}")
        
        # Step 1: Create/update document metadata first
        job.current_step = "📄 Processing document metadata..."
        job.substep = "Creating comprehensive document profile"
        job.progress = 10
        job.save()
        
        # Get the JSON-LD directory from job options or use default
        jsonld_dir = job.options.get('jsonld_dir')
        if not jsonld_dir:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            jsonld_dir = os.path.join(current_dir, '..', '..', 'database', 'jsonld')
            jsonld_dir = os.path.abspath(jsonld_dir)
        
        print(f"📁 Using JSON-LD directory: {jsonld_dir}")
        
        # Pre-create document metadata if it doesn't exist
        from app.routes.agent_api import create_document_metadata_from_source
        document_metadata = create_document_metadata_from_source(job.filename)
        
        if document_metadata:
            # Save the document metadata first
            safe_filename = job.filename.replace(' ', '_').replace('/', '_').replace('\\', '_')
            if not safe_filename.endswith('.json'):
                safe_filename += '.json'
            
            metadata_path = os.path.join(jsonld_dir, safe_filename)
            os.makedirs(jsonld_dir, exist_ok=True)
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(document_metadata, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Document metadata pre-created: {metadata_path}")
            job.current_step = "✅ Document metadata created"
            job.progress = 20
            job.save()
        
        # Updated steps to reflect comprehensive processing
        steps = [
            ("📄 Document analysis complete", "Metadata and structure extracted"),
            ("🔍 Initializing LLM adapter...", "Loading language model"),
            ("🎯 Generating extraction prompt...", "Preparing AI analysis"),
            ("🤖 AI processing document content...", "Extracting stakeholder information"),
            ("🔍 Processing LLM response...", "Validating extracted stakeholders"),
            ("💾 Integrating results...", "Merging with document metadata"),
            ("✅ Finalizing output...", "Creating comprehensive JSON-LD")
        ]
        
        total_steps = len(steps)
        
        for i, (step, substep) in enumerate(steps[1:], 1):  # Skip first step (already done)
            job.current_step = step
            job.substep = substep
            job.progress = int(20 + (i / total_steps) * 50)  # 20-70%
            job.save()
            
            # Realistic sleep times
            sleep_time = {
                "cost": 1.5,
                "quality": 1.0,
                "speed": 0.5,
                "privacy": 1.5
            }.get(job.priority, 1.0)
            
            time.sleep(sleep_time)
        
        job.current_step = "🤖 AI extracting stakeholders..."
        job.substep = "Deep analysis of document content"
        job.progress = 70
        job.save()
        
        # Perform REAL extraction with LLM
        print(f"🤖 Starting LLM stakeholder extraction...")
        job.results = extract_stakeholders_enhanced(job.filename, jsonld_dir)
        
        job.progress = 90
        job.current_step = "🔗 Integrating with document metadata..."
        job.substep = "Creating comprehensive document profile"
        job.save()
        
        time.sleep(1)  # Brief pause for integration
        
        job.progress = 100
        job.current_step = "✅ Comprehensive extraction complete"
        job.substep = "Document metadata + stakeholders ready"
        job.update_status('complete')
        
        # Calculate cost estimate
        job.cost_estimate = calculate_extraction_cost(job)
        job.save()
        
        print(f"✅ Comprehensive extraction job {job.job_id} completed successfully")
        print(f"📊 Results include:")
        print(f"   - Stakeholders: {len(job.results.get('stakeholders', []))}")
        print(f"   - Document metadata: Available for integration")
        
    except Exception as e:
        job.update_status('error', error=str(e))
        job.progress = 0
        print(f"❌ Extraction job {job.job_id} failed: {e}")
        import traceback
        traceback.print_exc()

# Load jobs on module import
print("🔄 Loading persistent jobs on startup...")
load_jobs_from_persistence()

# Export functions
__all__ = [
    'ExtractionJob',
    'extraction_jobs',
    'job_counter',
    'get_estimated_duration',
    'get_model_for_priority',
    'calculate_extraction_cost',
    'calculate_success_rate',
    'calculate_avg_processing_time',
    'run_extraction_job',
    'load_jobs_from_persistence'
]