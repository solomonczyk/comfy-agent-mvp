"""Workflow registry for managing workflow specifications."""

from pathlib import Path
from typing import Any

from app.workflows.workflow_types import TaskType, WorkflowKind, WorkflowSpec


class WorkflowRegistry:
    """Registry for workflow specifications."""

    def __init__(self, workflows_dir: str | Path) -> None:
        """Initialize registry with workflows directory."""
        self.workflows_dir = Path(workflows_dir)
        self._workflows: dict[str, WorkflowSpec] = {}
        self._task_to_workflow: dict[TaskType, list[str]] = {}
        self._default_for_task: dict[TaskType, str] = {}
        self._initialize_registry()

    def _initialize_registry(self) -> None:
        """Initialize registry with default workflow specifications."""
        # Base path for SDXL template
        sdxl_template = self.workflows_dir / "sdxl_txt2img_template.json"

        # Portrait workflow
        self.register(WorkflowSpec(
            workflow_id="portrait_sdxl_v1",
            task_type=TaskType.PORTRAIT_TXT2IMG,
            workflow_path=str(sdxl_template),
            preset_name="portrait",
            kind=WorkflowKind.TXT2IMG,
            description="SDXL portrait generation with cinematic lighting",
            required_inputs=["prompt"],
            supports_retry=True,
            supports_judging=True,
            default_rewrite_mode="fallback",
            implemented=True,
        ))

        # Cinematic workflow
        self.register(WorkflowSpec(
            workflow_id="cinematic_sdxl_v1",
            task_type=TaskType.CINEMATIC_TXT2IMG,
            workflow_path=str(sdxl_template),
            preset_name="cinematic",
            kind=WorkflowKind.TXT2IMG,
            description="SDXL cinematic wide-shot generation",
            required_inputs=["prompt"],
            supports_retry=True,
            supports_judging=True,
            default_rewrite_mode="fallback",
            implemented=True,
        ))

        # Product workflow
        self.register(WorkflowSpec(
            workflow_id="product_sdxl_v1",
            task_type=TaskType.PRODUCT_TXT2IMG,
            workflow_path=str(sdxl_template),
            preset_name="product",
            kind=WorkflowKind.TXT2IMG,
            description="SDXL product photography generation",
            required_inputs=["prompt"],
            supports_retry=True,
            supports_judging=True,
            default_rewrite_mode="fallback",
            implemented=True,
        ))

        # Fashion workflow (using cinematic preset as base)
        self.register(WorkflowSpec(
            workflow_id="fashion_sdxl_v1",
            task_type=TaskType.FASHION_TXT2IMG,
            workflow_path=str(sdxl_template),
            preset_name="cinematic",  # Reuse cinematic preset for fashion
            kind=WorkflowKind.TXT2IMG,
            description="SDXL fashion editorial generation",
            required_inputs=["prompt"],
            supports_retry=True,
            supports_judging=True,
            default_rewrite_mode="fallback",
            implemented=True,
        ))

        # Upscale workflow (implemented)
        upscale_template = self.workflows_dir / "upscale_template.json"
        self.register(WorkflowSpec(
            workflow_id="upscale_v1",
            task_type=TaskType.UPSCALE,
            workflow_path=str(upscale_template),
            preset_name="portrait",
            kind=WorkflowKind.UPSCALE,
            description="Image upscaling workflow with SDXL",
            required_inputs=["input_image"],
            supports_retry=True,
            supports_judging=True,
            default_rewrite_mode="raw",
            implemented=True,
        ))

        # Inpaint face workflow (implemented)
        inpaint_template = self.workflows_dir / "sdxl_inpaint_face_template.json"
        self.register(WorkflowSpec(
            workflow_id="inpaint_face_v1",
            task_type=TaskType.INPAINT_FACE,
            workflow_path=str(inpaint_template),
            preset_name="inpaint",
            kind=WorkflowKind.INPAINT,
            description="Face inpainting workflow with SDXL",
            required_inputs=["image", "mask"],
            supports_retry=True,
            supports_judging=True,
            default_rewrite_mode="raw",
            implemented=True,
        ))

        # Img2img workflow (implemented)
        img2img_template = self.workflows_dir / "img2img_simple_template.json"
        self.register(WorkflowSpec(
            workflow_id="img2img_v1",
            task_type=TaskType.IMG2IMG,
            workflow_path=str(img2img_template),
            preset_name="portrait",  # Use existing preset, edit workflows use raw mode
            kind=WorkflowKind.IMG2IMG,
            description="Image-to-image workflow with SDXL (simple template)",
            required_inputs=["input_image"],
            supports_retry=True,
            supports_judging=True,
            default_rewrite_mode="raw",  # Edit workflows use raw mode
            implemented=True,
        ))

        # Img2img batch workflow (MK-6J bounded generation)
        img2img_batch_template = self.workflows_dir / "img2img_batch_template.json"
        self.register(WorkflowSpec(
            workflow_id="img2img_batch_v1",
            task_type=TaskType.IMG2IMG,
            workflow_path=str(img2img_batch_template),
            preset_name="portrait",
            kind=WorkflowKind.IMG2IMG,
            description="MK-6J: Batch img2img workflow generating 3 frames per submission",
            required_inputs=["input_image"],
            supports_retry=False,
            supports_judging=False,
            default_rewrite_mode="raw",
            implemented=True,
        ))

    def register(self, spec: WorkflowSpec) -> None:
        """Register a workflow specification."""
        self._workflows[spec.workflow_id] = spec

        # Update task to workflow mapping
        if spec.task_type not in self._task_to_workflow:
            self._task_to_workflow[spec.task_type] = []
        self._task_to_workflow[spec.task_type].append(spec.workflow_id)

        # Set as default for task type if it's the first or if it's implemented
        if spec.task_type not in self._default_for_task or spec.implemented:
            self._default_for_task[spec.task_type] = spec.workflow_id

    def list_workflows(self) -> list[WorkflowSpec]:
        """List all registered workflows."""
        return list(self._workflows.values())

    def get_workflow(self, workflow_id: str) -> WorkflowSpec | None:
        """Get workflow specification by ID."""
        return self._workflows.get(workflow_id)

    def get_workflows_for_task(self, task_type: TaskType) -> list[WorkflowSpec]:
        """Get all workflows for a given task type."""
        workflow_ids = self._task_to_workflow.get(task_type, [])
        return [self._workflows[wid] for wid in workflow_ids if wid in self._workflows]

    def get_default_for_task(self, task_type: TaskType) -> WorkflowSpec | None:
        """Get default workflow for a given task type."""
        workflow_id = self._default_for_task.get(task_type)
        if workflow_id:
            return self._workflows.get(workflow_id)
        return None

    def get_implemented_workflows(self) -> list[WorkflowSpec]:
        """Get only implemented workflows."""
        return [spec for spec in self._workflows.values() if spec.implemented]
