"""Test generation pre-submit validation.

RC-COMBINE-V2-99001-102000

Validates:
- Checkpoint resolution required
- Legacy 512 workflow blocked
- Stub workflow blocked
- All validation checks pass before submit
"""
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"


def _read_json(name: str) -> dict:
    path = CONTROL_DIR / name
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class TestPreSubmitValidation:
    def test_pre_submit_validation_report_exists(self):
        """generation_pre_submit_validation_report.json must exist."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report, "generation_pre_submit_validation_report.json missing"

    def test_all_checks_passed(self):
        """All validation checks must have passed."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("all_checks_passed") is True

    def test_authorization_artifact_present(self):
        """Authorization artifact must have been present at validation time."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("authorization_artifact_present") is True

    def test_operator_authorized(self):
        """Operator must have been authorized."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("operator_authorized") is True

    def test_max_generations_equals_one(self):
        """max_generations must equal 1."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("max_generations_equals_one") is True

    def test_checkpoint_resolved(self):
        """Checkpoint must have been resolved."""
        report = _read_json("generation_pre_submit_validation_report.json")
        checks = report.get("validation_checks", {})
        assert checks.get("checkpoint_resolved") is True

    def test_checkpoint_exists_in_comfyui(self):
        """Checkpoint must exist in ComfyUI."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("checkpoint_exists_in_comfyui") is True

    def test_workflow_contains_ksampler(self):
        """Workflow must contain KSampler."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("workflow_contains_ksampler") is True

    def test_workflow_contains_saveimage(self):
        """Workflow must contain SaveImage."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("workflow_contains_saveimage") is True

    def test_legacy_512_blocked(self):
        """Legacy 512 workflow must be blocked."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("legacy_512_workflow_blocked") is True

    def test_stub_workflow_blocked(self):
        """Stub workflow must be blocked."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("stub_workflow_blocked") is True

    def test_resolution_is_sdxl_compatible(self):
        """Resolution must be SDXL compatible (1024x1024)."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("resolution_is_sdxl_compatible") is True

    def test_no_fake_prompt_id(self):
        """No fake prompt_id at validation time."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("no_fake_prompt_id") is True

    def test_no_fake_assets(self):
        """No fake assets at validation time."""
        report = _read_json("generation_pre_submit_validation_report.json")
        assert report.get("validation_checks", {}).get("no_fake_assets") is True

    def test_execution_contract_exists(self):
        """generation_execution_contract.json must exist."""
        contract = _read_json("generation_execution_contract.json")
        assert contract, "generation_execution_contract.json missing"

    def test_contract_resolved_checkpoint(self):
        """Contract must reference the resolved checkpoint."""
        contract = _read_json("generation_execution_contract.json")
        assert contract.get("resolved_checkpoint") == "sd_xl_base_1.0_0.9vae.safetensors"

    def test_contract_resolution_sdxl(self):
        """Contract must specify SDXL default resolution."""
        contract = _read_json("generation_execution_contract.json")
        rp = contract.get("resolution_policy", {})
        assert rp.get("width") >= 1024 and rp.get("height") >= 1024

    def test_contract_legacy_512_blocked(self):
        """Contract must block legacy 512 workflows."""
        contract = _read_json("generation_execution_contract.json")
        assert contract.get("legacy_512_blocked") is True

    def test_contract_stub_blocked(self):
        """Contract must block stub workflows."""
        contract = _read_json("generation_execution_contract.json")
        assert contract.get("stub_workflow_blocked") is True

    def test_contract_max_generations(self):
        """Contract must specify max_generations=1."""
        contract = _read_json("generation_execution_contract.json")
        assert contract.get("max_generations") == 1
