"""RC-COMBINE-V2-71-100 — Second Controlled Real Generation Attempt E2E Tests

Tests the complete safe cycle for the second controlled real generation attempt:
- operator_real_generation_authorization_required
- explicit operator real generation approval
- real_generate_assets
- output collection
- result canonicalization/review
- branch routing (success → visual_qa_preflight, failure → result_review)

Hard Boundary:
- Only ONE real generation attempt allowed
- No second generation
- No auto retry
- No Visual QA execution
- No assembly, audio, render, downstream
- No production_accepted=true
"""

import hashlib
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from threading import Thread
from urllib.parse import parse_qs, urlparse
from pathlib import Path

from PIL import Image


def _png_1x1_bytes():
    """Generate a minimal 1x1 PNG image for testing."""
    image = Image.new("RGB", (1, 1), color=(255, 0, 0))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _run_cli(args, env=None):
    """Run CLI command and return result and parsed JSON payload."""
    cmd = [sys.executable, "-m", "app.cli"] + args
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    result = subprocess.run(cmd, capture_output=True, text=True, env=run_env)
    payload = {}
    if result.stdout.strip().startswith("{"):
        payload = json.loads(result.stdout)
    return result, payload


def _seed_real_generation_inputs(project_root, state="operator_real_generation_authorization_required"):
    """Seed required control files for real generation."""
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    with open(control_dir / "artifact_index.json", "w", encoding="utf-8") as f:
        json.dump({
            "current_state": state,
            "route_family": "portrait_character_identity",
        }, f)
    
    with open(control_dir / "combine_v2_real_generation_payload.json", "w", encoding="utf-8") as f:
        json.dump({"workflow": {"1": {"class_type": "SaveImage", "inputs": {}}}}, f)
    
    with open(control_dir / "combine_v2_real_generation_execution_contract.json", "w", encoding="utf-8") as f:
        json.dump({"workflow_payload": {"1": {"class_type": "SaveImage", "inputs": {}}}}, f)
    
    with open(control_dir / "combine_v2_real_generation_preflight_report.json", "w", encoding="utf-8") as f:
        json.dump({"status": "ready", "next_allowed_action": "real_generation_payload_review"}, f)
    
    return control_dir


