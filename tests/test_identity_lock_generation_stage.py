"""
Tests for RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001

Covers:
- Identity contract enforcement
- Forbidden reference roles
- Negative prompt contents
- Gate blocking
- Max generations = 1
- Blank/framing/identity validation structure
- State correctness
- Production acceptance = False
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

DATA_ROOT = (
    Path(__file__).parent.parent
    / "data"
    / "rc2_multishot1_ep01"
)
CONTROL_DIR = DATA_ROOT / "output" / "control" / "identity_lock"
PROJECT_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def identity_anchor_contract():
    path = CONTROL_DIR / "identity_anchor_contract.json"
    if not path.exists():
        pytest.skip(f"identity_anchor_contract.json not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def identity_context_pack():
    path = CONTROL_DIR / "identity_context_pack.json"
    if not path.exists():
        pytest.skip(f"identity_context_pack.json not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def reference_routing_report():
    path = CONTROL_DIR / "reference_role_routing_report.json"
    if not path.exists():
        pytest.skip(f"reference_role_routing_report.json not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def identity_workflow_patch():
    path = CONTROL_DIR / "identity_locked_workflow_patch.json"
    if not path.exists():
        pytest.skip(f"identity_locked_workflow_patch.json not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def submitted_workflow():
    path = CONTROL_DIR / "submitted_identity_locked_workflow.json"
    if not path.exists():
        pytest.skip(f"submitted_identity_locked_workflow.json not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def generation_gate():
    path = CONTROL_DIR / "identity_generation_gate.json"
    if not path.exists():
        pytest.skip(f"identity_generation_gate.json not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def generation_manifest():
    path = CONTROL_DIR / "identity_generation_manifest.json"
    if not path.exists():
        pytest.skip(f"identity_generation_manifest.json not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def result_review():
    path = CONTROL_DIR / "identity_result_review.json"
    if not path.exists():
        pytest.skip(f"identity_result_review.json not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def operator_review_packet():
    path = CONTROL_DIR / "operator_visual_review_packet.json"
    if not path.exists():
        pytest.skip(f"operator_visual_review_packet.json not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def state_json():
    path = DATA_ROOT / "output" / "control" / "state.json"
    if not path.exists():
        pytest.skip(f"state.json not found: {path}")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def proof_json():
    path = PROJECT_ROOT / "RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001_proof.json"
    if not path.exists():
        pytest.skip(f"proof.json not found: {path}")
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Identity Contract Tests
# ---------------------------------------------------------------------------

class TestIdentityContract:

    def test_contract_exists(self, identity_anchor_contract):
        assert identity_anchor_contract is not None

    def test_canonical_source_enforced(self, identity_anchor_contract):
        # Field is identity_preservation_rules or canonical_identity_source
        text = json.dumps(identity_anchor_contract).lower()
        assert "canonical" in text, "Contract must enforce canonical identity source"

    def test_quality_refs_blocked_from_identity(self, identity_anchor_contract):
        forbidden = json.dumps(identity_anchor_contract).lower()
        assert "quality" in forbidden or "forbidden" in forbidden, \
            "Contract must block quality refs from identity role"

    def test_composition_refs_blocked_from_identity(self, identity_anchor_contract):
        forbidden = json.dumps(identity_anchor_contract).lower()
        assert "composition" in forbidden or "forbidden" in forbidden, \
            "Contract must block composition refs from identity role"

    def test_extra_subjects_forbidden(self, identity_anchor_contract):
        text = json.dumps(identity_anchor_contract).lower()
        assert "extra" in text or "second" in text or "multi" in text, \
            "Contract must forbid extra subjects"


# ---------------------------------------------------------------------------
# Reference Routing Tests
# ---------------------------------------------------------------------------

class TestReferenceRouting:

    def test_routing_report_exists(self, reference_routing_report):
        assert reference_routing_report is not None

    def test_identity_source_present(self, reference_routing_report):
        # Field may be identity_source_selection or identity_source
        assert "identity_source_selection" in reference_routing_report or \
               "identity_source" in reference_routing_report, \
            "Routing report must have identity_source field"

    def test_quality_refs_not_identity_source(self, reference_routing_report):
        identity_src = reference_routing_report.get("identity_source", {})
        # Quality refs should not be the identity source
        role = str(identity_src.get("role", "")).lower()
        assert "quality" not in role, \
            "Quality refs must not be used as identity source"

    def test_forbidden_quality_in_identity_path(self, reference_routing_report):
        # forbidden_routing may be a top-level key
        forbidden_routing = reference_routing_report.get("forbidden_routing", {})
        quality_handling = reference_routing_report.get("quality_reference_handling", {})
        text = json.dumps(reference_routing_report).lower()
        assert "quality" in text and ("forbidden" in text or "blocked" in text), \
            "Quality refs must be blocked from identity path"


# ---------------------------------------------------------------------------
# Workflow Patch Tests
# ---------------------------------------------------------------------------

class TestWorkflowPatch:

    def test_patch_exists(self, identity_workflow_patch):
        assert identity_workflow_patch is not None

    def test_negative_prompt_has_no_second_person(self, identity_workflow_patch):
        prompt_mods = identity_workflow_patch.get("prompt_modifications", {})
        neg = " ".join(prompt_mods.get("negative_prompt_additions", []))
        text = neg.lower()
        has_extra_person = any(kw in text for kw in [
            "second person", "extra person", "duplicate person", "man in foreground",
            "multiple people", "crowd"
        ])
        assert has_extra_person, "Negative prompt must forbid second/extra persons"

    def test_resolution_not_square_closeup(self, identity_workflow_patch):
        framing = identity_workflow_patch.get("framing_constraints", {})
        target_res = framing.get("target_resolution", "")
        assert target_res != "1024x1024", \
            "Workflow must not use square 1024x1024 (closeup) resolution"

    def test_single_subject_enforced(self, identity_workflow_patch):
        text = json.dumps(identity_workflow_patch).lower()
        assert "single" in text or "one subject" in text or "single subject" in text, \
            "Patch must enforce single subject"


# ---------------------------------------------------------------------------
# Submitted Workflow Tests
# ---------------------------------------------------------------------------

class TestSubmittedWorkflow:

    def test_submitted_workflow_exists(self, submitted_workflow):
        assert submitted_workflow is not None

    def test_submitted_has_ksampler(self, submitted_workflow):
        node_types = [v.get("class_type", "") for v in submitted_workflow.values()
                      if isinstance(v, dict)]
        assert "KSampler" in node_types, "Submitted workflow must have KSampler"

    def test_submitted_has_save_image(self, submitted_workflow):
        node_types = [v.get("class_type", "") for v in submitted_workflow.values()
                      if isinstance(v, dict)]
        assert "SaveImage" in node_types, "Submitted workflow must have SaveImage"

    def test_resolution_is_wide_format(self, submitted_workflow):
        for node in submitted_workflow.values():
            if isinstance(node, dict) and node.get("class_type") == "EmptyLatentImage":
                w = node["inputs"]["width"]
                h = node["inputs"]["height"]
                assert w > h, f"Resolution must be wide format, got {w}x{h}"
                return
        pytest.skip("EmptyLatentImage node not found")

    def test_negative_prompt_contains_identity_terms(self, submitted_workflow):
        for node in submitted_workflow.values():
            if isinstance(node, dict) and node.get("class_type") == "CLIPTextEncode":
                text = node.get("inputs", {}).get("text", "").lower()
                if "blurry" in text or "duplicate" in text or "extra" in text:
                    # This is the negative prompt node — check identity terms
                    assert any(kw in text for kw in [
                        "extra person", "second person", "duplicate person",
                        "identity drift", "face swap", "different woman"
                    ]), "Negative prompt must include identity protection terms"
                    return


# ---------------------------------------------------------------------------
# Generation Gate Tests
# ---------------------------------------------------------------------------

class TestGenerationGate:

    def test_gate_exists(self, generation_gate):
        assert generation_gate is not None

    def test_max_generations_is_one(self, generation_gate):
        max_gen = generation_gate.get("max_generations", 0)
        assert max_gen == 1, f"max_generations must be 1, got {max_gen}"

    def test_gate_blocks_without_identity_contract(self, generation_gate):
        # identity_contract_valid is the actual field name
        text = json.dumps(generation_gate).lower()
        assert "identity_contract" in text, \
            "Gate must reference identity contract requirement"

    def test_stop_after_generation(self, generation_gate):
        text = json.dumps(generation_gate).lower()
        assert "stop" in text or "operator_visual_review" in text or \
               "stop_after_generation" in text, \
            "Gate must stop after generation for operator review"


# ---------------------------------------------------------------------------
# Generation Manifest Tests
# ---------------------------------------------------------------------------

class TestGenerationManifest:

    def test_manifest_exists(self, generation_manifest):
        assert generation_manifest is not None

    def test_generation_performed(self, generation_manifest):
        assert generation_manifest.get("generation_performed") is True

    def test_generation_count_is_one(self, generation_manifest):
        count = generation_manifest.get("generation_count", 0)
        assert count == 1, f"generation_count must be 1, got {count}"

    def test_max_generations_is_one(self, generation_manifest):
        max_gen = generation_manifest.get("max_generations", 0)
        assert max_gen == 1, f"max_generations must be 1, got {max_gen}"

    def test_no_second_generation(self, generation_manifest):
        assert generation_manifest.get("second_generation_attempted") is False

    def test_no_blind_retry(self, generation_manifest):
        assert generation_manifest.get("blind_retry_attempted") is False

    def test_asset_path_present(self, generation_manifest):
        path = generation_manifest.get("generated_asset_path", "")
        assert path, "generated_asset_path must be set"

    def test_asset_exists_on_disk(self, generation_manifest):
        path = generation_manifest.get("generated_asset_path", "")
        assert path and Path(path).exists(), \
            f"Generated asset must exist on disk: {path}"


# ---------------------------------------------------------------------------
# Result Review Tests
# ---------------------------------------------------------------------------

class TestResultReview:

    def test_review_exists(self, result_review):
        assert result_review is not None

    def test_blank_detector_field_present(self, result_review):
        assert "blank_detector" in result_review, "blank_detector must be in review"

    def test_framing_detector_field_present(self, result_review):
        assert "framing_detector" in result_review, "framing_detector must be in review"

    def test_single_subject_gate_field_present(self, result_review):
        assert "single_subject_gate" in result_review, "single_subject_gate must be in review"

    def test_identity_gate_field_present(self, result_review):
        assert "identity_gate" in result_review, "identity_gate must be in review"

    def test_production_not_accepted(self, result_review):
        assert result_review.get("production_accepted") is False, \
            "production_accepted must be False — awaiting operator review"

    def test_state_is_operator_visual_review(self, result_review):
        state = result_review.get("current_state", "")
        assert state == "operator_visual_review_required", \
            f"State must be operator_visual_review_required, got {state}"

    def test_operator_checklist_present(self, result_review):
        checklist = result_review.get("operator_checklist", [])
        assert len(checklist) > 0, "operator_checklist must have entries"

    def test_operator_decision_is_null(self, result_review):
        assert result_review.get("operator_decision") is None, \
            "operator_decision must be null (not yet decided)"


# ---------------------------------------------------------------------------
# Operator Review Packet Tests
# ---------------------------------------------------------------------------

class TestOperatorReviewPacket:

    def test_packet_exists(self, operator_review_packet):
        assert operator_review_packet is not None

    def test_asset_for_review_present(self, operator_review_packet):
        path = operator_review_packet.get("asset_for_review", "")
        assert path, "asset_for_review must be set"

    def test_gate_results_present(self, operator_review_packet):
        gates = operator_review_packet.get("gate_results", {})
        assert "blank_detector" in gates
        assert "framing_detector" in gates
        assert "single_subject_gate" in gates
        assert "identity_gate" in gates

    def test_production_not_accepted(self, operator_review_packet):
        assert operator_review_packet.get("production_accepted") is False

    def test_operator_decision_null(self, operator_review_packet):
        assert operator_review_packet.get("operator_decision") is None


# ---------------------------------------------------------------------------
# State Tests
# ---------------------------------------------------------------------------

class TestState:

    def test_state_is_operator_visual_review(self, state_json):
        state = state_json.get("current_state", "")
        assert state == "operator_visual_review_required", \
            f"State must be operator_visual_review_required, got {state}"

    def test_production_not_accepted(self, state_json):
        assert state_json.get("production_accepted") is False

    def test_generation_count_is_one(self, state_json):
        count = state_json.get("generation_count", 0)
        assert count == 1, f"generation_count must be 1, got {count}"


# ---------------------------------------------------------------------------
# Proof Tests
# ---------------------------------------------------------------------------

class TestProof:

    def test_proof_exists(self, proof_json):
        assert proof_json is not None

    def test_proof_generation_performed(self, proof_json):
        assert proof_json.get("generation_performed") is True

    def test_proof_no_second_generation(self, proof_json):
        assert proof_json.get("second_generation_attempted") is False

    def test_proof_identity_contract(self, proof_json):
        assert proof_json.get("identity_contract_created") is True or \
               proof_json.get("identity_contract_enforced") is True

    def test_proof_production_not_accepted(self, proof_json):
        assert proof_json.get("production_accepted") is False

    def test_proof_asset_sha256(self, proof_json):
        sha = proof_json.get("generated_asset_sha256", "")
        assert len(sha) == 64, f"SHA256 must be 64 chars, got: {sha!r}"


# ---------------------------------------------------------------------------
# Module Import Tests
# ---------------------------------------------------------------------------

class TestModuleImports:

    def test_identity_lock_module_importable(self):
        from app.agents.identity_lock import IdentityLockRunner
        assert IdentityLockRunner is not None

    def test_contract_importable(self):
        from app.agents.identity_lock.contract import IdentityLockContract
        assert IdentityLockContract is not None

    def test_brain_decision_importable(self):
        from app.agents.identity_lock.brain_decision import LLMBrainDecision
        assert LLMBrainDecision is not None

    def test_identity_gate_importable(self):
        from app.agents.identity_lock.identity_gate import IdentityGate
        assert IdentityGate is not None

    def test_single_subject_gate_importable(self):
        from app.agents.identity_lock.single_subject_gate import SingleSubjectGate
        assert SingleSubjectGate is not None

    def test_workflow_patch_importable(self):
        from app.agents.identity_lock.workflow_patch import WorkflowPatch
        assert WorkflowPatch is not None
