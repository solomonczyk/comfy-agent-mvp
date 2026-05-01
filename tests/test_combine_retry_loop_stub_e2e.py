import json
import subprocess
import sys


def _run_cli(args):
    cmd = [sys.executable, "-m", "app.cli"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    payload = {}
    if result.stdout.strip():
        payload = json.loads(result.stdout)
    return result, payload


def test_combine_retry_loop_stub_e2e(tmp_path):
    project_root = tmp_path
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)

    # Seed baseline state at operator visual review.
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump(
            {
                "current_state": "operator_visual_review",
                "route_family": "portrait_character_identity",
            },
            f,
        )

    # Baseline upstream contracts required for generation authorization refresh.
    with open(control_dir / "combine_v2_asset_gate_decision.json", "w") as f:
        json.dump({"missing_assets": [], "inventory": {"hero": "asset_001"}}, f)
    with open(control_dir / "combine_v2_workflow_contract.json", "w") as f:
        json.dump({"workflow_id": "wf_retry_loop"}, f)
    with open(control_dir / "combine_v2_prompt_contract.json", "w") as f:
        json.dump({"prompts": ["retry prompt"]}, f)
    with open(control_dir / "combine_v2_preflight_contract.json", "w") as f:
        json.dump({"preflight_passed": True}, f)

    # Baseline QA inputs consumed by retry policy stage.
    with open(control_dir / "combine_v2_visual_qa_stub_report.json", "w") as f:
        json.dump({"stage": "visual_qa_required", "retry_aware": True}, f)
    with open(control_dir / "combine_v2_operator_visual_review_packet.json", "w") as f:
        json.dump({"stage": "operator_visual_review", "retry_aware": True}, f)

    # 1) operator_visual_review -> reject
    result, payload = _run_cli(
        [
            "combine-operator-visual-decision",
            "--project-root",
            str(project_root),
            "--decision",
            "reject",
            "--reason",
            "retry_visual_stub_requires_next_correction",
            "--json",
        ]
    )
    assert result.returncode == 0, result.stderr
    assert payload["operator_visual_decision"] == "rejected"
    assert payload["visuals_accepted"] is False
    assert payload["next_allowed_action"] == "retry_correction_required"
    assert payload["retry_authorized"] is False
    assert payload["assembly_allowed"] is False
    assert payload["generation_performed"] is False
    assert payload["comfyui_execution"] is False
    assert payload["downstream_executed"] is False
    assert payload["production_accepted"] is False

    # 2) retry_correction_required refresh
    result, payload = _run_cli(
        [
            "combine-run-stage",
            "--project-root",
            str(project_root),
            "--stage",
            "retry_correction_required",
            "--dry-run",
            "--json",
        ]
    )
    assert result.returncode == 0, result.stderr
    assert payload["metadata"]["retry_authorization_required"] is True
    assert payload["metadata"]["retry_authorized"] is False
    assert payload["next_allowed_action"] == "operator_retry_authorization_required"
    assert payload["generation_performed"] is False
    assert payload["comfyui_execution"] is False
    assert payload["downstream_executed"] is False

    for filename in [
        "combine_v2_retry_failure_classification.json",
        "combine_v2_retry_corrective_plan.json",
        "combine_v2_retry_authorization_request.json",
    ]:
        assert (control_dir / filename).exists()

    # 3) operator_retry_authorization_required
    result, payload = _run_cli(
        ["combine-authorize-retry", "--project-root", str(project_root), "--json"]
    )
    assert result.returncode == 0, result.stderr
    assert payload["operator_retry_authorized"] is True
    assert payload["retry_gate_open"] is False
    assert payload["next_allowed_action"] == "generation_authorization_required"
    assert payload["retry_executed"] is False
    assert payload["generation_performed"] is False
    assert payload["comfyui_execution"] is False
    assert payload["downstream_executed"] is False

    # 4) generation_authorization_required refresh with retry context
    result, payload = _run_cli(
        [
            "combine-run-stage",
            "--project-root",
            str(project_root),
            "--stage",
            "generation_authorization_required",
            "--dry-run",
            "--json",
        ]
    )
    assert result.returncode == 0, result.stderr
    assert payload["next_allowed_action"] == "operator_generation_authorization_required"
    retry_context = payload["metadata"]["combine_v2_generation_payload_stub"]["retry_context"]
    assert retry_context["retry_requested"] is True
    assert retry_context["operator_retry_authorized"] is True
    assert retry_context["retry_gate_open"] is False
    assert retry_context["corrective_plan_applied_to_payload"] is True
    assert retry_context["retry_execution_authorized"] is False

    for filename in [
        "combine_v2_generation_authorization_request.json",
        "combine_v2_generation_authorization_decision.json",
        "combine_v2_generation_payload_stub.json",
    ]:
        assert (control_dir / filename).exists()

    # 5) operator_generation_authorization_required
    result, payload = _run_cli(
        ["combine-authorize-generation", "--project-root", str(project_root), "--json"]
    )
    assert result.returncode == 0, result.stderr
    assert payload["operator_generation_authorized"] is True
    assert payload["generation_gate_open"] is True
    assert payload["next_allowed_action"] == "generate_assets"
    assert payload["retry_context_preserved"] is True
    assert payload["generation_performed"] is False
    assert payload["comfyui_execution"] is False
    assert payload["downstream_executed"] is False

    # 6) generate_assets stub refresh
    result, payload = _run_cli(
        [
            "combine-run-stage",
            "--project-root",
            str(project_root),
            "--stage",
            "generate_assets",
            "--dry-run",
            "--json",
        ]
    )
    assert result.returncode == 0, result.stderr
    assert payload["metadata"]["generation_gate_open"] is True
    assert payload["next_allowed_action"] == "visual_qa_required_stub_pending"
    assert payload["generation_performed"] is False
    assert payload["comfyui_execution"] is False
    assert payload["downstream_executed"] is False
    assert (
        payload["metadata"]["combine_v2_generation_execution_stub_result"]["generated_assets"]
        == []
    )

    for filename in [
        "combine_v2_generation_execution_plan.json",
        "combine_v2_generation_execution_stub_result.json",
        "combine_v2_generation_trace_stub.json",
    ]:
        assert (control_dir / filename).exists()

    # Move through pending gate before visual_qa_required.
    result, _ = _run_cli(
        [
            "combine-run-stage",
            "--project-root",
            str(project_root),
            "--stage",
            "visual_qa_required_stub_pending",
            "--dry-run",
            "--json",
        ]
    )
    assert result.returncode == 0, result.stderr

    # 7) visual_qa_required stub refresh
    result, payload = _run_cli(
        [
            "combine-run-stage",
            "--project-root",
            str(project_root),
            "--stage",
            "visual_qa_required",
            "--dry-run",
            "--json",
        ]
    )
    assert result.returncode == 0, result.stderr
    assert payload["retry_aware"] is True
    assert payload["real_image_analysis"] is False
    assert payload["operator_review_required"] is True
    assert payload["metadata"]["visual_qa_passed"] is False
    assert payload["next_allowed_action"] == "operator_visual_review"
    assert payload["generation_performed"] is False
    assert payload["comfyui_execution"] is False
    assert payload["downstream_executed"] is False

    for filename in [
        "combine_v2_visual_qa_stub_report.json",
        "combine_v2_operator_visual_review_packet.json",
    ]:
        assert (control_dir / filename).exists()

    # Ensure retry context is preserved in operator generation artifact.
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "r") as f:
        operator_generation_auth = json.load(f)
    assert operator_generation_auth["retry_context"]["operator_retry_authorized"] is True
    assert operator_generation_auth["retry_context"]["retry_gate_open"] is False

    # Verify final orchestrator state is back at operator visual review gate.
    result, payload = _run_cli(
        ["combine-status", "--project-root", str(project_root), "--json"]
    )
    assert result.returncode == 0, result.stderr
    assert payload["current_state"] == "visual_qa_required"
    assert payload["next_allowed_action"] == "operator_visual_review"
    assert payload["generation_performed"] is False
    assert payload["comfyui_execution"] is False

    # Ensure root-level control artifacts are not written outside output/control.
    assert not (project_root / "artifact_index.json").exists()
    assert not (project_root / "ledger.json").exists()
    assert not (project_root / "episode_ledger.json").exists()
