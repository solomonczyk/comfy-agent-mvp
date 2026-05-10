#!/usr/bin/env python3
"""
Tests for RC-COMBINE-V2-GENERATED-VISUAL-PURGE-001
"""

import json
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp")
TARGET_OUTPUT_ROOT = PROJECT_ROOT / "data/rc2_multishot1_ep01/output"
CONTROL_DIR = TARGET_OUTPUT_ROOT / "control"

VISUAL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp4"}
PURGE_TASK_ID = "RC-COMBINE-V2-GENERATED-VISUAL-PURGE-001"


class TestGeneratedVisualOutputsPurge:
    def test_no_generated_visual_files_remain_in_canonical_paths(self):
        for ext in VISUAL_EXTENSIONS:
            matches = list(TARGET_OUTPUT_ROOT.rglob(f"*{ext}"))
            assert len(matches) == 0, f"Found remaining visual file: {matches[0]}"

    def test_artifact_index_has_no_active_canonical_visual_result(self):
        local_index = CONTROL_DIR / "artifact_index.json"
        if local_index.exists():
            with open(local_index, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data.get("production_accepted") is False
            assert data.get("assembly_allowed") is False
            assert data.get("downstream_allowed") is False
            # Ensure no visual asset paths are treated as canonical
            for key in ["current_best_concept_candidate_asset", "current_best_quality_reference_asset",
                        "v13_asset_path", "v14_asset_path"]:
                if key in data:
                    assert data.get(f"{key}_canonical_result", False) is False
                    assert data.get(f"{key}_usable_as_reference", False) is False
                    assert data.get(f"{key}_usable_for_downstream", False) is False

    def test_ledger_records_purge(self):
        local_ledger = CONTROL_DIR / "episode_ledger.json"
        root_ledger = PROJECT_ROOT / "episode_ledger.json"

        for ledger_path in [local_ledger, root_ledger]:
            if ledger_path.exists():
                with open(ledger_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                events = data if isinstance(data, list) else data.get("events", [])
                purge_events = [e for e in events if e.get("task_id") == PURGE_TASK_ID]
                assert len(purge_events) > 0, f"No purge event found in {ledger_path}"

    def test_previous_preview_artifacts_invalidated(self):
        invalidation_report = CONTROL_DIR / "generated_visual_outputs_reference_invalidation_report.json"
        assert invalidation_report.exists()
        with open(invalidation_report, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("visual_asset_status") == "purged_by_operator_directive"
        assert data.get("canonical_result") is False
        assert data.get("usable_as_reference") is False
        assert data.get("usable_for_downstream") is False
        assert data.get("production_accepted") is False

    def test_production_accepted_remains_false(self):
        state_report = CONTROL_DIR / "post_purge_state_report.json"
        assert state_report.exists()
        with open(state_report, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("production_accepted") is False
        assert data.get("current_state") == "visual_outputs_purged_rebuild_required"
        assert data.get("next_allowed_action") == "fresh_visual_strategy_required"

    def test_voice_assembly_downstream_blocked(self):
        state_report = CONTROL_DIR / "post_purge_state_report.json"
        with open(state_report, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("voice_generation_ready") is False
        assert data.get("assembly_allowed") is False
        assert data.get("downstream_allowed") is False

    def test_no_generation_render_happened_during_purge(self):
        manifest = CONTROL_DIR / "generated_visual_outputs_purge_manifest.json"
        assert manifest.exists()
        with open(manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("embedded_visual_content_preserved") is False
        assert data.get("total_files_deleted") > 0

    def test_purge_manifest_created(self):
        manifest = CONTROL_DIR / "generated_visual_outputs_purge_manifest.json"
        assert manifest.exists()
        with open(manifest, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("task_id") == PURGE_TASK_ID
        assert "files_found" in data
        assert len(data["files_found"]) > 0
        for entry in data["files_found"]:
            assert entry.get("action") == "deleted"
            assert entry.get("canonical_reference_invalidated") is True

    def test_inventory_created(self):
        inventory = CONTROL_DIR / "generated_visual_outputs_inventory_before_purge.json"
        assert inventory.exists()
        with open(inventory, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("task_id") == PURGE_TASK_ID
        assert data.get("total_files") > 0

    def test_fresh_visual_strategy_required_packet_created(self):
        packet = CONTROL_DIR / "fresh_visual_strategy_required_packet.json"
        assert packet.exists()
        with open(packet, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("current_state") == "visual_outputs_purged_rebuild_required"
        assert data.get("next_allowed_action") == "fresh_visual_strategy_required"

    def test_active_canonical_visual_results_remaining_is_zero(self):
        state_report = CONTROL_DIR / "post_purge_state_report.json"
        with open(state_report, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("active_canonical_visual_results") == 0
        assert data.get("visual_files_remaining_in_canonical_paths") == 0
        assert data.get("usable_visual_references") == 0
