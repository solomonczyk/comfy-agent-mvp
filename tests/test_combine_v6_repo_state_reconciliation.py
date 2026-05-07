"""RC-COMBINE-V2-4201-4500 — Test repo state reconciliation and freeze proof fix.

Verifies that:
- dirty files are properly classified
- the freeze contradiction is acknowledged
- git clean is achievable
"""

import json
from pathlib import Path
import pytest


RECONCILIATION_SCHEMA = {
    "task_id": "RC-COMBINE-V2-4201-4500",
    "reconciliation_type": "repository_state",
    "dirty_files_classified": True,
    "git_status_clean_achieved": True,
    "v6_candidate_preserved": True,
    "v6_freeze_artifacts_unchanged": True,
}

FREEZE_RECONCILIATION_SCHEMA = {
    "previous_claimed_git_status_clean": True,
    "unstaged_files_reported": True,
    "contradiction_acknowledged": True,
    "corrected_freeze_status": "accepted_with_blockers_until_reconciled",
    "production_accepted": False,
    "generation_allowed": False,
}


@pytest.fixture
def project_root():
    return Path("data/rc2_multishot1_ep01")


@pytest.fixture
def reconciliation(project_root):
    path = project_root / "output" / "control" / "combine_v2_repo_state_reconciliation.json"
    if not path.exists():
        pytest.skip("Reconciliation artifact not found")
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def freeze_reconciliation(project_root):
    path = project_root / "output" / "control" / "combine_v2_v6_freeze_proof_reconciliation.json"
    if not path.exists():
        pytest.skip("Freeze proof reconciliation not found")
    with open(path) as f:
        return json.load(f)


class TestRepoStateReconciliation:
    def test_reconciliation_schema(self, reconciliation):
        for key, expected in RECONCILIATION_SCHEMA.items():
            assert reconciliation.get(key) == expected, f"{key} mismatch"

    def test_task_id(self, reconciliation):
        assert reconciliation["task_id"] == "RC-COMBINE-V2-4201-4500"

    def test_dirty_files_classified_true(self, reconciliation):
        assert reconciliation["dirty_files_classified"] is True

    def test_all_files_classified(self, reconciliation):
        files = reconciliation.get("files", [])
        assert len(files) == 5
        for f in files:
            assert "path" in f
            assert "status" in f
            assert "category" in f
            assert f["category"] in ("canonical_artifact", "local_noise", "helper_script", "blocker")
            assert "action_taken" in f
            assert "reason" in f

    def test_no_blockers(self, reconciliation):
        assert reconciliation.get("blockers", None) == []

    def test_git_clean_achieved(self, reconciliation):
        assert reconciliation["git_status_clean_achieved"] is True

    def test_v6_candidate_preserved(self, reconciliation):
        assert reconciliation["v6_candidate_preserved"] is True

    def test_v6_freeze_artifacts_unchanged(self, reconciliation):
        assert reconciliation["v6_freeze_artifacts_unchanged"] is True

    def test_canonical_artifacts_classified(self, reconciliation):
        canonical = [f for f in reconciliation["files"] if f["category"] == "canonical_artifact"]
        assert len(canonical) == 2
        for f in canonical:
            assert f["action_taken"] == "committed"

    def test_local_noise_classified(self, reconciliation):
        local_noise = [f for f in reconciliation["files"] if f["category"] == "local_noise"]
        assert len(local_noise) == 2

    def test_helper_script_classified(self, reconciliation):
        helper = [f for f in reconciliation["files"] if f["category"] == "helper_script"]
        assert len(helper) == 1
        assert helper[0]["action_taken"].startswith("moved_to_scripts_tools")


class TestFreezeProofReconciliation:
    def test_freeze_reconciliation_schema(self, freeze_reconciliation):
        for key, expected in FREEZE_RECONCILIATION_SCHEMA.items():
            assert freeze_reconciliation.get(key) == expected, f"{key} mismatch"

    def test_contradiction_acknowledged(self, freeze_reconciliation):
        assert freeze_reconciliation["contradiction_acknowledged"] is True

    def test_corrected_freeze_status(self, freeze_reconciliation):
        assert freeze_reconciliation["corrected_freeze_status"] == "accepted_with_blockers_until_reconciled"

    def test_original_v6_freeze_artifacts_unchanged(self, freeze_reconciliation):
        assert freeze_reconciliation["original_v6_freeze_artifacts_unchanged"] is True

    def test_production_not_accepted(self, freeze_reconciliation):
        assert freeze_reconciliation["production_accepted"] is False

    def test_generation_not_allowed(self, freeze_reconciliation):
        assert freeze_reconciliation["generation_allowed"] is False

    def test_actions_correct_freeze_contradiction(self, freeze_reconciliation):
        actions = freeze_reconciliation.get("correction_actions", [])
        assert len(actions) == 4
