"""
Persistent Job Storage for DocEX
Stores extraction jobs in files to survive Flask restarts
"""

import os
import json
import time
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class PersistentJobManager:
    """Manages extraction jobs with persistent storage"""
    
    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            storage_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'temp', 'jobs')
        
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Persistent job storage: {self.storage_dir}")
    
    def save_job(self, job):
        """Save job to persistent storage"""
        try:
            job_file = self.storage_dir / f"{job.job_id}.json"
            
            job_data = {
                'job_id': job.job_id,
                'filename': job.filename,
                'priority': job.priority,
                'options': job.options,
                'status': job.status,
                'progress': job.progress,
                'current_step': job.current_step,
                'substep': job.substep,
                'start_time': job.start_time,
                'model_used': job.model_used,
                'cost_estimate': job.cost_estimate,
                'results': job.results,
                'error': job.error
            }
            
            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(job_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Job {job.job_id} saved to persistent storage")
            return True
            
        except Exception as e:
            print(f"❌ Error saving job {job.job_id}: {e}")
            return False
    
    def load_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load job from persistent storage"""
        try:
            job_file = self.storage_dir / f"{job_id}.json"
            
            if not job_file.exists():
                return None
            
            with open(job_file, 'r', encoding='utf-8') as f:
                job_data = json.load(f)
            
            print(f"📂 Job {job_id} loaded from persistent storage")
            return job_data
            
        except Exception as e:
            print(f"❌ Error loading job {job_id}: {e}")
            return None
    
    def update_job_status(self, job_id: str, status: str, **kwargs):
        """Update job status in persistent storage"""
        try:
            job_data = self.load_job(job_id)
            if job_data:
                job_data['status'] = status
                job_data.update(kwargs)
                
                job_file = self.storage_dir / f"{job_id}.json"
                with open(job_file, 'w', encoding='utf-8') as f:
                    json.dump(job_data, f, indent=2, ensure_ascii=False)
                
                print(f"🔄 Job {job_id} status updated to: {status}")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error updating job {job_id}: {e}")
            return False
    
    def get_all_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all jobs from persistent storage"""
        jobs = {}
        
        try:
            for job_file in self.storage_dir.glob("*.json"):
                job_id = job_file.stem
                job_data = self.load_job(job_id)
                if job_data:
                    jobs[job_id] = job_data
            
            print(f"📊 Loaded {len(jobs)} jobs from persistent storage")
            return jobs
            
        except Exception as e:
            print(f"❌ Error loading all jobs: {e}")
            return {}
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old job files"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            cleaned = 0
            
            for job_file in self.storage_dir.glob("*.json"):
                if job_file.stat().st_mtime < cutoff_time:
                    job_file.unlink()
                    cleaned += 1
            
            if cleaned > 0:
                print(f"🧹 Cleaned up {cleaned} old job files")
                
        except Exception as e:
            print(f"❌ Error cleaning up jobs: {e}")

# Global persistent job manager
persistent_job_manager = PersistentJobManager()