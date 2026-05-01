import json
import subprocess
import sys


class TestCombineRetryAwareGenerationGate:
    """RC-COMBINE-V2-13 — retry-aware operator generation authorization gate."""

    def run_cli(self, args):
        cmd = [sys.executable, "-m", "app.cli"] + args
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_retry_aware_payload_is_loaded_and_preserved(self, tmp_path):
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        retry_context = {
            "retry_requested": True,
            "operator_retry_authorized": True,
            "retry_gate_open": False,
            "corrective_plan_applied_to_payload": True,
            "retry_execution_authorized": False,
        }

        with open(control_dir / "combine_v2_generation_authorization_request.json", "w") as f:
            json.dump(
                {
                    "generation_authorization_ready": True,
                    "authorization_required": True,
                    "retry_requested": True,
                },
                f,
            )
        with open(control_dir / "combine_v2_generation_authorization_decision.json", "w") as f:
            json.dump(
                {
                    "authorization_required": True,
                    "generation_authorized": False,
                    "next_allowed_action": "operator_generation_authorization_required",
                },
                f,
            )
        with open(control_dir / "combine_v2_generation_payload_stub.json", "w") as f:
            json.dump(
                {
                    "payload_type": "generation_contract_v2",
                    "retry_context": retry_context,
                },
                f,
            )
        with open(control_dir / "combine_v2_asset_gate_decision.json", "w") as f:
            json.dump({"missing_assets": []}, f)
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump({"current_state": "generation_authorization_required"}, f)

        result = self.run_cli(["combine-authorize-generation", "--project-root", str(tmp_path), "--json"])
        assert result.returncode == 0, result.stderr

        payload = json.loads(result.stdout)
        assert payload["status"] == "ok"
        assert payload["generation_gate_open"] is True
        assert payload["next_allowed_action"] == "generate_assets"
        assert payload["retry_context_preserved"] is True
        assert payload["generation_performed"] is False
        assert payload["comfyui_execution"] is False
        assert payload["downstream_executed"] is False
        assert payload["production_accepted"] is False

        auth_artifact_path = control_dir / "combine_v2_operator_generation_authorization.json"
        assert auth_artifact_path.exists()
        with open(auth_artifact_path, "r") as f:
            auth_artifact = json.load(f)

        assert auth_artifact["operator_generation_authorized"] is True
        assert auth_artifact["generation_gate_open"] is True
        assert auth_artifact["next_allowed_action"] == "generate_assets"
        assert auth_artifact["retry_context"] == retry_context
        assert auth_artifact["retry_context"]["retry_gate_open"] is False
        assert auth_artifact["generation_performed"] is False
        assert auth_artifact["comfyui_execution"] is False
        assert auth_artifact["downstream_executed"] is False
        assert auth_artifact["production_accepted"] is False

        # V2-13 scope: gate is opened for the next controlled stage only.
        # No retry execution or generate execution side effects should be created.
        assert not (control_dir / "combine_v2_retry_generate_execution_result.json").exists()
        assert not (control_dir / "combine_v2_generation_execution_stub_result.json").exists()

    def test_requires_retry_aware_generation_artifacts(self, tmp_path):
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        with open(control_dir / "combine_v2_generation_authorization_decision.json", "w") as f:
            json.dump({"authorization_required": True, "generation_authorized": False}, f)
        with open(control_dir / "combine_v2_asset_gate_decision.json", "w") as f:
            json.dump({"missing_assets": []}, f)

        result = self.run_cli(["combine-authorize-generation", "--project-root", str(tmp_path), "--json"])
        assert result.returncode == 1
        payload = json.loads(result.stdout)
        assert payload["status"] == "error"
        assert "combine_v2_generation_authorization_request.json" in payload["message"]
        assert "combine_v2_generation_payload_stub.json" in payload["message"]
