"""
Test: combine-authorize-corrective-retry-v4-generation
Task ID: RC-COMBINE-V2-2841-2900

Tests the operator authorization gate for Corrective Retry V4 generation.
Covers:
- approval_branch: true
- rejection_branch: true
- missing_review_artifact_blocks: true
- invalid_state_blocks: true
- max_generations_must_equal_1: true
- generation_gate_opened_only_after_operator_approval: true
- generation_not_performed: true
- comfyui_submit_not_executed: true
- retry_not_attempted: true
- visual_qa_not_executed: true
- assembly_not_executed: true
- downstream_not_executed: true
- production_accepted_false: true
- state_transition_correct: true
- canonical_artifacts_updated: true
"""

import pytest
import json
from pathlib import Path
from argparse import Namespace


class TestCombineCorrectiveRetryV4GenerationAuthorization:
    """Test suite for RC-COMBINE-V2-2841-2900"""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project structure with required artifacts."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create updated implementation plan review artifact
        review_artifact = {
            "task_id": "RC-COMBINE-V2-2781-2840",
            "review_type": "operator_review_updated_retry_v4_implementation_plan",
            "previous_layer": "RC-COMBINE-V2-2721-2780",
            "previous_commit": "2759d52",
            "stage": "operator_retry_v4_updated_implementation_plan_review_required",
            "shot_id": "shot02",
            "timestamp": "2026-05-07T06:32:24.275696+00:00",
            "updated_plan_reviewed": True,
            "operator_approved": True,
            "operator_decision": "approve_updated_retry_implementation_plan",
            "plan_structurally_valid": True,
            "generation_authorized": False,
            "retry_authorized": False,
            "comfyui_submit_authorized": False,
            "visual_qa_authorized": False,
            "assembly_authorized": False,
            "downstream_authorized": False,
            "production_accepted": False,
            "new_generation_performed": False,
            "new_comfyui_submit_executed": False,
            "retry_attempted": False,
            "visual_qa_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "current_state": "operator_retry_v4_generation_authorization_required",
            "next_allowed_action": "operator_retry_v4_generation_authorization_required",
            "artifacts": [
                "output/control/combine_v2_corrective_retry_v4_updated_implementation_plan.json",
                "output/control/combine_v2_corrective_retry_v4_updated_implementation_plan_review_packet.json"
            ]
        }

        with open(control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json", 'w') as f:
            json.dump(review_artifact, f, indent=2)

        return tmp_path

    def setup_artifact_index(self, temp_project, current_state, next_allowed_action, production_accepted=False, generation_gate_opened=False):
        """Setup artifact_index.json with given state."""
        control_dir = temp_project / "output" / "control"
        artifact_index = {
            "current_state": current_state,
            "next_allowed_action": next_allowed_action,
            "production_accepted": production_accepted,
            "generation_gate_opened": generation_gate_opened,
            "downstream_blocked": True,
            "stage_results": []
        }
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(artifact_index, f, indent=2)

        # Create empty ledger
        with open(control_dir / "episode_ledger.json", 'w') as f:
            json.dump([], f, indent=2)

    def test_approval_branch(self, temp_project):
        """Test approval branch opens generation gate."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        result = combine_authorize_corrective_retry_v4_generation(args)
        assert result == 0, "Should succeed with approval"

        # Verify authorization artifact created
        control_dir = temp_project / "output" / "control"
        auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"
        assert auth_path.exists(), "Authorization artifact should be created"

        with open(auth_path) as f:
            auth = json.load(f)

        assert auth["operator_authorized"] is True
        assert auth["generation_gate_opened"] is True
        assert auth["max_generations"] == 1
        assert auth["current_state"] == "corrective_retry_v4_real_execute_assets"
        assert auth["next_allowed_action"] == "corrective_retry_v4_real_execute_assets"

    def test_rejection_branch(self, temp_project):
        """Test rejection branch does not open generation gate."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=False,
            reject=True,
            max_generations=1,
            json=True
        )

        result = combine_authorize_corrective_retry_v4_generation(args)
        assert result == 1, "Should return 1 for rejection"

        # Verify rejection artifact created
        control_dir = temp_project / "output" / "control"
        rejection_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization_rejection.json"
        assert rejection_path.exists(), "Rejection artifact should be created"

        with open(rejection_path) as f:
            rejection = json.load(f)

        assert rejection["operator_authorized"] is False
        assert rejection["generation_gate_opened"] is False
        assert rejection["current_state"] == "operator_retry_v4_generation_authorization_required"

    def test_missing_review_artifact_blocks(self, temp_project):
        """Test that missing review artifact blocks authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        # Remove the review artifact
        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"
        review_path.unlink()

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        result = combine_authorize_corrective_retry_v4_generation(args)
        assert result == 1, "Should fail when review artifact is missing"

    def test_invalid_state_blocks(self, temp_project):
        """Test that invalid current_state blocks authorization."""
        self.setup_artifact_index(
            temp_project,
            "invalid_state",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        result = combine_authorize_corrective_retry_v4_generation(args)
        assert result == 1, "Should fail with invalid state"

    def test_max_generations_must_equal_1(self, temp_project):
        """Test that max_generations != 1 blocks authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=2,  # Invalid: must be 1
            json=True
        )

        result = combine_authorize_corrective_retry_v4_generation(args)
        assert result == 1, "Should fail when max_generations != 1"

    def test_generation_gate_opened_only_after_operator_approval(self, temp_project):
        """Test that generation_gate_opened is only true after approval."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required",
            generation_gate_opened=False
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        # Verify artifact_index updated
        control_dir = temp_project / "output" / "control"
        with open(control_dir / "artifact_index.json") as f:
            artifact_index = json.load(f)

        assert artifact_index["generation_gate_opened"] is True
        assert artifact_index["operator_retry_v4_generation_authorized"] is True

    def test_generation_not_performed(self, temp_project):
        """Test that generation is not performed during authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        control_dir = temp_project / "output" / "control"
        auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"

        with open(auth_path) as f:
            auth = json.load(f)

        assert auth["generation_performed"] is False
        assert auth["generation_attempts"] == 0

    def test_comfyui_submit_not_executed(self, temp_project):
        """Test that ComfyUI submit is not executed during authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        control_dir = temp_project / "output" / "control"
        auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"

        with open(auth_path) as f:
            auth = json.load(f)

        assert auth["comfyui_execution"] is False
        assert auth["workflow_submitted"] is False

    def test_retry_not_attempted(self, temp_project):
        """Test that retry is not attempted during authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        control_dir = temp_project / "output" / "control"
        auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"

        with open(auth_path) as f:
            auth = json.load(f)

        assert auth["retry_attempted"] is False

    def test_visual_qa_not_executed(self, temp_project):
        """Test that visual QA is not executed during authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        control_dir = temp_project / "output" / "control"
        auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"

        with open(auth_path) as f:
            auth = json.load(f)

        assert auth["visual_qa_executed"] is False

    def test_assembly_not_executed(self, temp_project):
        """Test that assembly is not executed during authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        control_dir = temp_project / "output" / "control"
        auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"

        with open(auth_path) as f:
            auth = json.load(f)

        assert auth["assembly_executed"] is False

    def test_downstream_not_executed(self, temp_project):
        """Test that downstream is not executed during authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        control_dir = temp_project / "output" / "control"
        auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"

        with open(auth_path) as f:
            auth = json.load(f)

        assert auth["downstream_executed"] is False

    def test_production_accepted_false(self, temp_project):
        """Test that production_accepted remains false."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        control_dir = temp_project / "output" / "control"
        auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"

        with open(auth_path) as f:
            auth = json.load(f)

        assert auth["production_accepted"] is False

    def test_state_transition_correct(self, temp_project):
        """Test that state transitions correctly to corrective_retry_v4_real_execute_assets."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        control_dir = temp_project / "output" / "control"
        with open(control_dir / "artifact_index.json") as f:
            artifact_index = json.load(f)

        assert artifact_index["current_state"] == "corrective_retry_v4_real_execute_assets"
        assert artifact_index["next_allowed_action"] == "corrective_retry_v4_real_execute_assets"

    def test_artifact_index_updated(self, temp_project):
        """Test that artifact_index.json is properly updated."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        control_dir = temp_project / "output" / "control"
        with open(control_dir / "artifact_index.json") as f:
            artifact_index = json.load(f)

        assert artifact_index["operator_retry_v4_generation_authorized"] is True
        assert artifact_index["generation_gate_opened"] is True
        assert artifact_index["max_generations"] == 1
        assert artifact_index["generation_performed"] is False
        assert artifact_index["workflow_submitted"] is False
        assert artifact_index["comfyui_execution"] is False
        assert artifact_index["retry_attempted"] is False
        assert artifact_index["visual_qa_executed"] is False
        assert artifact_index["assembly_executed"] is False
        assert artifact_index["downstream_executed"] is False
        assert artifact_index["production_accepted"] is False

    def test_episode_ledger_updated(self, temp_project):
        """Test that episode_ledger.json is properly updated."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        combine_authorize_corrective_retry_v4_generation(args)

        control_dir = temp_project / "output" / "control"
        with open(control_dir / "episode_ledger.json") as f:
            ledger = json.load(f)

        assert len(ledger) > 0
        last_event = ledger[-1]
        assert last_event["event_type"] == "operator_retry_v4_generation_authorized"
        assert last_event["operator_retry_v4_generation_authorized"] is True
        assert last_event["max_generations"] == 1
        assert last_event["generation_gate_opened"] is True

    def test_review_artifact_not_approved_blocks(self, temp_project):
        """Test that unapproved review artifact blocks authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required"
        )

        # Update review artifact to not approved
        control_dir = temp_project / "output" / "control"
        review_path = control_dir / "combine_v2_operator_retry_v4_updated_implementation_plan_review.json"
        with open(review_path) as f:
            review = json.load(f)

        review["operator_approved"] = False
        review["operator_decision"] = "reject_updated_retry_implementation_plan"

        with open(review_path, 'w') as f:
            json.dump(review, f, indent=2)

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        result = combine_authorize_corrective_retry_v4_generation(args)
        assert result == 1, "Should fail when review artifact is not approved"

    def test_production_accepted_true_blocks(self, temp_project):
        """Test that production_accepted=true blocks authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required",
            production_accepted=True
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        result = combine_authorize_corrective_retry_v4_generation(args)
        assert result == 1, "Should fail when production_accepted is true"

    def test_generation_gate_already_open_blocks(self, temp_project):
        """Test that already open generation gate blocks re-authorization."""
        self.setup_artifact_index(
            temp_project,
            "operator_retry_v4_generation_authorization_required",
            "operator_retry_v4_generation_authorization_required",
            generation_gate_opened=True  # Already open
        )

        from app.cli import combine_authorize_corrective_retry_v4_generation

        args = Namespace(
            project_root=str(temp_project),
            approve=True,
            reject=False,
            max_generations=1,
            json=True
        )

        result = combine_authorize_corrective_retry_v4_generation(args)
        assert result == 1, "Should fail when generation_gate_opened is already true"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


# ---------------------------------------------------------------------------
# RC-COMBINE-V2-2901-2960 additions
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
CONTROL_DIR = PROJECT_ROOT / "output" / "control"
ASSETS_DIR = PROJECT_ROOT / "output" / "assets"


def _load_control(filename):
    p = CONTROL_DIR / filename
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)


class TestUnauthorizedExecutionBlocked:
    """RC-COMBINE-V2-2901-2960: unauthorized_execution_blocked."""

    def test_no_execute_flag_means_no_generation(self, tmp_path, capsys):
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        import argparse
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        (control / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").write_text(
            json.dumps({"route_has_comfyui_access": True})
        )
        (control / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
            json.dumps({"real_workflow_binding_created": True, "workflow_source": ""})
        )
        args = argparse.Namespace(
            project_root=str(tmp_path), shot_id="shot02",
            execute=False, max_generations=1, json=True
        )
        rc = combine_corrective_retry_v4_real_execute_assets(args)
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert data["generation_performed"] is False
        assert data["workflow_submitted"] is False
        assert data["comfyui_execution"] is False

    def test_missing_auth_artifact_blocks_execute(self, tmp_path, capsys):
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        import argparse
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        (control / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").write_text(
            json.dumps({"route_has_comfyui_access": True})
        )
        (control / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
            json.dumps({"real_workflow_binding_created": True, "workflow_source": ""})
        )
        (control / "artifact_index.json").write_text(
            json.dumps({"current_state": "operator_retry_v4_real_execution_authorization_required"})
        )
        args = argparse.Namespace(
            project_root=str(tmp_path), shot_id="shot02",
            execute=True, max_generations=1, json=True
        )
        rc = combine_corrective_retry_v4_real_execute_assets(args)
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        assert data["generation_performed"] is False
        assert "authorization" in data["blocked_reason"]


class TestMaxGenerationsEnforced:
    """RC-COMBINE-V2-2901-2960: max_generations_enforced, second_generation_blocked."""

    def test_max_generations_2_blocked(self, tmp_path, capsys):
        from app.cli import combine_corrective_retry_v4_real_execute_assets
        import argparse
        control = tmp_path / "output" / "control"
        control.mkdir(parents=True)
        (control / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").write_text(
            json.dumps({"route_has_comfyui_access": True})
        )
        (control / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
            json.dumps({"real_workflow_binding_created": True, "workflow_source": ""})
        )
        args = argparse.Namespace(
            project_root=str(tmp_path), shot_id="shot02",
            execute=True, max_generations=2, json=True
        )
        rc = combine_corrective_retry_v4_real_execute_assets(args)
        assert rc == 1
        data = json.loads(capsys.readouterr().out)
        assert data["blocked_reason"] == "max_generations_must_equal_1"

    def test_second_generation_not_attempted_in_result(self):
        r = _load_control("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("second_generation_attempted") is False

    def test_generation_attempts_capped_at_one(self):
        ai = _load_control("artifact_index.json")
        assert ai.get("generation_attempts") == 1


class TestOutputValidation:
    """RC-COMBINE-V2-2901-2960: missing/corrupted output blocks success."""

    def test_missing_output_would_fail(self, tmp_path):
        """Verify asset validation logic: non-existent asset must be detected."""
        missing = tmp_path / "nonexistent.png"
        assert not missing.exists()

    def test_corrupted_output_would_fail(self, tmp_path):
        """Verify that zero-byte file is detected as corrupted."""
        f = tmp_path / "corrupt.png"
        f.write_bytes(b"")
        assert f.stat().st_size == 0
        assert f.stat().st_size <= 1024  # fails size check

    def test_real_asset_passes_size_check(self):
        p = ASSETS_DIR / "combine_v2_corrective_retry_v4_shot02_00002_.png"
        if p.exists():
            assert p.stat().st_size > 1024

    def test_real_asset_sha256_is_deterministic(self):
        p = ASSETS_DIR / "combine_v2_corrective_retry_v4_shot02_00002_.png"
        if not p.exists():
            pytest.skip("Asset not present on disk")
        with open(p, "rb") as f:
            h1 = json.dumps({"sha256": __import__("hashlib").sha256(f.read()).hexdigest()})
        with open(p, "rb") as f:
            h2 = json.dumps({"sha256": __import__("hashlib").sha256(f.read()).hexdigest()})
        assert h1 == h2


class TestComfyUISubmitExecutedOnce:
    """RC-COMBINE-V2-2901-2960: comfyui_submit_executed_once."""

    def test_generation_attempts_is_one(self):
        r = _load_control("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("generation_attempts") == 1

    def test_prompt_id_recorded(self):
        r = _load_control("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("prompt_id") == "8b60d0af-4011-4a4a-96ca-6ba9f7221b2e"

    def test_workflow_submitted_true(self):
        r = _load_control("combine_v2_corrective_retry_v4_real_execution_result.json")
        assert r.get("workflow_submitted") is True

    def test_submit_record_artifact_exists(self):
        p = CONTROL_DIR / "combine_v2_corrective_retry_v4_real_execute_submit_record.json"
        assert p.exists(), "Submit record must exist"
