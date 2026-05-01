import hashlib
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
    if result.stdout.strip().startswith("{"):
        payload = json.loads(result.stdout)
    return result, payload


def _seed_real_generation_inputs(project_root):
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    with open(control_dir / "artifact_index.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "current_state": "operator_real_generation_authorization_required",
                "route_family": "portrait_character_identity",
            },
            f,
        )
    with open(control_dir / "combine_v2_real_generation_payload.json", "w", encoding="utf-8") as f:
        json.dump({"workflow": {"1": {"class_type": "SaveImage", "inputs": {}}}}, f)
    with open(
        control_dir / "combine_v2_real_generation_execution_contract.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump({"workflow_payload": {"1": {"class_type": "SaveImage", "inputs": {}}}}, f)
    with open(
        control_dir / "combine_v2_real_generation_preflight_report.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump({"status": "ready", "next_allowed_action": "real_generation_payload_review"}, f)
    return control_dir


def test_combine_real_generation_gate_and_submit(tmp_path):
    class _Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path == "/prompt":
                body = json.dumps({"prompt_id": "pid-1"}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def do_GET(self):
            if self.path == "/history/pid-1":
                body = json.dumps(
                    {
                        "pid-1": {
                            "status": {"status_str": "success"},
                            "outputs": {
                                "7": {
                                    "images": [
                                        {
                                            "filename": "mock_frame_001.png",
                                            "subfolder": "",
                                            "type": "output",
                                        }
                                    ]
                                }
                            },
                        }
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path == "/queue":
                body = json.dumps({"queue_running": [], "queue_pending": []}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            return

    project_root = tmp_path
    control_dir = _seed_real_generation_inputs(project_root)

    # 1) Approval blocked without explicit flag.
    blocked_result, blocked_payload = _run_cli(
        [
            "combine-authorize-real-generation",
            "--project-root",
            str(project_root),
            "--json",
        ]
    )
    assert blocked_result.returncode == 1
    assert blocked_payload["status"] == "blocked"
    assert blocked_payload["explicit_confirmation_received"] is False

    # 2-4) Approval + gate created and open with explicit confirmation.
    approve_result, approve_payload = _run_cli(
        [
            "combine-authorize-real-generation",
            "--project-root",
            str(project_root),
            "--confirm-real-comfyui-execution",
            "--json",
        ]
    )
    assert approve_result.returncode == 0
    assert approve_payload["operator_real_generation_authorized"] is True
    assert approve_payload["real_generation_gate_open"] is True
    assert (control_dir / "combine_v2_operator_real_generation_approval.json").exists()
    assert (control_dir / "combine_v2_real_generation_gate_decision.json").exists()

    # 5) Submit without --execute remains dry-run.
    dry_result, dry_payload = _run_cli(
        [
            "combine-real-generate-assets",
            "--project-root",
            str(project_root),
            "--json",
        ]
    )
    assert dry_result.returncode == 0
    assert dry_payload["status"] == "authorization_required"
    assert dry_payload["generation_performed"] is False

    # 6) Submit without approval is blocked.
    no_approval_project = tmp_path / "no_approval"
    no_approval_control = _seed_real_generation_inputs(no_approval_project)
    assert not (no_approval_control / "combine_v2_operator_real_generation_approval.json").exists()
    no_approval_result, no_approval_payload = _run_cli(
        [
            "combine-real-generate-assets",
            "--project-root",
            str(no_approval_project),
            "--execute",
            "--max-generations",
            "1",
            "--json",
        ]
    )
    assert no_approval_result.returncode == 1
    assert no_approval_payload["status"] == "blocked"

    # 7) max_generations > 1 blocked.
    max_result, max_payload = _run_cli(
        [
            "combine-real-generate-assets",
            "--project-root",
            str(project_root),
            "--execute",
            "--max-generations",
            "2",
            "--json",
        ]
    )
    assert max_result.returncode == 1
    assert max_payload["status"] == "blocked"

    # 8) preflight not ready blocked.
    with open(
        control_dir / "combine_v2_real_generation_preflight_report.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump({"status": "blocked"}, f)
    preflight_result, preflight_payload = _run_cli(
        [
            "combine-real-generate-assets",
            "--project-root",
            str(project_root),
            "--execute",
            "--max-generations",
            "1",
            "--json",
        ]
    )
    assert preflight_result.returncode == 1
    assert preflight_payload["status"] == "blocked"
    with open(
        control_dir / "combine_v2_real_generation_preflight_report.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump({"status": "ready"}, f)

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    workflow_template = project_root / "workflows" / "template.json"
    workflow_template.parent.mkdir(parents=True, exist_ok=True)
    workflow_template.write_text(json.dumps({"template": True}), encoding="utf-8")
    workflow_before = hashlib.sha256(workflow_template.read_bytes()).hexdigest()

    try:
        execute_result, execute_payload = _run_cli(
            [
                "combine-real-generate-assets",
                "--project-root",
                str(project_root),
                "--execute",
                "--max-generations",
                "1",
                "--json",
            ],
            env={"COMFY_BASE_URL": base_url},
        )
        assert execute_result.returncode == 0

        # 9-13) submit request and all result artifacts created.
        assert (control_dir / "combine_v2_real_submit_request.json").exists()
        assert (control_dir / "combine_v2_real_generation_result.json").exists()
        assert (control_dir / "combine_v2_real_generation_observed_settings.json").exists()
        assert (control_dir / "combine_v2_real_generation_outputs_manifest.json").exists()
        assert (control_dir / "combine_v2_real_generation_trace.json").exists()
        assert execute_payload["generation_attempts"] == 1
        assert execute_payload["generated_assets_count"] >= 0

        # 14-18) safety flags and forced QA gate.
        assert execute_payload["downstream_executed"] is False
        assert execute_payload["production_accepted"] is False
        assert execute_payload["visual_qa_executed"] is False
        assert execute_payload["next_allowed_action"] == "visual_qa_required"

        # 19) root-level artifact_index/ledger not created.
        assert not (project_root / "artifact_index.json").exists()
        assert not (project_root / "episode_ledger.json").exists()

        # 20) workflow templates are not mutated.
        workflow_after = hashlib.sha256(workflow_template.read_bytes()).hexdigest()
        assert workflow_before == workflow_after
    finally:
        server.shutdown()
        server.server_close()
