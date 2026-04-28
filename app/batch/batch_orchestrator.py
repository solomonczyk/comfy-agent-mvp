"""Batch orchestrator for KT-4 batch orchestration."""
import asyncio
from pathlib import Path
from typing import Any, Callable

from app.assets.organizer import organize_run_artifacts
from app.batch.manifest import BatchManifest, ManifestPersistence
from app.batch.spec_loader import BatchSpec


class BatchOrchestrator:
    """Orchestrates execution of batch jobs headlessly."""
    
    def __init__(
        self,
        batches_dir: Path,
        manifests_dir: Path,
        job_executor: Callable[[str, str, dict[str, Any]], dict[str, Any]],
    ):
        self.batches_dir = batches_dir
        self.batches_dir.mkdir(parents=True, exist_ok=True)
        self.manifests_dir = manifests_dir
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_persistence = ManifestPersistence(manifests_dir)
        self.job_executor = job_executor
    
    async def run_batch(self, spec: BatchSpec) -> dict[str, Any]:
        """Run a batch of jobs sequentially (headless execution)."""
        # Create batch output directory
        batch_output_dir = self.batches_dir / spec.batch_id
        batch_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize manifest
        manifest = BatchManifest(
            batch_id=spec.batch_id,
            spec_path=str(spec.batch_id),
            output_dir=batch_output_dir,
            total_jobs=len(spec.jobs),
        )
        self.manifest_persistence.save(manifest)
        
        # Execute jobs sequentially
        results = []
        for job in spec.jobs:
            job_id = job["job_id"]
            mode = job["mode"]
            prompt = job["prompt"]
            settings = job.get("settings", {})
            
            # Create job-specific output directory
            job_output_dir = batch_output_dir / job_id
            job_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Execute job
            try:
                result = await self.job_executor(
                    mode=mode,
                    prompt=prompt,
                    settings=settings,
                    output_dir=job_output_dir,
                )
                # KT-5: organize job artifacts into data/batches/{batch_id}/{job_id}/
                try:
                    asset_report = organize_run_artifacts(
                        target_dir=job_output_dir,
                        result=result,
                    )
                    result["asset_report"] = asset_report
                except Exception as asset_exc:
                    result["asset_report"] = {"error": str(asset_exc)}
                manifest.update_job(job_id, result)
                results.append({
                    "job_id": job_id,
                    "status": result.get("status", "unknown"),
                    "verdict": result.get("verdict", "unknown"),
                })
            except Exception as exc:
                error_result = {
                    "status": "failed",
                    "verdict": "failed",
                    "error": str(exc),
                    "failed_stage": "execution",
                }
                manifest.update_job(job_id, error_result)
                results.append({
                    "job_id": job_id,
                    "status": "failed",
                    "verdict": "failed",
                    "error": str(exc),
                })
            
            # Persist manifest after each job
            self.manifest_persistence.save(manifest)
        
        # Mark batch as completed
        manifest.complete()
        self.manifest_persistence.save(manifest)
        
        # Return batch result
        return {
            "batch_id": spec.batch_id,
            "status": manifest.status,
            "total_jobs": len(spec.jobs),
            "completed_jobs": len([r for r in results if r["status"] == "completed"]),
            "failed_jobs": len([r for r in results if r["status"] == "failed"]),
            "results": results,
            "output_dir": str(batch_output_dir),
            "manifest_path": str(self.manifests_dir / f"{spec.batch_id}.json"),
        }
