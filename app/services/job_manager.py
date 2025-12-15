from datetime import datetime
from typing import Dict, Optional
import uuid


class JobManager:
    """
    In-memory job manager for tracking composite image creation jobs.
    For production, consider using Redis or a database.
    """

    def __init__(self):
        self.jobs: Dict[str, dict] = {}

    def create_job(self) -> str:
        """Create a new job and return job_id"""
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'completed_at': None,
            'result': None,
            'error': None
        }
        return job_id

    def update_job_status(self, job_id: str, status: str):
        """Update job status"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = status

    def complete_job(self, job_id: str, result: dict):
        """Mark job as completed with result"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = 'completed'
            self.jobs[job_id]['completed_at'] = datetime.utcnow().isoformat() + 'Z'
            self.jobs[job_id]['result'] = result

    def fail_job(self, job_id: str, error: str):
        """Mark job as failed with error message"""
        if job_id in self.jobs:
            self.jobs[job_id]['status'] = 'failed'
            self.jobs[job_id]['completed_at'] = datetime.utcnow().isoformat() + 'Z'
            self.jobs[job_id]['error'] = error

    def get_job(self, job_id: str) -> Optional[dict]:
        """Get job status and result"""
        return self.jobs.get(job_id)


# Singleton instance
job_manager = JobManager()
