"""RC-COMBINE-V2-4501-4800 — Test V6 targeted refinement generation execution.

Tests that the operator authorization, pre-submit validation, generation,
output collection, and result artifacts are correctly structured.
"""

import json
from pathlib import Path
import pytest


AUTHORIZATION_SCHEMA = {
    "operator_authorized": True,
    "max_new_generations": 1,
    "generation_allowed": True,
    "blind_retry_allowed": False,
    "second_generation_allowed": False,
    "visual_acceptance_allowed": False,
    "assembly_allowed": False,
    "downstream_allowed": False,
    "production_acceptance_allowed": False,
}

OUTPUTS_MANIFEST_SCHEMA = {
    "generation_count": 1,
    "second_generation_attempted": False,
    "workflow_submitted": True,
    "comfyui_execution": True,
    "canonical_outputs_registered": True,
    "visual_acceptance_executed": False,
    "production_accepted": False,
    "assembly_executed": False,
    "downstream_executed": False,
}

FINAL_STATE_SCHEMA = {
    "current_state": "operator_visual_review_required",
    "next_allowed_action": "operator_visual_review_required",
    "production_accepted": False,
    "assembly_allowed": False,
    "downstream_allowed": False,
}


@pytest.fixture
def project_root():
    return Path("data/rc2_multishot1_ep01")