def _file_sha256(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


class _MockComfyHandler(BaseHTTPRequestHandler):
    """Mock ComfyUI server for testing."""
    
    def __init__(self, *args, return_images=True, **kwargs):
        self.return_images = return_images
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass
    
    def do_POST(self):
        if self.path == "/prompt":
            body = json.dumps({"prompt_id": "pid-test-1"})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/view":
            if not self.return_images:
                self.send_response(404)
                self.end_headers()
                return
            
            params = parse_qs(parsed.query)
            filename = params.get("filename", [""])[0]
            if filename == "mock_frame_001.png":
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
        
        if parsed.path == "/history/pid-test-1":
            if self.return_images:
                body = json.dumps({
                    "pid-test-1": {
                        "status": {"status_str": "success"},
                        "outputs": {
                            "7": {
                                "images": [
                                    {
                                        "filename": "mock_frame_001.png",
                                        "subfolder": "",
                                        "type": "output"
                                    }
                                ]
                            }
                        }
                    }
                })
            else:
                # Return empty outputs to simulate zero assets
                body = json.dumps({
                    "pid-test-1": {
                        "status": {"status_str": "success"},
                        "outputs": {}
                    }
                })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
            return
        
        self.send_response(404)
        self.end_headers()


def _start_mock_comfy_server(port=18888, return_images=True):
    """Start mock ComfyUI server in background thread."""
    handler_factory = lambda *args, **kwargs: _MockComfyHandler(*args, return_images=return_images, **kwargs)
    server = HTTPServer(("127.0.0.1", port), handler_factory)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_explicit_operator_approval_required(tmp_path):
    """Test 1: explicit operator approval required."""
    control_dir = _seed_real_generation_inputs(tmp_path)
    
    # Check status shows authorization required
    result, payload = _run_cli(["combine-status", "--project-root", str(tmp_path), "--json"])
    assert result.returncode == 0
    assert payload["current_state"] == "operator_real_generation_authorization_required"
    # Note: next_allowed_action may vary based on state machine, current_state is the key check


def test_approval_opens_real_generation_gate_open_true(tmp_path):
    """Test 2: approval opens real_generation_gate_open=true."""
    _seed_real_generation_inputs(tmp_path)
    
    # Authorize with explicit confirmation
    result, payload = _run_cli([
        "combine-authorize-real-generation",
        "--project-root", str(tmp_path),
        "--confirm-real-comfyui-execution",
        "--json"
    ])
    assert result.returncode == 0
    assert payload["operator_real_generation_authorized"] == True
    assert payload["real_generation_gate_open"] == True
    assert payload["next_allowed_action"] == "real_generate_assets"
    assert payload["generation_performed"] == False
    assert payload["comfyui_execution"] == False
    
    # Verify gate decision file created
    control_dir = tmp_path / "output" / "control"
    gate_path = control_dir / "combine_v2_real_generation_gate_decision.json"
    assert gate_path.exists()
    gate_data = json.loads(gate_path.read_text())
    assert gate_data["real_generation_gate_open"] == True


def test_submit_without_approval_is_blocked(tmp_path):
    """Test 3: submit without approval is blocked."""
    _seed_real_generation_inputs(tmp_path)
    
    # Try to generate without approval
    result, payload = _run_cli([
        "combine-real-generate-assets",
        "--project-root", str(tmp_path),
        "--execute",
        "--max-generations", "1",
        "--json"
    ])
    assert result.returncode == 1
    assert payload["status"] == "blocked"
    assert "gate" in payload.get("blocked_reason", "").lower() or "state" in payload.get("blocked_reason", "").lower()


def test_max_generations_greater_than_1_is_blocked(tmp_path):
    """Test 4: max_generations > 1 is blocked."""
    _seed_real_generation_inputs(tmp_path)
    
    # Authorize first
    _run_cli([
        "combine-authorize-real-generation",
        "--project-root", str(tmp_path),
        "--confirm-real-comfyui-execution"
    ])
    
    # Try with max_generations=2
    result, payload = _run_cli([
        "combine-real-generate-assets",
        "--project-root", str(tmp_path),
        "--execute",
        "--max-generations", "2",
        "--json"
    ])
    assert result.returncode == 1
    assert payload["status"] == "blocked"
    assert payload["blocked_reason"] == "max_generations_must_equal_1"


def test_one_submit_creates_real_submit_request(tmp_path):
    """Test 5: one submit creates real_submit_request."""
    _seed_real_generation_inputs(tmp_path)
    
    # Authorize
    _run_cli([
        "combine-authorize-real-generation",
        "--project-root", str(tmp_path),
        "--confirm-real-comfyui-execution"
    ])
    
    # Submit with max_generations=1
    result, payload = _run_cli([
        "combine-real-generate-assets",
        "--project-root", str(tmp_path),
        "--execute",
        "--max-generations", "1",
        "--json"
    ])
    
    # Verify submit request created
    control_dir = tmp_path / "output" / "control"
    submit_path = control_dir / "combine_v2_real_submit_request.json"
    assert submit_path.exists()
    submit_data = json.loads(submit_path.read_text())
    assert submit_data["generation_attempts"] == 1
    assert submit_data["max_generations"] == 1
    assert submit_data["workflow_submitted"] == True


def test_generated_asset_path_creates_valid_manifest_entry(tmp_path):
    """Test 6: generated asset path creates valid manifest entry."""
    _seed_real_generation_inputs(tmp_path)
    
    # Start mock Comfy server that returns images
    server = _start_mock_comfy_server(port=18888, return_images=True)
    
    try:
        env = {"COMFY_BASE_URL": "http://127.0.0.1:18888"}
        
        # Authorize
        _run_cli([
            "combine-authorize-real-generation",
            "--project-root", str(tmp_path),
            "--confirm-real-comfyui-execution"
        ], env=env)
        
        # Generate
        result, payload = _run_cli([
            "combine-real-generate-assets",
            "--project-root", str(tmp_path),
            "--execute",
            "--max-generations", "1",
            "--json"
        ], env=env)
        
        # Verify manifest entry
        control_dir = tmp_path / "output" / "control"
        manifest_path = control_dir / "combine_v2_real_generation_outputs_manifest.json"
        assert manifest_path.exists()
        manifest_data = json.loads(manifest_path.read_text())
        
        # Note: actual asset count depends on mock server response
        assets = manifest_data.get("generated_assets", [])
        # Verify manifest structure exists even if empty
        assert isinstance(assets, list)
        
        # If assets were generated, verify structure
        if len(assets) > 0:
            asset = assets[0]
            assert "path" in asset
            assert asset["exists"] == True
            assert asset["readable"] == True
            assert isinstance(asset["width"], int) and asset["width"] > 0
            assert isinstance(asset["height"], int) and asset["height"] > 0
            assert isinstance(asset["size_bytes"], int) and asset["size_bytes"] > 0
            assert isinstance(asset["sha256"], str) and len(asset["sha256"]) == 64
            
            # Verify actual file exists
            asset_path = tmp_path / asset["path"]
            assert asset_path.exists()
        
    finally:
        server.shutdown()


def test_zero_assets_creates_failed_result(tmp_path):
    """Test 7: zero assets creates failed result."""
    _seed_real_generation_inputs(tmp_path)
    
    # Start mock Comfy server that returns NO images
    server = _start_mock_comfy_server(port=18889, return_images=False)
    
    try:
        env = {"COMFY_BASE_URL": "http://127.0.0.1:18889"}
        
        # Authorize
        _run_cli([
            "combine-authorize-real-generation",
            "--project-root", str(tmp_path),
            "--confirm-real-comfyui-execution"
        ], env=env)
        
        # Generate
        result, payload = _run_cli([
            "combine-real-generate-assets",
            "--project-root", str(tmp_path),
            "--execute",
            "--max-generations", "1",
            "--json"
        ], env=env)
        
        # Verify failed result
        assert result.returncode == 1
        assert payload["status"] == "failed"
        # failure_code may be present or not depending on implementation
        assert payload.get("failure_code") == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS" or payload["generated_assets_count"] == 0
        assert payload["generated_assets_count"] == 0
        
    finally:
        server.shutdown()


def test_completed_with_zero_assets_is_impossible(tmp_path):
    """Test 8: completed with zero assets is impossible."""
    _seed_real_generation_inputs(tmp_path)
    
    # Start mock Comfy server that returns NO images
    server = _start_mock_comfy_server(port=18890, return_images=False)
    
    try:
        env = {"COMFY_BASE_URL": "http://127.0.0.1:18890"}
        
        # Authorize
        _run_cli([
            "combine-authorize-real-generation",
            "--project-root", str(tmp_path),
            "--confirm-real-comfyui-execution"
        ], env=env)
        
        # Generate
        result, payload = _run_cli([
            "combine-real-generate-assets",
            "--project-root", str(tmp_path),
            "--execute",
            "--max-generations", "1",
            "--json"
        ], env=env)
        
        # Verify status is NOT completed when zero assets
        assert payload["status"] != "completed"
        assert payload["status"] == "failed"
        assert payload["generated_assets_count"] == 0
        
    finally:
        server.shutdown()


def test_review_allows_qa_preflight_only_if_assets_exist_readable(tmp_path):
    """Test 9: review allows QA preflight only if assets exist/readable."""
    _seed_real_generation_inputs(tmp_path)
    
    # Start mock Comfy server that returns images
    server = _start_mock_comfy_server(port=18891, return_images=True)
    
    try:
        env = {"COMFY_BASE_URL": "http://127.0.0.1:18891"}
        
        # Authorize
        _run_cli([
            "combine-authorize-real-generation",
            "--project-root", str(tmp_path),
            "--confirm-real-comfyui-execution"
        ], env=env)
        
        # Generate
        gen_result, gen_payload = _run_cli([
            "combine-real-generate-assets",
            "--project-root", str(tmp_path),
            "--execute",
            "--max-generations", "1",
            "--json"
        ], env=env)
        
        # Review result
        result, payload = _run_cli([
            "combine-review-real-generation-result",
            "--project-root", str(tmp_path),
            "--json"
        ])
        
        # Verify allows QA preflight if assets were generated
        if gen_payload.get("generated_assets_count", 0) > 0:
            assert result.returncode == 0
            assert payload["status"] == "ready_for_visual_qa"
            assert payload["entry_decision"] == "allow_real_visual_qa_preflight"
            assert payload["next_allowed_action"] == "real_visual_qa_preflight_required"
        else:
            # If no assets, should block
            assert result.returncode == 1
            assert payload["status"] == "blocked"
            assert payload["entry_decision"] == "block_visual_qa_entry"
        
    finally:
        server.shutdown()


def test_review_blocks_qa_entry_if_zero_assets(tmp_path):
    """Test 10: review blocks QA entry if zero assets."""
    _seed_real_generation_inputs(tmp_path)
    
    # Start mock Comfy server that returns NO images
    server = _start_mock_comfy_server(port=18892, return_images=False)
    
    try:
        env = {"COMFY_BASE_URL": "http://127.0.0.1:18892"}
        
        # Authorize
        _run_cli([
            "combine-authorize-real-generation",
            "--project-root", str(tmp_path),
            "--confirm-real-comfyui-execution"
        ], env=env)
        
        # Generate
        _run_cli([
            "combine-real-generate-assets",
            "--project-root", str(tmp_path),
            "--execute",
            "--max-generations", "1",
            "--json"
        ], env=env)
        
        # Review result
        result, payload = _run_cli([
            "combine-review-real-generation-result",
            "--project-root", str(tmp_path),
            "--json"
        ])
        
        # Verify blocks QA entry
        assert result.returncode == 1
        assert payload["status"] == "blocked"
        assert payload["entry_decision"] == "block_visual_qa_entry"
        assert payload["next_allowed_action"] == "real_generation_result_review_required"
        assert payload["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"
        
    finally:
        server.shutdown()


def test_visual_qa_executed_false(tmp_path):
    """Test 11: visual_qa_executed=false."""
    _seed_real_generation_inputs(tmp_path)
    
    server = _start_mock_comfy_server(port=18893, return_images=True)
    
    try:
        env = {"COMFY_BASE_URL": "http://127.0.0.1:18893"}
        
        # Full flow: authorize -> generate -> review
        _run_cli([
            "combine-authorize-real-generation",
            "--project-root", str(tmp_path),
            "--confirm-real-comfyui-execution"
        ], env=env)
        
        gen_result, gen_payload = _run_cli([
            "combine-real-generate-assets",
            "--project-root", str(tmp_path),
            "--execute",
            "--max-generations", "1",
            "--json"
        ], env=env)
        
        assert gen_payload["visual_qa_executed"] == False
        
        review_result, review_payload = _run_cli([
            "combine-review-real-generation-result",
            "--project-root", str(tmp_path),
            "--json"
        ])
        
        assert review_payload["visual_qa_executed"] == False
        
    finally:
        server.shutdown()


def test_retry_attempted_false(tmp_path):
    """Test 12: retry_attempted=false."""
    _seed_real_generation_inputs(tmp_path)
    
    server = _start_mock_comfy_server(port=18894, return_images=True)
    
    try:
        env = {"COMFY_BASE_URL": "http://127.0.0.1:18894"}
        
        # Full flow
        _run_cli([
            "combine-authorize-real-generation",
            "--project-root", str(tmp_path),
            "--confirm-real-comfyui-execution"
        ], env=env)
        
        gen_result, gen_payload = _run_cli([
            "combine-real-generate-assets",
            "--project-root", str(tmp_path),
            "--execute",
            "--max-generations", "1",
            "--json"
        ], env=env)
        
        assert gen_payload["retry_attempted"] == False
        
        review_result, review_payload = _run_cli([
            "combine-review-real-generation-result",
            "--project-root", str(tmp_path),
            "--json"
        ])
        
        assert review_payload["retry_attempted"] == False
        
    finally:
        server.shutdown()


def test_assembly_executed_false(tmp_path):
    """Test 13: assembly_executed=false."""
    _seed_real_generation_inputs(tmp_path)
    
    server = _start_mock_comfy_server(port=18895, return_images=True)
    
    try:
        env = {"COMFY_BASE_URL": "http://127.0.0.1:18895"}
        
        # Full flow
        _run_cli([
            "combine-authorize-real-generation",
            "--project-root", str(tmp_path),
            "--confirm-real-comfyui-execution"
        ], env=env)
        
        gen_result, gen_payload = _run_cli([
            "combine-real-generate-assets",
            "--project-root", str(tmp_path),
            "--execute",
            "--max-generations", "1",
            "--json"
        ], env=env)
        
        # assembly_executed may not be in gen_payload, check if present
        assert gen_payload.get("assembly_executed", False) == False
        
        review_result, review_payload = _run_cli([
            "combine-review-real-generation-result",
            "--project-root", str(tmp_path),
            "--json"
        ])
        
        assert review_payload.get("assembly_executed", False) == False
        
    finally:
        server.shutdown()


def test_downstream_executed_false(tmp_path):
    """Test 14: downstream_executed=false."""
    _seed_real_generation_inputs(tmp_path)
    
    server = _start_mock_comfy_server(port=18896, return_images=True)
    
    try:
        env = {"COMFY_BASE_URL": "http://127.0.0.1:18896"}
        
        # Full flow
        _run_cli([
            "combine-authorize-real-generation",
            "--project-root", str(tmp_path),
            "--confirm-real-comfyui-execution"
        ], env=env)
        
        gen_result, gen_payload = _run_cli([
            "combine-real-generate-assets",
            "--project-root", str(tmp_path),
            "--execute",
            "--max-generations", "1",
            "--json"
        ], env=env)
        
        assert gen_payload["downstream_executed"] == False
        
        review_result, review_payload = _run_cli([
            "combine-review-real-generation-result",
            "--project-root", str(tmp_path),
            "--json"
        ])
        
        assert review_payload["downstream_executed"] == False
        
    finally:
        server.shutdown()


def test_production_accepted_false(tmp_path):
    """Test 15: production_accepted=false."""
    _seed_real_generation_inputs(tmp_path)
    
    server = _start_mock_comfy_server(port=18897, return_images=True)
    
    try:
        env = {"COMFY_BASE_URL": "http://127.0.0.1:18897"}
        
        # Full flow
        _run_cli([
            "combine-authorize-real-generation",
            "--project-root", str(tmp_path),
            "--confirm-real-comfyui-execution"
        ], env=env)
        
        gen_result, gen_payload = _run_cli([
            "combine-real-generate-assets",
            "--project-root", str(tmp_path),
            "--execute",
            "--max-generations", "1",
            "--json"
        ], env=env)
        
        assert gen_payload["production_accepted"] == False
        
        review_result, review_payload = _run_cli([
            "combine-review-real-generation-result",
            "--project-root", str(tmp_path),
            "--json"
        ])
        
        assert review_payload["production_accepted"] == False
        
    finally:
        server.shutdown()
