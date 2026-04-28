"""Batch spec loader for KT-4 batch orchestration."""
import json
from pathlib import Path
from typing import Any


class BatchSpec:
    """Batch specification defining a set of jobs to execute."""
    
    def __init__(self, batch_id: str, description: str, jobs: list[dict[str, Any]]):
        self.batch_id = batch_id
        self.description = description
        self.jobs = jobs
    
    def __repr__(self) -> str:
        return f"BatchSpec(batch_id={self.batch_id}, jobs={len(self.jobs)})"


class SpecLoader:
    """Loads and validates batch specification files."""
    
    @staticmethod
    def load(spec_path: Path) -> BatchSpec:
        """Load a batch spec from a JSON file."""
        if not spec_path.exists():
            raise FileNotFoundError(f"Batch spec not found: {spec_path}")
        
        with open(spec_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Validate required fields
        if "batch_id" not in data:
            raise ValueError("Batch spec missing required field: batch_id")
        if "jobs" not in data:
            raise ValueError("Batch spec missing required field: jobs")
        
        # Validate jobs structure
        jobs = data["jobs"]
        if not isinstance(jobs, list):
            raise ValueError("Batch spec 'jobs' must be a list")
        
        for i, job in enumerate(jobs):
            if "job_id" not in job:
                raise ValueError(f"Job {i} missing required field: job_id")
            if "mode" not in job:
                raise ValueError(f"Job {i} missing required field: mode")
            if "prompt" not in job:
                raise ValueError(f"Job {i} missing required field: prompt")
        
        return BatchSpec(
            batch_id=data["batch_id"],
            description=data.get("description", ""),
            jobs=jobs,
        )
