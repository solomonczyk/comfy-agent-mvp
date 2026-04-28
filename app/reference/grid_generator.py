"""MK-R1 — Character reference grid generator.

Generates a grid of reference images for a character via ComfyUI,
then stitches them into a single PNG used as IP-Adapter input.
"""
from __future__ import annotations

import copy
import json
import logging
import random
import time
from pathlib import Path
from typing import Any

from app.brief.models import CharacterDef, ProjectMeta

log = logging.getLogger(__name__)

POSE_HINTS: list[str] = [
    "front view, neutral pose",
    "front view, slight smile",
    "front view, looking down",
    "front view, tired expression",
    "three quarter view left",
    "three quarter view right",
    "side profile left",
    "side profile right",
    "looking up",
    "looking away",
    "sitting pose",
    "standing pose",
    "close up face",
    "medium shot",
    "hands visible",
    "from behind",
]


class ReferenceGridGenerator:
    """Generates a character reference grid via ComfyUI and stitches with PIL."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        workflow_template: dict | None = None,
        checkpoint: str | None = None,
        session: Any = None,
        allow_live_submit: bool = False,
    ) -> None:
        self.host = host
        self.port = port
        self.checkpoint = checkpoint
        self.allow_live_submit = allow_live_submit

        if workflow_template is None:
            template_path = Path("data/workflow_template.json")
            with open(template_path, encoding="utf-8") as f:
                workflow_template = json.load(f)
        self.workflow_template = workflow_template

        if session is None:
            import requests
            self.session = requests.Session()
        else:
            self.session = session

    # ── public ────────────────────────────────────────────────────────────────

    def get_best_frame(self, output_dir: Path, character_name: str) -> Path:
        """Return path to the single best individual frame (first generated: _ref_0000).

        The frames subdir is output_dir/frames/. Falls back to the grid PNG if no
        individual frame is found.

        Args:
            output_dir: Same directory passed to generate().
            character_name: Character name used during generation.

        Returns:
            Path to the best individual frame PNG.

        Raises:
            FileNotFoundError: If neither a frame nor the grid PNG exists.
        """
        frames_dir = Path(output_dir) / "frames"
        best = frames_dir / f"{character_name}_frame_0000.png"
        if best.exists():
            return best
        # fallback: any _ref_0000 in output_dir itself (older layout)
        fallback_old = Path(output_dir) / f"{character_name}_ref_0000.png"
        if fallback_old.exists():
            return fallback_old
        # last resort: grid
        grid = Path(output_dir) / f"{character_name}_reference_grid.png"
        if grid.exists():
            log.warning(f"[GRID] get_best_frame: no individual frame found, falling back to grid")
            return grid
        raise FileNotFoundError(
            f"No reference frame found for '{character_name}' in {output_dir}"
        )

    def generate(
        self,
        character: CharacterDef,
        meta: ProjectMeta,
        output_dir: Path,
        grid_size: int = 4,
    ) -> Path:
        """Generate a grid_size×grid_size reference grid PNG for character.

        Args:
            character: CharacterDef with name and visual_description.
            meta: ProjectMeta for style/mood context.
            output_dir: Directory to save individual frames and final grid.
            grid_size: Side length of the grid (default 4 → 4×4 = 16 images).

        Returns:
            Path to the stitched grid PNG.
        """
        if not self.allow_live_submit:
            raise RuntimeError(
                "ReferenceGridGenerator live ComfyUI submit is disabled. "
                "Set allow_live_submit=True explicitly for real generation."
            )
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "frames").mkdir(parents=True, exist_ok=True)

        total = grid_size * grid_size
        base_seed = hash(character.name) % (2 ** 32)
        style = meta.style_hint or ""
        mood = meta.mood or ""

        log.info(f"[GRID] Generating {total} reference images for '{character.name}'")

        frame_paths: list[Path] = []
        for idx in range(total):
            pose = POSE_HINTS[idx % len(POSE_HINTS)]
            positive = self._build_prompt(character, style, mood, pose)
            seed = (base_seed + idx) % (2 ** 32)
            frame_path = self._generate_single(
                positive=positive,
                seed=seed,
                idx=idx,
                character_name=character.name,
                output_dir=output_dir / "frames",
            )
            if frame_path:
                frame_paths.append(frame_path)
                log.info(f"[GRID] Frame {idx+1}/{total}: {frame_path.name}")
            else:
                log.warning(f"[GRID] Frame {idx+1}/{total}: no output collected")

        if not frame_paths:
            raise RuntimeError(f"No frames generated for character '{character.name}'")

        grid_path = self._stitch_grid(frame_paths, grid_size, character.name, output_dir / "frames")
        log.info(f"[GRID] Grid saved: {grid_path} ({grid_path.stat().st_size // 1024} KB)")
        return grid_path

    # ── helpers ───────────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        character: CharacterDef,
        style: str,
        mood: str,
        pose: str,
    ) -> str:
        parts = [character.visual_description, pose]
        if style:
            parts.append(style)
        if mood:
            parts.append(mood)
        return ", ".join(p.strip() for p in parts if p.strip())

    _IPADAPTER_CLASSES = frozenset(
        ("IPAdapterAdvanced", "IPAdapter", "IPAdapterFaceID",
         "IPAdapterUnifiedLoader", "LoadImage")
    )

    def _strip_ipadapter(self, workflow: dict) -> dict:
        """Remove IPAdapter-related nodes and reconnect KSampler model to checkpoint."""
        # Find checkpoint loader node id
        ckpt_node_id: str | None = None
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "CheckpointLoaderSimple":
                ckpt_node_id = node_id
                break

        # Remove IPAdapter nodes
        to_remove = [
            nid for nid, node in workflow.items()
            if isinstance(node, dict) and node.get("class_type", "") in self._IPADAPTER_CLASSES
        ]
        for nid in to_remove:
            del workflow[nid]

        # Reconnect KSampler model input to checkpoint loader
        if ckpt_node_id:
            for node in workflow.values():
                if isinstance(node, dict) and node.get("class_type") == "KSampler":
                    node["inputs"]["model"] = [ckpt_node_id, 0]

        return workflow

    def _generate_single(
        self,
        positive: str,
        seed: int,
        idx: int,
        character_name: str,
        output_dir: Path,
    ) -> Path | None:
        workflow = copy.deepcopy(self.workflow_template)

        inject_map = workflow.pop("__inject__", {})
        pos_node = inject_map.get("positive_prompt_node")
        if pos_node and pos_node in workflow:
            workflow[pos_node]["inputs"]["text"] = positive

        # Strip IPAdapter nodes — no reference image at grid generation stage
        workflow = self._strip_ipadapter(workflow)

        for node in workflow.values():
            if isinstance(node, dict) and node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = seed
                node["inputs"]["batch_size"] = 1

        for node in workflow.values():
            if isinstance(node, dict) and node.get("class_type") == "EmptyLatentImage":
                node["inputs"]["batch_size"] = 1
                node["inputs"]["width"] = 512
                node["inputs"]["height"] = 512

        if self.checkpoint:
            from app.comfy.workflow_patcher import WorkflowPatcher
            WorkflowPatcher.patch_checkpoint(workflow, self.checkpoint)

        job_start = time.time()
        url = f"http://{self.host}:{self.port}/prompt"
        resp = self.session.post(url, json={"prompt": workflow}, timeout=30)
        if resp.status_code != 200:
            log.error(f"[GRID] Submit failed HTTP {resp.status_code}")
            return None

        prompt_id = resp.json().get("prompt_id")
        if not prompt_id:
            log.error("[GRID] No prompt_id returned")
            return None

        self._poll(prompt_id, timeout_sec=300)

        return self._collect_frame(prompt_id, job_start, idx, character_name, output_dir)

    def _poll(self, prompt_id: str, timeout_sec: float = 300) -> None:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            resp = self.session.get(
                f"http://{self.host}:{self.port}/history/{prompt_id}", timeout=10
            )
            if resp.status_code == 200:
                history = resp.json()
                if prompt_id in history:
                    status = history[prompt_id].get("status", {})
                    if status.get("completed", False):
                        return
            time.sleep(1.0)
        raise TimeoutError(f"[GRID] Timeout waiting for prompt {prompt_id}")

    def _collect_frame(
        self,
        prompt_id: str,
        job_start: float,
        idx: int,
        character_name: str,
        output_dir: Path,
    ) -> Path | None:
        """Copy the newest ComfyUI output frame to output_dir (the frames/ subdir)."""
        comfy_out = Path(
            "F:/ComfyUI/comfyUI_portable_inst/ComfyUI_windows_portable_nvidia_cu126"
            "/ComfyUI_windows_portable/ComfyUI/output/agent"
        )
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if comfy_out.exists():
            recent = sorted(
                [p for p in comfy_out.glob("*.png") if p.stat().st_mtime >= job_start],
                key=lambda p: p.stat().st_mtime,
            )
            if recent:
                dest = output_dir / f"{character_name}_frame_{idx:04d}.png"
                import shutil
                shutil.copy2(recent[0], dest)
                return dest
        return None

    def _stitch_grid(
        self,
        frame_paths: list[Path],
        grid_size: int,
        character_name: str,
        output_dir: Path,
    ) -> Path:
        from PIL import Image

        images = []
        for p in frame_paths:
            try:
                images.append(Image.open(p).convert("RGB"))
            except Exception as exc:
                log.warning(f"[GRID] Could not open {p}: {exc}")

        if not images:
            raise RuntimeError("No valid images to stitch into grid")

        img_w, img_h = images[0].size

        cols = grid_size
        rows = (len(images) + cols - 1) // cols

        grid_w = cols * img_w
        grid_h = rows * img_h
        grid = Image.new("RGB", (grid_w, grid_h), color=(0, 0, 0))

        for i, img in enumerate(images):
            col = i % cols
            row = i // cols
            if img.size != (img_w, img_h):
                img = img.resize((img_w, img_h), Image.LANCZOS)
            grid.paste(img, (col * img_w, row * img_h))

        grid_path = output_dir.parent / f"{character_name}_reference_grid.png"
        grid.save(str(grid_path))
        return grid_path
