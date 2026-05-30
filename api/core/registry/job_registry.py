# gemini-flash
from dataclasses import dataclass
from typing import List, Optional
from .base_registry import Registry

@dataclass
class JobSpec:
    key: str
    schedule_cron: str
    handler_path: str
    app: str = ""
    enabled_default: bool = True

class JobRegistry(Registry[JobSpec]):
    """Registry for background jobs."""
    
    def register_from_manifest(self, app_name: str, manifest: dict):
        jobs = manifest.get("jobs", [])
        for job in jobs:
            if isinstance(job, dict):
                job_obj = JobSpec(
                    key=job["key"],
                    schedule_cron=job["schedule_cron"],
                    handler_path=job["handler_path"],
                    app=app_name,
                    enabled_default=job.get("enabled_default", True)
                )
                self.register(app_name, job_obj.key, job_obj)
            elif isinstance(job, JobSpec):
                job.app = app_name
                self.register(app_name, job.key, job)

# Singleton instance
job_registry = JobRegistry()
