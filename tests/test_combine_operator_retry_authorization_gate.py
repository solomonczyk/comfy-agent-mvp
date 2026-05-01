import json
import subprocess
import sys

import pytest


class TestCombineOperatorRetryAuthorizationGate:
    """RC-COMBINE-V2-11 — operator retry authorization gate tests."""

    @pytest.fixture
    def project_setup(self, tmp_path):
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(
                {
                    "current_state": "operator_retry_authorization_required",
                    "route_family": "portrait_character_identity",
                },
                f,
            )

        with open(control_dir / "combine_v2_retry_failure_classification.json", "w") as f:
            json.dump({"classification": "visual_quality_failure", "requires_retry": True}, f)
        with open(control_dir / "combine_v2_retry_corrective_plan.json", "w") as f:
            json.dump({"plan_id": "CP-001", "retry_gate_opened": False}, f)
        with open(control_dir / "combine_v2_retry_authorization_request.json", "w") as f:
            json.dump({"request_id": "REQ-001", "status": "pending_authorization"}, f)

        return tmp_path

    def run_cli(self, args):
        cmd = [sys.executable, "-m", "app.cli"] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_cannot_authorize_without_retry_authorization_request(self, project_setup):
        control_dir = project_setup / "output" / "control"
        (control_dir / "combine_v2_retry_authorization_request.json").unlink()

        result = self.run_cli(["combine-authorize-retry", "--project-root", str(project_setup), "--json"])

        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["operator_retry_authorized"] is False
        assert payload["next_allowed_action"] == "operator_retry_authorization_required"
        assert payload["retry_executed"] is False
        assert "retry_authorization_request" in payload["blocked_reason"]

    def test_cannot_authorize_without_corrective_plan(self, project_setup):
        control_dir = project_setup / "output" / "control"
        (control_dir / "combine_v2_retry_corrective_plan.json").unlink()

        result = self.run_cli(["combine-authorize-retry", "--project-root", str(project_setup), "--json"])

        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["operator_retry_authorized"] is False
        assert payload["next_allowed_action"] == "operator_retry_authorization_required"
        assert payload["retry_executed"] is False
        assert "retry_corrective_plan" in payload["blocked_reason"]

    def test_authorization_artifacts_and_boundary_flags_created(self, project_setup):
        control_dir = project_setup / "output" / "control"

        result = self.run_cli(["combine-authorize-retry", "--project-root", str(project_setup), "--json"])
        assert result.returncode == 0

        operator_auth_path = control_dir / "combine_v2_operator_retry_authorization.json"
        retry_gate_decision_path = control_dir / "combine_v2_retry_gate_decision.json"

        # 3. can create operator_retry_authorization artifact
        assert operator_auth_path.exists()
        # 4. creates retry_gate_decision artifact
        assert retry_gate_decision_path.exists()

        with open(operator_auth_path, "r") as f:
            operator_auth = json.load(f)
        with open(retry_gate_decision_path, "r") as f:
            retry_gate_decision = json.load(f)
        payload = json.loads(result.stdout)

        assert operator_auth["operator_retry_authorized"] is True
        assert retry_gate_decision["operator_retry_authorized"] is True
        assert payload["operator_retry_authorization_created"] is True
        assert payload["retry_gate_decision_created"] is True

        # 5. next_allowed_action=generation_authorization_required
        assert payload["next_allowed_action"] == "generation_authorization_required"
        # 6. retry_gate_open=false
        assert retry_gate_decision["retry_gate_open"] is False
        assert payload["retry_gate_open"] is False
        # 7. retry_executed=false
        assert retry_gate_decision["retry_executed"] is False
        assert payload["retry_executed"] is False
        # 8. generation_performed=false
        assert retry_gate_decision["generation_performed"] is False
        assert payload["generation_performed"] is False
        # 9. comfyui_execution=false
        assert retry_gate_decision["comfyui_execution"] is False
        assert payload["comfyui_execution"] is False
        # 10. downstream_executed=false
        assert retry_gate_decision["downstream_executed"] is False
        assert payload["downstream_executed"] is False
        # 11. production_accepted=false
        assert retry_gate_decision["production_accepted"] is False
        assert payload["production_accepted"] is False
