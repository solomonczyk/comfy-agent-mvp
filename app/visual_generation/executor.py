"""
Exactly-one-generation ComfyUI executor.
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


COMFYUI_DEFAULT_HOST = "127.0.0.1"
COMFYUI_DEFAULT_PORT = 8188
MAX_POLL_SECONDS = 300
POLL_INTERVAL = 5


class GenerationExecutor:
    """Submits exactly one ComfyUI generation. No retry. No second submit."""

    TASK_ID = "RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001"

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.gate_dir = self.control_dir / "controlled_visual_generation_gate"
        self.candidate_dir = self.control_dir / "fresh_visual_candidate"
        self.assets_dir = self.project_root / "output" / "assets" / "fresh_visual_candidates"

    def execute(
        self,
        workflow_payload: Dict[str, Any],
        comfyui_host: str = COMFYUI_DEFAULT_HOST,
        comfyui_port: int = COMFYUI_DEFAULT_PORT,
    ) -> Dict[str, Any]:
        """
        Submit workflow to ComfyUI, wait for completion, collect outputs.
        Returns execution result dict.
        """
        self.candidate_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        base_url = f"http://{comfyui_host}:{comfyui_port}"

        # Fresh generation: force denoise=1.0 on all KSampler nodes
        # (denoise<1.0 is img2img mode and crashes with EmptyLatentImage)
        workflow_payload = self._patch_denoise(workflow_payload)

        # --- Submit ---
        try:
            prompt_id, error = self._submit(base_url, workflow_payload)
        except Exception as exc:
            return self._failure_result(str(exc), generation_attempted=True)

        if error or not prompt_id:
            return self._failure_result(error or "no prompt_id returned", generation_attempted=True)

        # --- Poll for completion ---
        completed, history = self._poll(base_url, prompt_id)
        if not completed:
            return self._failure_result(
                f"ComfyUI execution timed out after {MAX_POLL_SECONDS}s",
                prompt_id=prompt_id,
                generation_attempted=True,
            )

        # --- Collect outputs ---
        output_images = self._collect_images(history, prompt_id)
        if not output_images:
            # ComfyUI sometimes returns empty outputs even on success —
            # fall back to scanning disk by SaveImage filename_prefix
            from app.visual_generation.manifest import COMFYUI_OUTPUT_DIR
            output_images = self._collect_images_from_disk(
                workflow_payload, COMFYUI_OUTPUT_DIR
            )
        if not output_images:
            return self._failure_result(
                "No output images found in history or on disk",
                prompt_id=prompt_id,
                generation_attempted=True,
            )

        result = {
            "task_id": self.TASK_ID,
            "document_type": "generation_execution_report",
            "timestamp": self._now(),
            "generation_performed": True,
            "generation_count": 1,
            "max_generations": 1,
            "workflow_submitted": True,
            "comfyui_execution": True,
            "prompt_id": prompt_id,
            "output_images": output_images,
            "retry_attempted": False,
            "second_generation_attempted": False,
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "failure": False,
            "failure_reason": None,
        }

        with open(self.candidate_dir / "generation_execution_report.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        return result

    # ------------------------------------------------------------------
    # ComfyUI interaction
    # ------------------------------------------------------------------

    def _submit(self, base_url: str, payload: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        body = json.dumps({"prompt": payload}).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}/prompt",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if "error" in data:
            return None, str(data["error"])
        return data.get("prompt_id"), None

    def _poll(self, base_url: str, prompt_id: str) -> tuple[bool, Dict[str, Any]]:
        deadline = time.time() + MAX_POLL_SECONDS
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(
                    f"{base_url}/history/{prompt_id}", timeout=10
                ) as resp:
                    history = json.loads(resp.read().decode("utf-8"))
                if prompt_id in history:
                    return True, history[prompt_id]
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)
        return False, {}

    def _collect_images(
        self, history: Dict[str, Any], prompt_id: str
    ) -> List[str]:
        images: List[str] = []
        outputs = history.get("outputs", {})
        for node_id, node_out in outputs.items():
            for img in node_out.get("images", []):
                filename = img.get("filename", "")
                if filename:
                    images.append(filename)
        return images

    def _collect_images_from_disk(
        self, workflow_payload: Dict[str, Any], comfyui_output_dir: str
    ) -> List[str]:
        """Fallback: find files by filename_prefix from SaveImage nodes."""
        import glob
        images: List[str] = []
        output_path = Path(comfyui_output_dir)
        for node in workflow_payload.values():
            if isinstance(node, dict) and node.get("class_type") == "SaveImage":
                prefix = node.get("inputs", {}).get("filename_prefix", "")
                if prefix:
                    pattern = str(output_path / f"{prefix}*.png")
                    found = sorted(glob.glob(pattern))
                    # Take only the newest file (latest generation)
                    if found:
                        images.append(Path(found[-1]).name)
        return images

    def _failure_result(
        self,
        reason: str,
        prompt_id: Optional[str] = None,
        generation_attempted: bool = False,
    ) -> Dict[str, Any]:
        result = {
            "task_id": self.TASK_ID,
            "document_type": "generation_execution_report",
            "timestamp": self._now(),
            "generation_performed": False,
            "generation_count": 1 if generation_attempted else 0,
            "max_generations": 1,
            "workflow_submitted": generation_attempted,
            "comfyui_execution": False,
            "prompt_id": prompt_id,
            "output_images": [],
            "retry_attempted": False,
            "second_generation_attempted": False,
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "failure": True,
            "failure_reason": reason,
        }
        self.candidate_dir.mkdir(parents=True, exist_ok=True)
        with open(
            self.candidate_dir / "generation_execution_report.json", "w", encoding="utf-8"
        ) as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        return result

    @staticmethod
    def _patch_denoise(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Force denoise=1.0 on KSampler/KSamplerAdvanced nodes for txt2img."""
        import copy
        payload = copy.deepcopy(payload)
        for node in payload.values():
            if isinstance(node, dict):
                ct = node.get("class_type", "")
                if ct in ("KSampler", "KSamplerAdvanced"):
                    inputs = node.get("inputs", {})
                    if "denoise" in inputs:
                        inputs["denoise"] = 1.0
        return payload

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
