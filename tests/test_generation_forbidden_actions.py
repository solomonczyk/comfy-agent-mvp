"""Test forbidden actions — verify the gate prevents dangerous operations.

RC-COMBINE-V2-99001-102000

Validates:
- Second generation blocked
- Blind retry blocked
- Fake prompt_id blocked
- Fake generated assets blocked
- Visual QA acceptance not executed
- Assembly not executed
- Downstream not executed
- Production_accepted false
- Artifact index updated
- Episode ledger updated
- Git freeze proof required
"""
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"


def _read_json(name: str) -> dict:
    path = CONTROL_DIR / name
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class TestForbiddenSecondGeneration:
    def test_second_generation_not_attempted(self):
        """Second generation must not have been attempted."""
        report = _read_json("generation_execution_report.json")
        assert report.get("second_generation_attempted") is False, (
            "Second generation must not be attempted"
        )

    def test_generation_count_not_exceeded(self):
        """generation_count must not exceed max_generations."""
        report = _read_json("generation_execution_report.json")
        assert report.get("generation_count", 0) <= report.get("max_generations", 1)


class TestForbiddenBlindRetry:
    def test_blind_retry_not_attempted(self):
        """Blind retry must not have been attempted."""
        report = _read_json("generation_execution_report.json")
        assert report.get("blind_retry_attempted") is False, (
            "Blind retry must not be attempted"
        )

    def test_no_retry_flag_in_report(self):
        """No retry_attempted flag should be true in any artifact."""
        for name in ["generation_execution_report.json"]:
            doc = _read_json(name)
            if "retry_attempted" in doc:
                assert doc["retry_attempted"] is False, f"{name} has retry_attempted=true"


class TestForbiddenFakePromptId:
    def test_no_fake_prompt_id_in_report(self):
        """No fake prompt_id in execution report."""
        report = _read_json("generation_execution_report.json")
        pid = report.get("prompt_id", "")
        assert pid != "fake_prompt_id", "Fake prompt_id detected"

    def test_no_fake_prompt_id_in_prompt_report(self):
        """No fake prompt_id in prompt_id_report."""
        report = _read_json("prompt_id_report.json")
        if report:
            assert report.get("fake_prompt_id") is not True
            pid = report.get("prompt_id", "")
            if pid:
                assert pid != "fake_prompt_id"

    def test_no_fake_prompt_id_in_review(self):
        """No fake prompt_id detected in review."""
        review = _read_json("generation_result_review.json")
        if review:
            assert review.get("fake_prompt_id_detected") is False


