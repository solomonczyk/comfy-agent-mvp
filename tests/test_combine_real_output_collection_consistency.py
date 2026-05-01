import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from PIL import Image


def _png_1x1_bytes():
    image = Image.new("RGB", (1, 1), color=(255, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _run_cli(args, env=None):
    cmd = [sys.executable, "-m", "app.cli"] + args
    run_env = None
    if env:
        run_env = {}
        run_env.update(env)
        import os
        merged = os.environ.copy()
        merged.update(run_env)
        run_env = merged
    result = subprocess.run(cmd, capture_output=True, text=True, env=run_env)
    payload = {}
    if result.stdout.strip().startswith("{"):
        payload = json.loads(result.stdout)
    return result, payload


def _seed_real_generation_inputs(project_root):
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    with open(control_dir / "artifact_index.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "current_state": "operator_real_generation_approved",
                "route_family": "portrait_character_identity",
            },
            handle,
        )
    with open(control_dir / "combine_v2_operator_real_generation_approval.json", "w", encoding="utf-8") as handle:
        json.dump({"operator_real_generation_authorized": True}, handle)
    with open(control_dir / "combine_v2_real_generation_gate_decision.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "real_generation_gate_open": True,
                "next_allowed_action": "real_generate_assets",
            },
            handle,
        )
    with open(control_dir / "combine_v2_real_generation_payload.json", "w", encoding="utf-8") as handle:
        json.dump({"workflow": {"1": {"class_type": "SaveImage", "inputs": {}}}}, handle)
    with open(control_dir / "combine_v2_real_generation_execution_contract.json", "w", encoding="utf-8") as handle:
        json.dump({"workflow_payload": {"1": {"class_type": "SaveImage", "inputs": {}}}}, handle)
    with open(control_dir / "combine_v2_real_generation_preflight_report.json", "w", encoding="utf-8") as handle:
        json.dump({"status": "ready"}, handle)
    return control_dir


class _ZeroOutputsHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/prompt":
            body = json.dumps({"prompt_id": "pid-zero"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        if self.path == "/history/pid-zero":
            body = json.dumps(
                {"pid-zero": {"status": {"status_str": "success"}, "outputs": {}}}
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


class _OneOutputHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/prompt":
            body = json.dumps({"prompt_id": "pid-one"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/history/pid-one":
            body = json.dumps(
                {
                    "pid-one": {
                        "status": {"status_str": "success"},
                        "outputs": {
                            "10": {
                                "images": [
                                    {
                                        "filename": "collected_001.png",
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
        if parsed.path == "/view":
            params = parse_qs(parsed.query)
            filename = params.get("filename", [""])[0]
            if filename == "collected_001.png":
                body = _png_1x1_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()
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


def _run_real_generate(project_root, base_url):
    return _run_cli(
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


def test_zero_assets_fails_and_blocks_visual_qa(tmp_path):
    _seed_real_generation_inputs(tmp_path)
    server = HTTPServer(("127.0.0.1", 0), _ZeroOutputsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        _, payload = _run_real_generate(tmp_path, f"http://127.0.0.1:{server.server_port}")
        assert payload["status"] != "completed"
        assert payload["status"] == "failed"
        assert payload["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"
        assert payload["generated_assets_count"] == 0
        assert payload["next_allowed_action"] != "visual_qa_required"
        assert payload["next_allowed_action"] == "real_generation_result_review_required"
        assert payload["visual_qa_executed"] is False
        assert payload["retry_attempted"] is False
        assert payload["downstream_executed"] is False
        assert payload["production_accepted"] is False
    finally:
        server.shutdown()
        server.server_close()


def test_manifest_contains_collected_readable_asset_fields(tmp_path):
    control_dir = _seed_real_generation_inputs(tmp_path)
    server = HTTPServer(("127.0.0.1", 0), _OneOutputHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        _, payload = _run_real_generate(tmp_path, f"http://127.0.0.1:{server.server_port}")
        assert payload["status"] == "completed"
        assert payload["generated_assets_count"] == 1
        manifest = json.loads(
            (control_dir / "combine_v2_real_generation_outputs_manifest.json").read_text(encoding="utf-8")
        )
        assert manifest["generated_assets_count"] == 1
        asset = manifest["generated_assets"][0]
        assert asset["exists"] is True
        assert asset["readable"] is True
        assert asset["width"] == 1
        assert asset["height"] == 1
        assert len(asset["sha256"]) == 64
    finally:
        server.shutdown()
        server.server_close()
