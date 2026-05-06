"""Tests for combine-corrective-retry-v4-create-non-stub-execution-route.

RC-COMBINE-V2-2121-2180 — Non-stub execution route binding for corrective retry V4.
"""

import json
import argparse
import pytest
from pathlib import Path


def _make_args(project_root, shot_id="shot02", json_out=True):
    return argparse.Namespace(
        project_root=str(project_root),
        shot_id=shot_id,
        json=json_out,
    )


def _setup_project(tmp_path, current_state="corrective_retry_v4_submit_path_fix_required",
                   next_allowed="corrective_retry_v4_non_stub_execution_route_required"):
    """Create minimal project structure."""
    project_root = tmp_path / "project"
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    artifact_index = {
        "current_state": current_state,
        "next_allowed_action": next_allowed,
        "route_family": "custom",
    }
    (control_dir / "artifact_index.json").write_text(json.dumps(artifact_index))

    ledger = []
    (control_dir / "episode_ledger.json").write_text(json.dumps(ledger))

    implementation_package = {
        "source_asset": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png",
        "failure_basis": "CORRUPTED_V3_ASSET_STUB_GENERATION",
    }
    (control_dir / "combine_v2_corrective_retry_v4_implementation_package.json").write_text(
        json.dumps(implementation_package)
    )

    return project_root, control_dir