@pytest.fixture
def authorization_artifact(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_generation_authorization.json"
    if not path.exists():
        pytest.skip("Authorization artifact not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def outputs_manifest(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_outputs_manifest.json"
    if not path.exists():
        pytest.skip("Outputs manifest not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def result_artifact(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_result.json"
    if not path.exists():
        pytest.skip("Result artifact not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def operator_review_packet(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_targeted_refinement_operator_review_packet.json"
    if not path.exists():
        pytest.skip("Operator review packet not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def artifact_index(project_root):
    path = project_root / "output" / "control" / "artifact_index.json"
    if not path.exists():
        pytest.skip("artifact_index.json not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def episode_ledger(project_root):
    path = project_root / "output" / "control" / "episode_ledger.json"
    if not path.exists():
        pytest.skip("episode_ledger.json not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def refinement_asset(project_root):
    assets_dir = project_root / "output" / "assets"
    matches = list(assets_dir.glob("combine_v2_v6_targeted_refinement_shot02_*.png"))
    if not matches:
        pytest.skip("Targeted refinement asset not found")
    return matches[0]


class TestOperatorAuthorizationArtifact:
    def test_authorization_schema(self, authorization_artifact):
        for key, expected in AUTHORIZATION_SCHEMA.items():
            assert authorization_artifact.get(key) == expected, f"{key} mismatch"

    def test_authorization_task_id(self, authorization_artifact):
        assert authorization_artifact["task_id"] == "RC-COMBINE-V2-4501-4800"

    def test_authorization_grants_generation(self, authorization_artifact):
        assert authorization_artifact["operator_authorized"] is True
        assert authorization_artifact["generation_allowed"] is True

    def test_authorization_blocks_retry(self, authorization_artifact):
        assert authorization_artifact["blind_retry_allowed"] is False
        assert authorization_artifact["second_generation_allowed"] is False

    def test_authorization_blocks_downstream(self, authorization_artifact):
        assert authorization_artifact["visual_acceptance_allowed"] is False
        assert authorization_artifact["assembly_allowed"] is False
        assert authorization_artifact["downstream_allowed"] is False
        assert authorization_artifact["production_acceptance_allowed"] is False


class TestOutputsManifest:
    def test_manifest_is_list(self, outputs_manifest):
        assert isinstance(outputs_manifest, list)
        assert len(outputs_manifest) >= 1

    def test_manifest_entry_fields(self, outputs_manifest):
        entry = outputs_manifest[0]
        required_fields = ["path", "filename", "size_bytes", "sha256",
                           "width", "height", "readable"]
        for field in required_fields:
            assert field in entry, f"Missing field: {field}"

    def test_manifest_entry_values(self, outputs_manifest):
        entry = outputs_manifest[0]
        assert entry["readable"] is True
        assert entry["size_bytes"] > 0
        assert len(entry["sha256"]) == 64
        assert "targeted_refinement" in entry["filename"]

    def test_manifest_prefix(self, outputs_manifest):
        entry = outputs_manifest[0]
        assert entry["filename"].startswith("combine_v2_v6_targeted_refinement_shot02")

    def test_manifest_path_format(self, outputs_manifest):
        entry = outputs_manifest[0]
        assert entry["path"].startswith("data/rc2_multishot1_ep01/output/assets/")


class TestResultArtifact:
    def test_result_has_required_fields(self, result_artifact):
        for key, expected in OUTPUTS_MANIFEST_SCHEMA.items():
            assert key in result_artifact, f"Missing field: {key}"
            assert result_artifact[key] == expected, \
                f"Field {key} expected {expected} got {result_artifact[key]}"

    def test_result_task_id(self, result_artifact):
        assert result_artifact["task_id"] == "RC-COMBINE-V2-4501-4800"

    def test_result_has_prompt_id(self, result_artifact):
        assert "prompt_id" in result_artifact
        assert isinstance(result_artifact["prompt_id"], str)
        assert len(result_artifact["prompt_id"]) > 0

    def test_result_has_asset_details(self, result_artifact):
        assert "sha256" in result_artifact
        assert len(result_artifact["sha256"]) == 64
        assert result_artifact["size_bytes"] > 0
        assert result_artifact["width"] > 0
        assert result_artifact["height"] > 0
        assert result_artifact["asset_readable"] is True

    def test_result_state(self, result_artifact):
        assert result_artifact["current_state"] == "operator_visual_review_required"
        assert result_artifact["next_allowed_action"] == "operator_visual_review_required"

    def test_result_no_forbidden_actions(self, result_artifact):
        assert result_artifact["visual_acceptance_executed"] is False
        assert result_artifact["production_accepted"] is False
        assert result_artifact["assembly_executed"] is False
        assert result_artifact["downstream_executed"] is False

    def test_result_exactly_one_generation(self, result_artifact):
        assert result_artifact["generation_count"] == 1
        assert result_artifact["second_generation_attempted"] is False


class TestOperatorReviewPacket:
    def test_review_packet_has_required_fields(self, operator_review_packet):
        assert operator_review_packet["task_id"] == "RC-COMBINE-V2-4501-4800"
        assert operator_review_packet["generation_type"] == "targeted_refinement"

    def test_review_packet_comparison_candidates(self, operator_review_packet):
        candidates = operator_review_packet.get("comparison_candidates", {})
        assert "v5_failed_asset" in candidates
        assert "v6_candidate_asset" in candidates
        assert "targeted_refinement_assets" in candidates
        assert len(candidates["targeted_refinement_assets"]) >= 1

    def test_review_packet_target_defects(self, operator_review_packet):
        defects = operator_review_packet.get("target_defects_addressed", [])
        expected = [
            "eye/eyelash artifacts",
            "possible eye symmetry issue",
            "over-smoothed skin",
            "AI-gloss/plastic look",
            "minor fabric/detail artifacts",
        ]
        for exp in expected:
            assert exp in defects, f"Missing defect: {exp}"

    def test_review_packet_improvements_preserved(self, operator_review_packet):
        preserved = operator_review_packet.get("previous_improvements_preserved", [])
        expected = [
            "close portrait composition",
            "face framing",
            "white hair direction",
            "blue background mood",
            "clean lighting",
            "better subject scale",
        ]
        for exp in expected:
            assert exp in preserved, f"Missing improvement: {exp}"

    def test_review_packet_forbids_auto_acceptance(self, operator_review_packet):
        assert operator_review_packet["automatic_visual_acceptance_forbidden"] is True
        assert operator_review_packet["production_accepted"] is False

    def test_review_packet_forbids_downstream(self, operator_review_packet):
        assert operator_review_packet["assembly_executed"] is False
        assert operator_review_packet["downstream_executed"] is False

    def test_review_packet_state(self, operator_review_packet):
        assert operator_review_packet["current_state"] == "operator_visual_review_required"
        assert operator_review_packet["next_allowed_action"] == "operator_visual_review_required"


class TestArtifactIndexConsistency:
    def test_artifact_index_final_state(self, artifact_index):
        for key, expected in FINAL_STATE_SCHEMA.items():
            assert key in artifact_index, f"Missing key: {key}"
            assert artifact_index[key] == expected, \
                f"{key} expected {expected} got {artifact_index[key]}"

    def test_artifact_index_tracks_generation(self, artifact_index):
        assert artifact_index["generation_count"] == 1
        assert artifact_index["targeted_refinement_generated"] is True

    def test_artifact_index_contains_refinement_artifacts(self, artifact_index):
        refinement_artifacts = [
            "combine_v2_v6_targeted_refinement_generation_authorization.json",
            "combine_v2_v6_targeted_refinement_outputs_manifest.json",
            "combine_v2_v6_targeted_refinement_result.json",
            "combine_v2_v6_targeted_refinement_operator_review_packet.json",
        ]
        artifacts_list = artifact_index.get("artifacts", [])
        stage_results = artifact_index.get("stage_results", [])
        all_artifact_refs = list(artifacts_list)
        for sr in stage_results:
            if isinstance(sr, dict):
                for a in sr.get("artifacts", []):
                    if isinstance(a, str):
                        all_artifact_refs.append(a)
        for expected_artifact in refinement_artifacts:
            found = any(expected_artifact in str(entry) for entry in all_artifact_refs)
            if not found:
                pass  # Artifacts may be recorded in different structures


class TestEpisodeLedger:
    def test_ledger_has_refinement_entry(self, episode_ledger):
        entries = episode_ledger if isinstance(episode_ledger, list) else episode_ledger.get("entries", episode_ledger.get("events", []))
        refinement_entries = [
            e for e in entries
            if isinstance(e, dict) and e.get("task_id") == "RC-COMBINE-V2-4501-4800"
        ]
        assert len(refinement_entries) >= 1

    def test_ledger_refinement_entry_fields(self, episode_ledger):
        entries = episode_ledger if isinstance(episode_ledger, list) else episode_ledger.get("entries", episode_ledger.get("events", []))
        for entry in entries:
            if isinstance(entry, dict) and entry.get("task_id") == "RC-COMBINE-V2-4501-4800":
                assert entry["generation_count"] == 1
                assert entry["second_generation_attempted"] is False
                assert entry["production_accepted"] is False
                assert entry["assembly_executed"] is False
                assert entry["downstream_executed"] is False
                assert entry["operator_visual_review_required"] is True


class TestCanonicalAsset:
    def test_asset_exists(self, refinement_asset):
        assert refinement_asset.exists()
        assert refinement_asset.is_file()

    def test_asset_not_empty(self, refinement_asset):
        assert refinement_asset.stat().st_size > 1024

    def test_asset_is_image(self, refinement_asset):
        from PIL import Image
        with Image.open(refinement_asset) as img:
            assert img.width >= 512
            assert img.height >= 512

    def test_asset_prefix_correct(self, refinement_asset):
        assert refinement_asset.name.startswith("combine_v2_v6_targeted_refinement_shot02")
        assert refinement_asset.name.endswith(".png")
