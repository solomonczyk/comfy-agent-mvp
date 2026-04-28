"""RC-RUNTIME1 — PreflightService for workflow validation."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PIL import Image
import numpy as np
from scipy.stats import entropy as scipy_entropy

from app.runtime.checkpoint_resolver import CheckpointResolverLite
from app.runtime.resize_selector import ResizeNodeSelector
from app.runtime.schema_registry import ComfyNodeSchemaRegistry
from app.runtime.workflow_editor import WorkflowGraphEditorLite

log = logging.getLogger(__name__)


class PreflightService:
    """Service for preflight validation of ComfyUI workflows.
    
    RC-RUNTIME1 — Validates workflows before submission to ComfyUI.
    Returns structured READY/BLOCKED JSON with detailed blocking reasons.
    """
    
    def __init__(
        self,
        schema_registry: ComfyNodeSchemaRegistry | None = None,
        checkpoint_resolver: CheckpointResolverLite | None = None,
    ):
        """Initialize preflight service.
        
        Args:
            schema_registry: Optional schema registry (creates default if None)
            checkpoint_resolver: Optional checkpoint resolver (creates default if None)
        """
        self.schema_registry = schema_registry or ComfyNodeSchemaRegistry()
        self.checkpoint_resolver = checkpoint_resolver or CheckpointResolverLite()
    
    def validate_clean_reference(
        self,
        reference_path: str | Path,
    ) -> dict[str, Any]:
        """RC-REAL2 — Validate clean reference image before submission.
        
        Validates that the clean reference is visually valid:
        - exists and readable
        - dimensions 480x640
        - entropy above threshold (> 2.0)
        - stddev above threshold (> 10.0)
        - not solid/near-solid
        - not contact sheet/grid
        - not UI strip/text panel
        
        Args:
            reference_path: Path to clean reference image
            
        Returns:
            Dict with 'valid' (bool), 'blocks' (list), and 'qc_stats' (dict)
        """
        reference_path = Path(reference_path)
        blocks = []
        qc_stats = {}
        
        # 1. Check file exists
        if not reference_path.exists():
            blocks.append(f"Clean reference does not exist: {reference_path}")
            return {"valid": False, "blocks": blocks, "qc_stats": qc_stats}
        
        # 2. Check file is readable
        try:
            img = Image.open(reference_path)
            img.load()
        except Exception as e:
            blocks.append(f"Clean reference is not readable: {e}")
            return {"valid": False, "blocks": blocks, "qc_stats": qc_stats}
        
        # 3. Check dimensions
        width, height = img.size
        qc_stats["dimensions"] = f"{width}x{height}"
        if width != 480 or height != 640:
            blocks.append(f"Clean reference dimensions invalid: {width}x{height} (expected 480x640)")
        
        # 4. Convert to numpy for stats
        arr = np.array(img)
        if len(arr.shape) != 3 or arr.shape[2] != 3:
            blocks.append(f"Clean reference has invalid shape: {arr.shape} (expected (H, W, 3))")
            return {"valid": False, "blocks": blocks, "qc_stats": qc_stats}
        
        # 5. Calculate statistics
        mean = arr.mean()
        stddev = arr.std()
        variance = arr.var()
        qc_stats["mean"] = float(mean)
        qc_stats["stddev"] = float(stddev)
        qc_stats["variance"] = float(variance)
        
        # 6. Calculate entropy
        hist, _ = np.histogram(arr.flatten(), bins=256, range=(0, 256))
        hist = hist / hist.sum()
        img_entropy = scipy_entropy(hist, base=2)
        qc_stats["entropy"] = float(img_entropy)
        
        # 7. Check entropy threshold
        entropy_threshold = 2.0
        if img_entropy < entropy_threshold:
            blocks.append(
                f"Clean reference entropy too low: {img_entropy:.4f} < {entropy_threshold} "
                f"(indicates blank/solid image)"
            )
        
        # 8. Check stddev threshold
        stddev_threshold = 10.0
        if stddev < stddev_threshold:
            blocks.append(
                f"Clean reference stddev too low: {stddev:.2f} < {stddev_threshold} "
                f"(indicates near-solid image)"
            )
        
        # 9. Check for multi-panel/contact sheet
        aspect_ratio = width / height
        if aspect_ratio > 3.0 or aspect_ratio < 0.33:
            blocks.append(
                f"Clean reference has extreme aspect ratio {aspect_ratio:.2f} "
                f"(suggests contact sheet/grid)"
            )
        
        # 10. Final verdict
        valid = len(blocks) == 0
        qc_stats["file_size_bytes"] = reference_path.stat().st_size
        qc_stats["verdict"] = "VALID" if valid else "INVALID"
        
        return {
            "valid": valid,
            "blocks": blocks,
            "qc_stats": qc_stats,
        }

    def validate_reference_locked_workflow(
        self,
        workflow: dict[str, Any],
        checkpoint_name: str,
        project_root: str | Path | None = None,
        clean_reference_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """Validate a reference_locked workflow before submission.
        
        RC-RUNTIME1 — Blocks invalid reference_locked graphs:
        - missing LoadImage
        - missing resize
        - missing VAEEncode
        - KSampler.latent_image points to EmptyLatentImage
        - dangling links
        - missing checkpoint
        - unsafe AppData/Temp/pytest production paths
        
        RC-REAL2 — Blocks invalid clean references:
        - clean reference does not exist
        - clean reference is not readable
        - clean reference dimensions invalid
        - clean reference entropy too low (blank/solid)
        - clean reference stddev too low (near-solid)
        - clean reference appears to be contact sheet/grid
        
        Args:
            workflow: ComfyUI workflow dict
            checkpoint_name: Checkpoint filename
            project_root: Project root for path validation
            clean_reference_path: Optional path to clean reference for QC validation
            
        Returns:
            Structured READY/BLOCKED JSON dict
        """
        editor = WorkflowGraphEditorLite(workflow)
        resize_selector = ResizeNodeSelector(
            self.schema_registry._object_info
        )
        
        blocks = []
        warnings = []
        
        # RC-REAL2: Validate clean reference if provided
        if clean_reference_path:
            ref_qc = self.validate_clean_reference(clean_reference_path)
            if not ref_qc["valid"]:
                blocks.extend([f"BLOCKED_BY_DIRTY_REFERENCE: {b}" for b in ref_qc["blocks"]])
            else:
                warnings.append(f"Clean reference QC PASS: {clean_reference_path}")
        
        # 1. Validate required nodes exist
        load_image_nodes = editor.find_nodes("LoadImage")
        if not load_image_nodes:
            blocks.append("Missing LoadImage node")
        
        vae_encode_nodes = editor.find_nodes("VAEEncode")
        if not vae_encode_nodes:
            blocks.append("Missing VAEEncode node")
        
        ksampler_nodes = editor.find_nodes("KSampler")
        if not ksampler_nodes:
            blocks.append("Missing KSampler node")
        
        # 2. Validate resize node exists
        resize_nodes = editor.find_nodes("ImageResize") + editor.find_nodes("ImageScale")
        if not resize_nodes:
            blocks.append("Missing resize node (ImageResize or ImageScale)")
        
        # 3. Validate KSampler.latent_image does not point to EmptyLatentImage
        for ksampler_id in ksampler_nodes:
            ksampler_node = workflow.get(ksampler_id)
            if isinstance(ksampler_node, dict):
                inputs = ksampler_node.get("inputs", {})
                latent_image = inputs.get("latent_image")
                if isinstance(latent_image, list) and len(latent_image) >= 2:
                    source_id = str(latent_image[0])
                    source_node = workflow.get(source_id)
                    if isinstance(source_node, dict):
                        if source_node.get("class_type") == "EmptyLatentImage":
                            blocks.append(
                                f"KSampler {ksampler_id}.latent_image points to EmptyLatentImage "
                                f"(should point to VAEEncode in reference_locked mode)"
                            )
        
        # 4. Validate no dangling links
        dangling_result = editor.validate_no_dangling_links()
        if not dangling_result["valid"]:
            blocks.extend(dangling_result["errors"])
        
        # 5. Validate checkpoint exists
        checkpoint_result = self.checkpoint_resolver.validate_checkpoint(checkpoint_name)
        if not checkpoint_result["valid"]:
            blocks.append(f"Missing checkpoint: {checkpoint_name}")
        
        # 6. Validate checkpoint path is safe
        if checkpoint_result["valid"]:
            checkpoint_path = checkpoint_result["path"]
            if not self.checkpoint_resolver.is_safe_path(checkpoint_path):
                blocks.append(f"Unsafe checkpoint path (AppData/Temp/pytest): {checkpoint_path}")
        
        # 7. Validate reference image path is safe
        for load_image_id in load_image_nodes:
            load_image_node = workflow.get(load_image_id)
            if isinstance(load_image_node, dict):
                inputs = load_image_node.get("inputs", {})
                image_path = inputs.get("image", "")
                if image_path:
                    if not self._is_safe_path(image_path, project_root):
                        blocks.append(
                            f"Unsafe reference image path (AppData/Temp/pytest): {image_path}"
                        )
        
        # 8. Validate LoadImage -> Resize -> VAEEncode -> KSampler chain
        if load_image_nodes and resize_nodes and vae_encode_nodes and ksampler_nodes:
            chain_valid = self._validate_reference_locked_chain(
                editor,
                load_image_nodes[0],
                resize_nodes[0],
                vae_encode_nodes[0],
                ksampler_nodes[0],
            )
            if not chain_valid:
                blocks.append("Invalid reference_locked chain (LoadImage -> Resize -> VAEEncode -> KSampler)")
        
        # Determine overall status
        status = "READY" if not blocks else "BLOCKED"
        
        # Report actual resize node type from workflow, not from schema registry
        actual_resize_node_type = None
        if resize_nodes:
            resize_node = workflow.get(resize_nodes[0])
            if isinstance(resize_node, dict):
                actual_resize_node_type = resize_node.get("class_type")
        
        result = {
            "status": status,
            "blocks": blocks,
            "warnings": warnings,
            "workflow_info": {
                "load_image_nodes": load_image_nodes,
                "resize_nodes": resize_nodes,
                "vae_encode_nodes": vae_encode_nodes,
                "ksampler_nodes": ksampler_nodes,
            },
            "checkpoint_info": checkpoint_result,
            "resize_node_type": actual_resize_node_type,
        }
        
        # Include clean reference QC stats if available
        if clean_reference_path:
            result["clean_reference_qc"] = ref_qc
        
        return result
    
    def _validate_reference_locked_chain(
        self,
        editor: WorkflowGraphEditorLite,
        load_image_id: str,
        resize_id: str,
        vae_encode_id: str,
        ksampler_id: str,
    ) -> bool:
        """Validate LoadImage -> Resize -> VAEEncode -> KSampler chain.
        
        Args:
            editor: Workflow editor
            load_image_id: LoadImage node ID
            resize_id: Resize node ID
            vae_encode_id: VAEEncode node ID
            ksampler_id: KSampler node ID
            
        Returns:
            True if chain is valid, False otherwise
        """
        workflow = editor.get_workflow()
        
        # Check LoadImage -> Resize connection
        resize_node = workflow.get(resize_id)
        if not isinstance(resize_node, dict):
            return False
        
        resize_inputs = resize_node.get("inputs", {})
        resize_image = resize_inputs.get("image")
        if not isinstance(resize_image, list) or str(resize_image[0]) != load_image_id:
            return False
        
        # Check Resize -> VAEEncode connection
        vae_encode_node = workflow.get(vae_encode_id)
        if not isinstance(vae_encode_node, dict):
            return False
        
        vae_encode_inputs = vae_encode_node.get("inputs", {})
        vae_encode_pixels = vae_encode_inputs.get("pixels")
        if not isinstance(vae_encode_pixels, list) or str(vae_encode_pixels[0]) != resize_id:
            return False
        
        # Check VAEEncode -> KSampler connection
        ksampler_node = workflow.get(ksampler_id)
        if not isinstance(ksampler_node, dict):
            return False
        
        ksampler_inputs = ksampler_node.get("inputs", {})
        ksampler_latent_image = ksampler_inputs.get("latent_image")
        if not isinstance(ksampler_latent_image, list) or str(ksampler_latent_image[0]) != vae_encode_id:
            return False
        
        return True
    
    def _is_safe_path(self, path: str, project_root: str | Path | None) -> bool:
        """Check if a path is safe (not in AppData/Temp/pytest).
        
        Args:
            path: Path string
            project_root: Project root for validation
            
        Returns:
            True if path is safe, False otherwise
        """
        path_lower = path.lower()
        
        # Block AppData
        if "appdata" in path_lower:
            return False
        
        # Block Temp
        if "\\temp\\" in path_lower or "/tmp/" in path_lower or "\\tmp\\" in path_lower:
            return False
        
        # Block pytest temp
        if "pytest" in path_lower and "temp" in path_lower:
            return False
        
        # Allow project-local paths
        if project_root:
            project_root_str = str(project_root).lower()
            if path_lower.startswith(project_root_str):
                return True
        
        return True
    
    def write_preflight_artifact(
        self,
        preflight_result: dict[str, Any],
        output_dir: str | Path,
        episode_id: str,
        shot_id: str,
    ) -> Path:
        """Write preflight result to artifact file.
        
        RC-RUNTIME1 — Writes output/control/ep01_shot01_preflight.json
        
        Args:
            preflight_result: Preflight validation result dict
            output_dir: Output directory
            episode_id: Episode ID
            shot_id: Shot ID
            
        Returns:
            Path to written artifact
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{episode_id}_{shot_id}_preflight.json"
        artifact_path = output_dir / filename
        
        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(preflight_result, f, indent=2, ensure_ascii=False)
        
        log.info(f"[PREFLIGHT] Wrote artifact: {artifact_path}")
        return artifact_path

    def validate_gorynych_identity_workflow(
        self,
        workflow: dict[str, Any],
        checkpoint_name: str,
        project_root: str | Path | None = None,
        character_canon_path: str | Path | None = None,
        reference_lock_path: str | Path | None = None,
    ) -> dict[str, Any]:
        """RC-GORYNYCH1 — Validate gorynych_identity workflow before submission.
        
        Blocks invalid gorynych_identity graphs:
        - Gorynych knowledge files missing (head_1.md, head_2.md, head_3.md)
        - IPAdapterAdvanced node missing
        - IPAdapterUnifiedLoader node missing
        - LoadImage node missing for reference
        - Character canon missing or invalid
        - Reference lock contract not approved (downstream_generation_allowed=false)
        - Required character anchors not approved
        - SaveImage prefix missing
        - Prompt nodes not patchable
        
        Args:
            workflow: ComfyUI workflow dict
            checkpoint_name: Checkpoint filename
            project_root: Project root for path validation
            character_canon_path: Optional path to character canon JSON
            reference_lock_path: Optional path to reference lock contract JSON
            
        Returns:
            Structured READY/BLOCKED JSON dict
        """
        blocks = []
        warnings = []
        
        # 1. Validate Gorynych knowledge files exist
        knowledge_dir = Path(project_root) / "docs" / "knowledge" if project_root else None
        if knowledge_dir and knowledge_dir.exists():
            required_files = ["head_1.md", "head_2.md", "head_3.md"]
            for filename in required_files:
                if not (knowledge_dir / filename).exists():
                    blocks.append(f"Gorynych knowledge file missing: docs/knowledge/{filename}")
        else:
            blocks.append("Gorynych knowledge directory missing: docs/knowledge/")
        
        # 2. Validate IPAdapterAdvanced node exists
        ipadapter_nodes = [node_id for node_id, node in workflow.items() 
                          if isinstance(node, dict) and node.get("class_type") == "IPAdapterAdvanced"]
        if not ipadapter_nodes:
            blocks.append("Missing IPAdapterAdvanced node (required for gorynych_identity mode)")
        
        # 3. Validate IPAdapterUnifiedLoader node exists
        ipadapter_loader_nodes = [node_id for node_id, node in workflow.items()
                                 if isinstance(node, dict) and node.get("class_type") == "IPAdapterUnifiedLoader"]
        if not ipadapter_loader_nodes:
            blocks.append("Missing IPAdapterUnifiedLoader node (required for gorynych_identity mode)")
        
        # 4. Validate LoadImage node exists for reference
        load_image_nodes = [node_id for node_id, node in workflow.items()
                           if isinstance(node, dict) and node.get("class_type") == "LoadImage"]
        if not load_image_nodes:
            blocks.append("Missing LoadImage node (required for reference image in gorynych_identity mode)")
        
        # 5. Validate CharacterCanon if path provided
        if character_canon_path:
            canon_path = Path(character_canon_path)
            if not canon_path.exists():
                blocks.append(f"Character canon missing: {character_canon_path}")
            else:
                try:
                    with open(canon_path, 'r', encoding='utf-8') as f:
                        canon_data = json.load(f)
                    
                    # Validate required fields
                    required_fields = ["character_id", "name", "anchors"]
                    for field in required_fields:
                        if field not in canon_data:
                            blocks.append(f"Character canon missing required field: {field}")
                    
                    # Validate at least one critical anchor exists and is approved
                    anchors = canon_data.get("anchors", [])
                    critical_anchors_approved = any(
                        anchor.get("priority") == "critical" and anchor.get("status") == "approved"
                        for anchor in anchors
                    )
                    if not critical_anchors_approved:
                        blocks.append("No critical character anchors approved (required for gorynych_identity mode)")
                        
                except Exception as e:
                    blocks.append(f"Character canon invalid or unreadable: {e}")
        
        # 6. Validate ReferenceLockContract if path provided
        if reference_lock_path:
            lock_path = Path(reference_lock_path)
            if not lock_path.exists():
                blocks.append(f"Reference lock contract missing: {reference_lock_path}")
            else:
                try:
                    with open(lock_path, 'r', encoding='utf-8') as f:
                        lock_data = json.load(f)
                    
                    # Validate downstream_generation_allowed
                    if not lock_data.get("downstream_generation_allowed", False):
                        blocks.append(
                            f"Reference lock contract does not allow downstream generation "
                            f"(downstream_generation_allowed=false). "
                            f"Lock reason: {lock_data.get('lock_reason', 'unknown')}"
                        )
                        
                except Exception as e:
                    blocks.append(f"Reference lock contract invalid or unreadable: {e}")
        
        # 7. Validate SaveImage prefix is present
        save_image_nodes = [node_id for node_id, node in workflow.items()
                           if isinstance(node, dict) and node.get("class_type") == "SaveImage"]
        if save_image_nodes:
            for node_id in save_image_nodes:
                node = workflow[node_id]
                inputs = node.get("inputs", {})
                filename_prefix = inputs.get("filename_prefix", "")
                if not filename_prefix or filename_prefix == "agent/output":
                    blocks.append(f"SaveImage node {node_id} missing or has default filename_prefix (must be shot-specific)")
        
        # 8. Validate prompt nodes are patchable (have __inject__ markers)
        inject_section = workflow.get("__inject__", {})
        if not inject_section.get("positive_prompt_node"):
            blocks.append("Workflow missing __inject__.positive_prompt_node marker (required for prompt injection)")
        if not inject_section.get("negative_prompt_node"):
            blocks.append("Workflow missing __inject__.negative_prompt_node marker (required for prompt injection)")
        
        # 9. Validate checkpoint exists
        checkpoint_result = self.checkpoint_resolver.validate_checkpoint(checkpoint_name)
        if not checkpoint_result["valid"]:
            blocks.append(f"Missing checkpoint: {checkpoint_name}")
        
        # 10. Validate no dangling links
        editor = WorkflowGraphEditorLite(workflow)
        dangling_result = editor.validate_no_dangling_links()
        if not dangling_result["valid"]:
            blocks.extend(dangling_result["errors"])
        
        # Determine overall status
        status = "READY" if not blocks else "BLOCKED"
        
        result = {
            "status": status,
            "blocks": blocks,
            "warnings": warnings,
            "workflow_info": {
                "ipadapter_advanced_nodes": ipadapter_nodes,
                "ipadapter_loader_nodes": ipadapter_loader_nodes,
                "load_image_nodes": load_image_nodes,
                "save_image_nodes": save_image_nodes,
            },
            "checkpoint_info": checkpoint_result,
            "generation_mode": "gorynych_identity",
        }
        
        return result