class TestNonStubExecutionRouteCreated:
    def test_route_binding_artifact_created(self, tmp_path):
        """Route binding artifact must be written to control dir."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(tmp_path)
        result = combine_corrective_retry_v4_create_non_stub_execution_route(
            _make_args(project_root))
        assert result == 0
        route_path = control_dir / "combine_v2_corrective_retry_v4_non_stub_execution_route.json"
        assert route_path.exists(), "Route binding artifact must exist"

    def test_route_binding_fields(self, tmp_path):
        """Route binding must have all required proof fields."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(tmp_path)
        combine_corrective_retry_v4_create_non_stub_execution_route(_make_args(project_root))

        route = json.loads(
            (control_dir / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").read_text()
        )
        assert route["non_stub_execution_route_created"] is True
        assert route["stub_layer_execute_block_preserved"] is True
        assert route["real_execution_adapter_identified"] is True
        assert route["route_has_comfyui_access"] is True
        assert route["dry_run_false_allowed_only_in_real_adapter"] is True
        assert route["fake_comfyui_execution_forbidden"] is True
        assert route["next_allowed_action"] == "operator_retry_v4_real_execution_authorization_required"
        assert route["generation_performed"] is False
        assert route["comfyui_execution"] is False
        assert route["workflow_submitted"] is False
        assert route["production_accepted"] is False

    def test_real_adapter_identified_as_combine_real_generate_assets(self, tmp_path):
        """Real adapter must be combine-real-generate-assets using ComfyClient."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(tmp_path)
        combine_corrective_retry_v4_create_non_stub_execution_route(_make_args(project_root))

        route = json.loads(
            (control_dir / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").read_text()
        )
        assert route["real_execution_adapter_command"] == "combine-real-generate-assets"
        assert route["real_execution_adapter_uses_comfy_client"] is True
        assert route["stub_layer_has_comfyui_access"] is False

    def test_stub_layer_execute_blocked_in_dry_run_enforcement(self, tmp_path):
        """dry_run_enforcement must document stub layer as execute_blocked_always."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(tmp_path)
        combine_corrective_retry_v4_create_non_stub_execution_route(_make_args(project_root))

        route = json.loads(
            (control_dir / "combine_v2_corrective_retry_v4_non_stub_execution_route.json").read_text()
        )
        enforcement = route["dry_run_enforcement"]
        assert enforcement["stub_layer_combine_corrective_retry_v4_generate_assets"] == "execute_blocked_always"
        assert "execute_allowed_with_operator_authorization" in enforcement[
            "real_adapter_combine_real_generate_assets"]


class TestArtifactIndexUpdated:
    def test_current_state_set_to_non_stub_route_required(self, tmp_path):
        """artifact_index current_state must advance to corrective_retry_v4_non_stub_execution_route_required."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(tmp_path)
        combine_corrective_retry_v4_create_non_stub_execution_route(_make_args(project_root))

        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index["current_state"] == "corrective_retry_v4_non_stub_execution_route_required"

    def test_next_allowed_action_set_to_operator_authorization(self, tmp_path):
        """artifact_index next_allowed_action must be operator_retry_v4_real_execution_authorization_required."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(tmp_path)
        combine_corrective_retry_v4_create_non_stub_execution_route(_make_args(project_root))

        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index["next_allowed_action"] == "operator_retry_v4_real_execution_authorization_required"

    def test_execution_flags_remain_false(self, tmp_path):
        """All execution flags must remain False after route creation."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(tmp_path)
        combine_corrective_retry_v4_create_non_stub_execution_route(_make_args(project_root))

        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index["generation_performed"] is False
        assert index["comfyui_execution"] is False
        assert index["workflow_submitted"] is False
        assert index["production_accepted"] is False


class TestLedgerUpdated:
    def test_ledger_event_appended(self, tmp_path):
        """Episode ledger must receive corrective_retry_v4_non_stub_execution_route_created event."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(tmp_path)
        combine_corrective_retry_v4_create_non_stub_execution_route(_make_args(project_root))

        ledger = json.loads((control_dir / "episode_ledger.json").read_text())
        assert isinstance(ledger, list)
        last = ledger[-1]
        assert last["event_type"] == "corrective_retry_v4_non_stub_execution_route_created"
        assert last["non_stub_execution_route_created"] is True
        assert last["generation_performed"] is False
        assert last["next_allowed_action"] == "operator_retry_v4_real_execution_authorization_required"


class TestStatePreconditionEnforced:
    def test_wrong_state_returns_error(self, tmp_path):
        """Must return exit code 1 if current_state does not permit this step."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(
            tmp_path,
            current_state="visual_qa_required",
            next_allowed="operator_visual_review",
        )
        result = combine_corrective_retry_v4_create_non_stub_execution_route(
            _make_args(project_root))
        assert result == 1

    def test_allowed_from_non_stub_route_required_state(self, tmp_path):
        """Must succeed when current_state is already corrective_retry_v4_non_stub_execution_route_required."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(
            tmp_path,
            current_state="corrective_retry_v4_non_stub_execution_route_required",
            next_allowed="corrective_retry_v4_non_stub_execution_route_required",
        )
        result = combine_corrective_retry_v4_create_non_stub_execution_route(
            _make_args(project_root))
        assert result == 0

    def test_allowed_from_submit_path_fix_with_correct_next_allowed(self, tmp_path):
        """Must succeed when current_state is corrective_retry_v4_submit_path_fix_required."""
        from app.cli import combine_corrective_retry_v4_create_non_stub_execution_route
        project_root, control_dir = _setup_project(
            tmp_path,
            current_state="corrective_retry_v4_submit_path_fix_required",
            next_allowed="corrective_retry_v4_non_stub_execution_route_required",
        )
        result = combine_corrective_retry_v4_create_non_stub_execution_route(
            _make_args(project_root))
        assert result == 0


class TestStateMachineRegistration:
    def test_new_state_is_valid(self):
        """operator_retry_v4_real_execution_authorization_required must be in STATES."""
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.is_valid_state("operator_retry_v4_real_execution_authorization_required")

    def test_transition_from_non_stub_route_required(self):
        """Must allow transition from non_stub_execution_route_required to operator_retry_v4_real_execution_authorization_required."""
        from app.orchestrator.state_machine import CombineStateMachine
        assert CombineStateMachine.can_transition(
            "corrective_retry_v4_non_stub_execution_route_required",
            "operator_retry_v4_real_execution_authorization_required",
        )

    def test_no_direct_transition_to_real_generate_assets(self):
        """Must not allow jumping directly from non_stub_route to real_generate_assets."""
        from app.orchestrator.state_machine import CombineStateMachine
        assert not CombineStateMachine.can_transition(
            "corrective_retry_v4_non_stub_execution_route_required",
            "real_generate_assets",
        )
