"""
Generated candidate manifest collector.
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from PIL import Image, UnidentifiedImageError
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


COMFYUI_OUTPUT_DIR = (
    "F:\\ComfyUI\\comfyUI_portable_inst\\ComfyUI_windows_portable_nvidia_cu126"
    "\\ComfyUI_windows_portable\\ComfyUI\\output"
)


class ManifestCollector:
    """Collects generated images into canonical assets dir and builds manifest."""

    TASK_ID = "RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001"

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.candidate_dir = self.control_dir / "fresh_visual_candidate"
        self.assets_dir = self.project_root / "output" / "assets" / "fresh_visual_candidates"

    def collect(
        self,
        prompt_id: str,
        output_images: List[str],
        comfyui_output_dir: str = COMFYUI_OUTPUT_DIR,
    ) -> Dict[str, Any]:
        """
        Copy images from ComfyUI output dir to canonical assets dir.
        Returns manifest dict.
        """
        self.candidate_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        collected: List[Dict[str, Any]] = []
        for filename in output_images:
            src = Path(comfyui_output_dir) / filename
            if not src.exists():
                # Try without subfolder
                collected.append(
                    {
                        "source_filename": filename,
                        "path": None,
                        "exists": False,
                        "readable": False,
                        "sha256": None,
                        "size_bytes": 0,
                        "width": 0,
                        "height": 0,
                        "error": f"source file not found: {src}",
                    }
                )
                continue

            dst = self.assets_dir / filename
            shutil.copy2(src, dst)

            sha256 = self._sha256(dst)
            size = dst.stat().st_size
            width, height = self._dimensions(dst)

            canonical = str(dst.relative_to(self.project_root.parent.parent)).replace("\\", "/")

            collected.append(
                {
                    "source_filename": filename,
                    "path": str(dst),
                    "exists": dst.exists(),
                    "readable": dst.stat().st_size > 0,
                    "sha256": sha256,
                    "size_bytes": size,
                    "width": width,
                    "height": height,
                }
            )

        all_present = all(a.get("exists") and a.get("readable") for a in collected)

        manifest = {
            "task_id": self.TASK_ID,
            "document_type": "generated_candidate_manifest",
            "timestamp": self._now(),
            "generation_performed": True,
            "generation_count": 1,
            "max_generations": 1,
            "workflow_submitted": True,
            "comfyui_execution": True,
            "prompt_id": prompt_id,
            "generated_assets": collected,
            "all_assets_present": all_present,
            "retry_attempted": False,
            "second_generation_attempted": False,
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
        }

        with open(
            self.candidate_dir / "generated_candidate_manifest.json", "w", encoding="utf-8"
        ) as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        return manifest

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _dimensions(path: Path) -> tuple[int, int]:
        if not PIL_AVAILABLE:
            return 0, 0
        try:
            with Image.open(path) as img:
                return img.width, img.height
        except Exception:
            return 0, 0

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
