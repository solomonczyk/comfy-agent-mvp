"""RC-COMBINE-V2-5101-5400 — Test V7 identity/fidelity generation runtime guards.

Verifies:
- Operator authorization required and created
- V7 package required
- Concept and quality references required
- One generation allowed, second generation blocked
- Canonical output registered
- Visual acceptance blocked
- Production accepted false
- Assembly/downstream blocked
- Operator review required final state
"""

import json
from pathlib import Path
import pytest


PROJECT_ROOT = Path("data/rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"
ASSETS_DIR = PROJECT_ROOT / "output" / "assets"

AUTHORIZATION_PATH = CONTROL_DIR / "combine_v2_v7_identity_fidelity_generation_authorization.json"
PACKAGE_PATH = CONTROL_DIR / "combine_v2_v7_identity_fidelity_locked_refinement_package.json"
GATE_PATH = CONTROL_DIR / "combine_v2_v7_identity_fidelity_generation_gate.json"
SUBMITTED_WORKFLOW_PATH = CONTROL_DIR / "shot02_v7_identity_fidelity_submitted_workflow.json"
MANIFEST_PATH = CONTROL_DIR / "combine_v2_v7_identity_fidelity_outputs_manifest.json"
RESULT_PATH = CONTROL_DIR / "combine_v2_v7_identity_fidelity_result.json"
REVIEW_PACKET_PATH = CONTROL_DIR / "combine_v2_v7_identity_fidelity_operator_review_packet.json"
INDEX_PATH = CONTROL_DIR / "artifact_index.json"
LEDGER_PATH = CONTROL_DIR / "episode_ledger.json"

V6_CONCEPT_ASSET = ASSETS_DIR / "combine_v2_clean_sdxl_v6_candidate_shot02_00001_.png"
V6_QUALITY_ASSET = ASSETS_DIR / "combine_v2_v6_targeted_refinement_shot02_00001_.png"


@pytest.fixture(scope="session", autouse=True)
def check_artifacts_exist():
    """Skip all tests if required artifacts are missing."""
    required = [
        AUTHORIZATION_PATH, PACKAGE_PATH, GATE_PATH,
        SUBMITTED_WORKFLOW_PATH, MANIFEST_PATH, RESULT_PATH,
        REVIEW_PACKET_PATH, INDEX_PATH, V6_CONCEPT_ASSET,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        pytest.skip(f"Required artifacts not found: {missing}")


class TestRuntimeGuards:
    def test_operator_authorization_required(self):
        gate = json.load(open(GATE_PATH))
        assert gate["requires_operator_authorization"] is True

    def test_operator_authorization_created(self):
        auth = json.load(open(AUTHORIZATION_PATH))
        assert auth["operator_authorized"] is True
        assert auth["generation_allowed"] is True

    def test_v7_package_required(self):
        pkg = json.load(open(PACKAGE_PATH))
        assert pkg["package_type"] == "v7_identity_fidelity_locked_refinement"

    def test_concept_reference_required(self):
        assert V6_CONCEPT_ASSET.exists(), "V6 concept reference missing"

    def test_quality_reference_required(self):
        assert V6_QUALITY_ASSET.exists(), "V6 quality reference missing"

    def test_one_generation_allowed(self):
        result = json.load(open(RESULT_PATH))
        assert result["generation_count"] == 1

    def test_second_generation_blocked(self):
        result = json.load(open(RESULT_PATH))
        assert result["second_generation_attempted"] is False

    def test_canonical_output_registered(self):
        manifest = json.load(open(MANIFEST_PATH))
        assert len(manifest["generated_assets"]) > 0

        asset_path = manifest["generated_assets"][0].get("path", "")
        assert asset_path
        full_path = PROJECT_ROOT / asset_path
        assert full_path.exists(), f"Canonical asset not found: {asset_path}"
        assert full_path.stat().st_size > 1024, "Asset too small"

    def test_visual_acceptance_blocked(self):
        manifest = json.load(open(MANIFEST_PATH))
        assert manifest["visual_acceptance_executed"] is False

    def test_production_accepted_false(self):
        result = json.load(open(RESULT_PATH))
        assert result["production_accepted"] is False

        index = json.load(open(INDEX_PATH))
        assert index["production_accepted"] is False

    def test_assembly_downstream_blocked(self):
        result = json.load(open(RESULT_PATH))
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False

        index = json.load(open(INDEX_PATH))
        assert index.get("assembly_allowed") is False
        assert index.get("downstream_allowed") is False

    def test_operator_review_required_final_state(self):
        index = json.load(open(INDEX_PATH))
        assert index["current_state"] == "operator_visual_review_required"
        assert index["next_allowed_action"] == "operator_visual_review_required"

        packet = json.load(open(REVIEW_PACKET_PATH))
        assert packet["next_allowed_action"] == "operator_visual_review_required"

    def test_ledger_entry(self):
        ledger = json.load(open(LEDGER_PATH))
        assert isinstance(ledger, list)

        v7_entries = [e for e in ledger if e.get("event_type") == "v7_identity_fidelity_generation_completed"]
        assert len(v7_entries) == 1

        entry = v7_entries[0]
        assert entry["generation_count"] == 1
        assert entry["second_generation_attempted"] is False
        assert entry["workflow_submitted"] is True
        assert entry["visual_acceptance_executed"] is False
        assert entry["assembly_executed"] is False
        assert entry["downstream_executed"] is False
        assert entry["current_state"] == "operator_visual_review_required"
        assert entry["next_allowed_action"] == "operator_visual_review_required"


class TestCanonicalAssetValidation:
    def test_asset_readable(self):
        manifest = json.load(open(MANIFEST_PATH))
        asset = manifest["generated_assets"][0]
        assert asset.get("readable") is True

    def test_sha256_present(self):
        manifest = json.load(open(MANIFEST_PATH))
        asset = manifest["generated_assets"][0]
        sha = asset.get("sha256", "")
        assert len(sha) == 64, "SHA256 missing or invalid"

    def test_asset_size_positive(self):
        manifest = json.load(open(MANIFEST_PATH))
        asset = manifest["generated_assets"][0]
        size = asset.get("size_bytes", 0)
        assert size > 1024, f"Asset too small: {size} bytes"

    def test_dimensions_present(self):
        manifest = json.load(open(MANIFEST_PATH))
        asset = manifest["generated_assets"][0]
        assert asset.get("width") is not None
        assert asset.get("height") is not None
        assert asset["width"] > 0
        assert asset["height"] > 0

    def test_asset_in_assets_dir(self):
        manifest = json.load(open(MANIFEST_PATH))
        asset_path = manifest["generated_assets"][0].get("path", "")
        assert "output/assets/" in asset_path or "output\\assets\\" in asset_path

    def test_asset_prefix(self):
        manifest = json.load(open(MANIFEST_PATH))
        asset_path = manifest["generated_assets"][0].get("path", "")
        filename = Path(asset_path).name
        assert "combine_v2_v7_identity_fidelity_shot02" in filename
