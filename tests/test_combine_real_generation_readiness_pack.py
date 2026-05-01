import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


def _run_cli(args, env=None):
    cmd = [sys.executable, "-m", "app.cli"] + args
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    result = subprocess.run(cmd, capture_output=True, text=True, env=run_env)
    payload = {}
    if result.returncode == 0 and result.stdout.strip().startswith("{"):
        payload = json.loads(result.stdout)
    return result, payload


def _seed_required_artifacts(control_dir):
    with open(control_dir / "artifact_index.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "current_state": "operator_visual_review",
                "route_family": "portrait_character_identity",
            },
            f,
        )
    with open(control_dir / "combine_v2_generation_payload_stub.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "retry_context": {
                    "retry_requested": True,
                    "operator_retry_authorized": True,
                    "corrective_plan_applied_to_payload": True,
                }
            },
            f,
        )
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w", encoding="utf-8") as f:
        json.dump({"execution_strategy": "stub_only"}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w", encoding="utf-8") as f:
        json.dump({"trace": "stub"}, f)
    with open(control_dir / "combine_v2_workflow_contract.json", "w", encoding="utf-8") as f:
        json.dump({"workflow_id": "wf-ready"}, f)
    with open(control_dir / "combine_v2_prompt_contract.json", "w", encoding="utf-8") as f:
        json.dump({"prompts": ["p1"]}, f)
    with open(control_dir / "combine_v2_asset_requirements_contract.json", "w", encoding="utf-8") as f:
        json.dump({"asset_requirements": {"characters": ["hero"]}}, f)
    with open(control_dir / "combine_v2_preflight_contract.json", "w", encoding="utf-8") as f:
        json.dump({"preflight_passed": True}, f)
    with open(control_dir / "combine_v2_retry_authorization_request.json", "w", encoding="utf-8") as f:
        json.dump({"retry_requested": True}, f)


def test_combine_real_generation_readiness_pack_blocked_when_comfy_unreachable(tmp_path):
    project_root = tmp_path
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    _seed_required_artifacts(control_dir)

    result, payload = _run_cli(
        [
            "combine-prepare-real-generation",
            "--project-root",
            str(project_root),
            "--dry-run",
            "--json",
        ],
        env={"COMFY_BASE_URL": "http://127.0.0.1:65530"},
    )
    assert result.returncode == 0, result.stderr
    assert payload["status"] == "blocked"
    assert payload["generation_performed"] is False
    assert payload["comfyui_execution"] is False
    assert payload["workflow_submitted"] is False
    assert payload["downstream_executed"] is False
    assert payload["production_accepted"] is False
    assert payload["next_allowed_action"] == "real_generation_preflight_required"

    preflight_report_path = control_dir / "combine_v2_real_generation_preflight_report.json"
    assert preflight_report_path.exists()
    with open(preflight_report_path, "r", encoding="utf-8") as f:
        preflight_report = json.load(f)
    assert preflight_report["status"] == "blocked"
    assert preflight_report["blocked_reason"] == "COMFYUI_UNREACHABLE"
    assert preflight_report["generation_submitted"] is False


def test_combine_real_generation_readiness_pack_ready_flow(tmp_path):
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/object_info":
                payload = {
                    "CheckpointLoaderSimple": {"input": {}},
                    "CLIPTextEncode": {"input": {}},
                    "KSampler": {"input": {}},
                    "VAEDecode": {"input": {}},
                }
                encoded = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            return

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    project_root = tmp_path
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    _seed_required_artifacts(control_dir)

    try:
        result, payload = _run_cli(
            [
                "combine-prepare-real-generation",
                "--project-root",
                str(project_root),
                "--dry-run",
                "--json",
            ],
            env={"COMFY_BASE_URL": base_url},
        )
        assert result.returncode == 0, result.stderr
        assert payload["status"] == "ok"
        assert payload["next_allowed_action"] == "operator_real_generation_authorization_required"
        assert payload["generation_performed"] is False
        assert payload["comfyui_execution"] is False
        assert payload["workflow_submitted"] is False
        assert payload["downstream_executed"] is False
        assert payload["production_accepted"] is False
        assert "real_generation_readiness_required" in payload["stages_executed"]
        assert "real_generation_preflight_required" in payload["stages_executed"]
        assert "real_generation_payload_review" in payload["stages_executed"]

        required_paths = [
            control_dir / "combine_v2_real_generation_readiness_report.json",
            control_dir / "combine_v2_real_generation_preflight_report.json",
            control_dir / "combine_v2_real_generation_payload.json",
            control_dir / "combine_v2_real_generation_execution_contract.json",
            control_dir / "combine_v2_operator_real_generation_authorization_request.json",
        ]
        for path in required_paths:
            assert path.exists(), f"Missing artifact: {path.name}"

        with open(control_dir / "combine_v2_real_generation_readiness_report.json", "r", encoding="utf-8") as f:
            readiness = json.load(f)
        assert readiness["status"] in {"ready_for_preflight", "blocked"}
        assert readiness["generation_performed"] is False
        assert readiness["comfyui_execution"] is False
        assert readiness["downstream_executed"] is False
        assert readiness["production_accepted"] is False

        with open(control_dir / "combine_v2_real_generation_preflight_report.json", "r", encoding="utf-8") as f:
            preflight = json.load(f)
        assert preflight["status"] == "ready"
        assert preflight["comfyui_reachable"] is True
        assert preflight["object_info_available"] is True
        assert preflight["required_nodes_checked"] is True
        assert preflight["generation_submitted"] is False
        assert preflight["comfyui_execution"] is False
        assert preflight["workflow_mutated"] is False
        assert preflight["downstream_executed"] is False

        with open(control_dir / "combine_v2_real_generation_payload.json", "r", encoding="utf-8") as f:
            real_payload = json.load(f)
        assert real_payload["retry_context"]["retry_requested"] is True
        assert real_payload["retry_context"]["operator_retry_authorized"] is True
        assert real_payload["retry_context"]["corrective_plan_applied_to_payload"] is True
        assert real_payload["generation_performed"] is False
        assert real_payload["comfyui_execution"] is False

        with open(control_dir / "combine_v2_real_generation_execution_contract.json", "r", encoding="utf-8") as f:
            execution_contract = json.load(f)
        assert execution_contract["workflow_submitted"] is False
        assert execution_contract["generation_performed"] is False
        assert execution_contract["comfyui_execution"] is False
        assert execution_contract["downstream_executed"] is False
        assert execution_contract["production_accepted"] is False

        with open(
            control_dir / "combine_v2_operator_real_generation_authorization_request.json",
            "r",
            encoding="utf-8",
        ) as f:
            authorization_request = json.load(f)
        assert authorization_request["current_layer_executes_comfyui"] is False
        assert authorization_request["generation_performed"] is False
        assert authorization_request["comfyui_execution"] is False
        assert authorization_request["downstream_executed"] is False
        assert authorization_request["production_accepted"] is False

        # Artifacts remain under output/control only.
        assert not (project_root / "artifact_index.json").exists()
        assert not (project_root / "episode_ledger.json").exists()
    finally:
        server.shutdown()
        server.server_close()