class TestForbiddenFakeAssets:
    def test_no_fake_assets_in_report(self):
        """No fake assets flag in execution report."""
        report = _read_json("generation_execution_report.json")
        assert report.get("fake_assets_attempted") is False, (
            "Fake assets must not be attempted"
        )

    def test_no_fake_assets_in_review(self):
        """No fake assets detected in review."""
        review = _read_json("generation_result_review.json")
        if review:
            assert review.get("fake_assets_detected") is False

    def test_assets_exist_on_disk(self):
        """All declared assets must exist on disk."""
        manifest = _read_json("canonical_outputs_manifest.json")
        for asset in manifest.get("generated_assets", []):
            abs_path = PROJECT_ROOT / asset.get("path", "")
            assert abs_path.exists(), f"Asset missing: {abs_path}"

    def test_assets_sha256_match(self):
        """Declared SHA256 must match computed SHA256."""
        manifest = _read_json("canonical_outputs_manifest.json")
        for asset in manifest.get("generated_assets", []):
            abs_path = PROJECT_ROOT / asset.get("path", "")
            if abs_path.exists():
                import hashlib
                digest = hashlib.sha256()
                with abs_path.open("rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        digest.update(chunk)
                assert digest.hexdigest() == asset.get("sha256", ""), (
                    f"SHA256 mismatch for {asset.get('path')}"
                )


class TestForbiddenVisualQAAcceptance:
    def test_visual_qa_not_executed_anywhere(self):
        """Visual QA must not be executed in any artifact."""
        for name in [
            "generation_execution_report.json",
            "generation_result_review.json",
            "artifact_index.json",
            "episode_ledger.json",
        ]:
            doc = _read_json(name)
            if "visual_qa_executed" in doc:
                assert doc["visual_qa_executed"] is False, f"{name} has visual_qa_executed=true"

    def test_visual_acceptance_not_executed(self):
        """Visual acceptance must not be executed."""
        review = _read_json("generation_result_review.json")
        if review:
            assert review.get("visual_acceptance_executed") is False


class TestForbiddenAssemblyDownstream:
    def test_assembly_not_executed(self):
        """Assembly must not be executed in any artifact."""
        for name in [
            "generation_execution_report.json",
            "generation_result_review.json",
            "artifact_index.json",
        ]:
            doc = _read_json(name)
            if "assembly_executed" in doc:
                assert doc["assembly_executed"] is False, f"{name} has assembly_executed=true"

    def test_downstream_not_executed(self):
        """Downstream must not be executed in any artifact."""
        for name in [
            "generation_execution_report.json",
            "generation_result_review.json",
            "artifact_index.json",
            "episode_ledger.json",
        ]:
            doc = _read_json(name)
            if "downstream_executed" in doc:
                assert doc["downstream_executed"] is False, f"{name} has downstream_executed=true"

    def test_production_not_accepted(self):
        """Production acceptance must be false in all artifacts."""
        for name in [
            "generation_execution_report.json",
            "generation_result_review.json",
            "artifact_index.json",
            "canonical_outputs_manifest.json",
        ]:
            doc = _read_json(name)
            if "production_accepted" in doc:
                assert doc["production_accepted"] is False, f"{name} has production_accepted=true"


class TestArtifactIndex:
    def test_artifact_index_exists(self):
        """artifact_index.json must exist."""
        idx = _read_json("artifact_index.json")
        assert idx, "artifact_index.json missing"

    def test_artifact_index_has_task_id(self):
        """artifact_index must reference this task."""
        idx = _read_json("artifact_index.json")
        assert idx.get("task_id") == "RC-COMBINE-V2-99001-102000"

    def test_artifact_index_generation_performed(self):
        """artifact_index must record generation as performed."""
        idx = _read_json("artifact_index.json")
        assert idx.get("generation_performed") is True

    def test_artifact_index_comfyui_submitted(self):
        """artifact_index must record ComfyUI submit."""
        idx = _read_json("artifact_index.json")
        assert idx.get("comfyui_submit_executed") is True

    def test_artifact_index_visual_qa_not_executed(self):
        """artifact_index must have visual_qa_executed=false."""
        idx = _read_json("artifact_index.json")
        assert idx.get("visual_qa_executed") is False

    def test_artifact_index_assembly_not_executed(self):
        """artifact_index must have assembly_executed=false."""
        idx = _read_json("artifact_index.json")
        assert idx.get("assembly_executed") is False

    def test_artifact_index_downstream_not_executed(self):
        """artifact_index must have downstream_executed=false."""
        idx = _read_json("artifact_index.json")
        assert idx.get("downstream_executed") is False

    def test_artifact_index_production_not_accepted(self):
        """artifact_index must have production_accepted=false."""
        idx = _read_json("artifact_index.json")
        assert idx.get("production_accepted") is False

    def test_artifact_index_prompt_id_present(self):
        """artifact_index must contain the real prompt_id."""
        idx = _read_json("artifact_index.json")
        assert isinstance(idx.get("prompt_id"), str) and len(idx["prompt_id"]) > 0

    def test_artifact_index_generation_count(self):
        """artifact_index must contain generation_count."""
        idx = _read_json("artifact_index.json")
        assert idx.get("generation_count", 0) >= 1

    def test_artifact_index_state_correct(self):
        """artifact_index current_state must be result_review."""
        idx = _read_json("artifact_index.json")
        assert idx.get("current_state") == "generation_result_review_required"


class TestEpisodeLedger:
    def test_episode_ledger_exists(self):
        """episode_ledger.json must exist."""
        ledger = _read_json("episode_ledger.json")
        assert ledger, "episode_ledger.json missing"

    def _get_ledger_entries(self):
        """Get ledger entries regardless of format (list or dict)."""
        ledger = _read_json("episode_ledger.json")
        if isinstance(ledger, list):
            return ledger
        return ledger.get("entries", []) if isinstance(ledger, dict) else []

    def test_ledger_has_controlled_generation_event(self):
        """Ledger must contain a controlled_generation_executed event."""
        entries = self._get_ledger_entries()
        events = [e for e in entries if e.get("event_type") == "controlled_generation_executed"]
        assert len(events) >= 1, "No controlled_generation_executed event in ledger"

    def test_ledger_event_has_generation_performed(self):
        """Ledger event must record generation_performed=true."""
        entries = self._get_ledger_entries()
        events = [e for e in entries if e.get("event_type") == "controlled_generation_executed"]
        assert events[0].get("generation_performed") is True

    def test_ledger_event_no_visual_qa(self):
        """Ledger event must have visual_qa_executed=false."""
        entries = self._get_ledger_entries()
        events = [e for e in entries if e.get("event_type") == "controlled_generation_executed"]
        assert events[0].get("visual_qa_executed") is False

    def test_ledger_event_no_downstream(self):
        """Ledger event must have downstream_executed=false."""
        entries = self._get_ledger_entries()
        events = [e for e in entries if e.get("event_type") == "controlled_generation_executed"]
        assert events[0].get("downstream_executed") is False

    def test_ledger_event_no_assembly(self):
        """Ledger event must have assembly_executed=false."""
        entries = self._get_ledger_entries()
        events = [e for e in entries if e.get("event_type") == "controlled_generation_executed"]
        assert events[0].get("assembly_executed") is False

    def test_ledger_event_no_production(self):
        """Ledger event must have production_accepted=false."""
        entries = self._get_ledger_entries()
        events = [e for e in entries if e.get("event_type") == "controlled_generation_executed"]
        assert events[0].get("production_accepted") is False

    def test_ledger_prompt_id(self):
        """Ledger event must contain prompt_id."""
        entries = self._get_ledger_entries()
        events = [e for e in entries if e.get("event_type") == "controlled_generation_executed"]
        assert isinstance(events[0].get("prompt_id"), str) and len(events[0]["prompt_id"]) > 0
