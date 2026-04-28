"""Batch manifest persistence for KT-4 batch orchestration."""
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class BatchManifest:
    """Manifest tracking batch execution status and job results."""
    
    def __init__(
        self,
        batch_id: str,
        spec_path: str,
        output_dir: Path,
        total_jobs: int,
    ):
        self.batch_id = batch_id
        self.spec_path = spec_path
        self.output_dir = str(output_dir)
        self.total_jobs = total_jobs
        self.started_at = datetime.utcnow().isoformat()
        self.completed_at = None
        self.jobs: dict[str, dict[str, Any]] = {}
        self.status = "running"
    
    def update_job(self, job_id: str, result: dict[str, Any]) -> None:
        """Update job status and result."""
        self.jobs[job_id] = {
            "status": result.get("status", "unknown"),
            "verdict": result.get("verdict", "unknown"),
            "failed_stage": result.get("failed_stage"),
            "error": result.get("error"),
            "images": result.get("images", []),
            "metadata_path": result.get("metadata_path"),
            "summary_path": result.get("summary_path"),
            "trace_path": result.get("trace_path"),
            "completed_at": datetime.utcnow().isoformat(),
        }
    
    def complete(self) -> None:
        """Mark batch as completed."""
        self.completed_at = datetime.utcnow().isoformat()
        self.status = "completed"
    
    def fail(self, reason: str) -> None:
        """Mark batch as failed."""
        self.completed_at = datetime.utcnow().isoformat()
        self.status = "failed"
        self.failure_reason = reason
    
    def to_dict(self) -> dict[str, Any]:
        """Convert manifest to dictionary for JSON serialization."""
        return {
            "batch_id": self.batch_id,
            "spec_path": self.spec_path,
            "output_dir": self.output_dir,
            "total_jobs": self.total_jobs,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "status": self.status,
            "jobs": self.jobs,
        }
    
    @staticmethod
    def from_dict(data: dict[str, Any]) -> "BatchManifest":
        """Create manifest from dictionary."""
        manifest = BatchManifest(
            batch_id=data["batch_id"],
            spec_path=data["spec_path"],
            output_dir=Path(data["output_dir"]),
            total_jobs=data["total_jobs"],
        )
        manifest.started_at = data["started_at"]
        manifest.completed_at = data.get("completed_at")
        manifest.status = data.get("status", "running")
        manifest.jobs = data.get("jobs", {})
        return manifest


class ManifestPersistence:
    """Handles saving and loading batch manifests."""
    
    def __init__(self, manifests_dir: Path):
        self.manifests_dir = manifests_dir
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, manifest: BatchManifest) -> Path:
        """Save manifest to disk."""
        manifest_path = self.manifests_dir / f"{manifest.batch_id}.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2)
        return manifest_path
    
    def load(self, batch_id: str) -> BatchManifest | None:
        """Load manifest from disk."""
        manifest_path = self.manifests_dir / f"{batch_id}.json"
        if not manifest_path.exists():
            return None
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return BatchManifest.from_dict(data)
