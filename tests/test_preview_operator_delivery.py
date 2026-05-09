"""RC-COMBINE-V2-PREVIEW-ARTIFACTS-OPERATOR-DELIVERY-001 — Tests for preview artifacts operator delivery."""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from app.cli import combine_build_preview_operator_delivery

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_args(project_root: str, json_output: bool = True):
    """Create a namespace-like object for combine_build_preview_operator_delivery."""
    from argparse import Namespace

    return Namespace(project_root=project_root, json=json_output)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _gen_file(path: Path, size: int = 100) -> str:
    """Create a file at *path* with *size* random bytes. Returns sha256 hex."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = os.urandom(size)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def project_dir():
    """Create a temp project with all three preview artifacts present."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Canonical preview dir is output/preview/ (singular)
        preview_dir = root / "output" / "preview"
        preview_dir.mkdir(parents=True, exist_ok=True)

        _gen_file(preview_dir / "preview_lowres.mp4", size=5000)
        _gen_file(preview_dir / "preview.gif", size=3000)
        _gen_file(preview_dir / "contact_sheet.jpg", size=2000)

        # Create control dir with render report and result review
        control_dir = root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        _write_json(control_dir / "preview_render_report.json", {
            "task_id": "RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001",
            "outputs": {
                "preview_lowres.mp4": {"size_bytes": 5000, "sha256": _sha256_of(preview_dir / "preview_lowres.mp4")},
                "preview.gif": {"size_bytes": 3000, "sha256": _sha256_of(preview_dir / "preview.gif")},
                "contact_sheet.jpg": {"size_bytes": 2000, "sha256": _sha256_of(preview_dir / "contact_sheet.jpg")},
            },
        })
        _write_json(control_dir / "preview_result_review.json", {
            "preview_artifacts_valid": True,
        })

        # Create artifact_index and episode_ledger for update testing
        _write_json(control_dir / "artifact_index.json", {
            "current_state": "preview_operator_review_required",
            "next_allowed_action": "preview_operator_review_required",
            "production_accepted": False,
        })
        _write_json(control_dir / "episode_ledger.json", [])

        yield str(root)


def _sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Tests — all artifacts present
# ---------------------------------------------------------------------------


class TestAllArtifactsPresent:
    def test_detects_all_preview_artifacts(self, project_dir):
        """All three preview artifacts are detected and marked exists=True."""
        result = combine_build_preview_operator_delivery(_make_args(project_dir))
        assert result == 0

        bundle = json.loads(Path(project_dir, "output/control/preview_operator_delivery_bundle.json").read_text())
        assert bundle["preview_artifacts_found"] is True
        assert bundle["operator_review_ready"] is True
        assert len(bundle["artifacts"]) == 3
        for a in bundle["artifacts"]:
            assert a["exists"] is True
            assert a["size_bytes"] > 0
            assert a["sha256"] is not None

    def test_produces_delivery_bundle_only_when_files_are_real(self, project_dir):
        """Delivery bundle is created with correct structure when files exist."""
        result = combine_build_preview_operator_delivery(_make_args(project_dir))
        assert result == 0

        bundle_path = Path(project_dir, "output/control/preview_operator_delivery_bundle.json")
        assert bundle_path.exists()

        bundle = json.loads(bundle_path.read_text())
        assert bundle["operator_review_ready"] is True
        assert bundle["human_verdict_required"] is True
        assert bundle["production_accepted"] is False
        assert bundle["operator_instruction"] == "Open these files manually before providing human verdict."

    def test_reconciliation_created(self, project_dir):
        """Reconciliation artifact compares claims vs filesystem."""
        combine_build_preview_operator_delivery(_make_args(project_dir))

        recon_path = Path(project_dir, "output/control/preview_artifact_delivery_reconciliation.json")
        assert recon_path.exists()
        recon = json.loads(recon_path.read_text())
        assert recon["all_artifacts_found"] is True
        assert recon["all_sha256_match_render_report"] is True
        assert recon["previous_proof_claims"]["preview_render_report"]["present"] is True

    def test_updates_artifact_index(self, project_dir):
        """Artifact index is updated with delivery check flags."""
        combine_build_preview_operator_delivery(_make_args(project_dir))

        idx = json.loads(Path(project_dir, "output/control/artifact_index.json").read_text())
        assert idx["preview_operator_delivery_checked"] is True
        assert idx["operator_review_ready"] is True
        assert idx["preview_artifacts_found"] is True
        # State must NOT change
        assert idx["current_state"] == "preview_operator_review_required"
        assert idx["next_allowed_action"] == "preview_operator_review_required"
        assert idx["production_accepted"] is False

    def test_updates_episode_ledger(self, project_dir):
        """Episode ledger gets delivery check event."""
        combine_build_preview_operator_delivery(_make_args(project_dir))

        ledger = json.loads(Path(project_dir, "output/control/episode_ledger.json").read_text())
        events = [e for e in ledger if e.get("event") == "preview_artifacts_operator_delivery_checked"]
        assert len(events) == 1
        ev = events[0]
        assert ev["operator_review_ready"] is True
        assert ev["state_after"] == "preview_operator_review_required"
        assert ev["next_allowed_action"] == "preview_operator_review_required"
        assert ev["production_accepted"] is False

    def test_no_fake_operator_verdict(self, project_dir):
        """Delivery bundle does NOT contain an operator verdict."""
        combine_build_preview_operator_delivery(_make_args(project_dir))
        bundle = json.loads(Path(project_dir, "output/control/preview_operator_delivery_bundle.json").read_text())
        assert "operator_verdict" not in bundle
        assert "verdict" not in bundle
        assert bundle.get("human_verdict_required") is True

    def test_no_production_accepted_true(self, project_dir):
        """production_accepted remains False everywhere."""
        combine_build_preview_operator_delivery(_make_args(project_dir))
        bundle = json.loads(Path(project_dir, "output/control/preview_operator_delivery_bundle.json").read_text())
        assert bundle["production_accepted"] is False

    def test_does_not_authorize_downstream(self, project_dir):
        """No voice/audio/assembly/downstream authorization flags set."""
        combine_build_preview_operator_delivery(_make_args(project_dir))
        bundle = json.loads(Path(project_dir, "output/control/preview_operator_delivery_bundle.json").read_text())
        assert "voice_generation_ready" not in bundle or bundle.get("voice_generation_ready") is not True
        assert "assembly_allowed" not in bundle or bundle.get("assembly_allowed") is not True
        assert "downstream_allowed" not in bundle or bundle.get("downstream_allowed") is not True


# ---------------------------------------------------------------------------
# Tests — missing / zero-byte artifacts
# ---------------------------------------------------------------------------


class TestMissingArtifacts:
    def test_blocks_when_preview_lowres_mp4_missing(self, project_dir):
        """Blocker created when preview_lowres.mp4 is missing."""
        preview_dir = Path(project_dir, "output/preview")
        os.remove(str(preview_dir / "preview_lowres.mp4"))

        combine_build_preview_operator_delivery(_make_args(project_dir))

        blocker = json.loads(Path(project_dir, "output/control/preview_operator_delivery_blocker.json").read_text())
        assert blocker["operator_review_possible"] is False
        assert blocker["blocker_type"] == "preview_artifacts_not_available_for_operator_review"
        # Verify which artifact is missing
        bundle = json.loads(Path(project_dir, "output/control/preview_operator_delivery_bundle.json").read_text())
        mp4 = [a for a in bundle["artifacts"] if a["name"] == "preview_lowres.mp4"][0]
        assert mp4["exists"] is False

    def test_blocks_when_preview_gif_missing(self, project_dir):
        """Blocker created when preview.gif is missing."""
        preview_dir = Path(project_dir, "output/preview")
        os.remove(str(preview_dir / "preview.gif"))

        combine_build_preview_operator_delivery(_make_args(project_dir))

        blocker_path = Path(project_dir, "output/control/preview_operator_delivery_blocker.json")
        assert blocker_path.exists()
        blocker = json.loads(blocker_path.read_text())
        assert blocker["operator_review_possible"] is False

        bundle = json.loads(Path(project_dir, "output/control/preview_operator_delivery_bundle.json").read_text())
        gif = [a for a in bundle["artifacts"] if a["name"] == "preview.gif"][0]
        assert gif["exists"] is False

    def test_blocks_when_contact_sheet_jpg_missing(self, project_dir):
        """Blocker created when contact_sheet.jpg is missing."""
        preview_dir = Path(project_dir, "output/preview")
        os.remove(str(preview_dir / "contact_sheet.jpg"))

        combine_build_preview_operator_delivery(_make_args(project_dir))

        blocker_path = Path(project_dir, "output/control/preview_operator_delivery_blocker.json")
        assert blocker_path.exists()

    def test_rejects_zero_byte_preview_artifact(self, project_dir):
        """Zero-byte artifact is treated as not existing."""
        preview_dir = Path(project_dir, "output/preview")
        (preview_dir / "preview_lowres.mp4").write_text("")

        combine_build_preview_operator_delivery(_make_args(project_dir))

        bundle = json.loads(Path(project_dir, "output/control/preview_operator_delivery_bundle.json").read_text())
        mp4 = [a for a in bundle["artifacts"] if a["name"] == "preview_lowres.mp4"][0]
        assert mp4["exists"] is False
        assert mp4["size_bytes"] == 0

    def test_blocker_sets_correct_next_action(self, project_dir):
        """Blocked state routes to reconciliation, not operator review."""
        preview_dir = Path(project_dir, "output/preview")
        os.remove(str(preview_dir / "preview_lowres.mp4"))

        combine_build_preview_operator_delivery(_make_args(project_dir))

        blocker = json.loads(Path(project_dir, "output/control/preview_operator_delivery_blocker.json").read_text())
        assert blocker["next_allowed_action"] == "preview_artifact_reconciliation_required"

        # Ledger should also reflect this
        ledger = json.loads(Path(project_dir, "output/control/episode_ledger.json").read_text())
        ev = [e for e in ledger if e.get("event") == "preview_artifacts_operator_delivery_checked"]
        assert len(ev) == 1
        assert ev[0]["next_allowed_action"] == "preview_artifact_reconciliation_required"

    def test_sha256_mismatch_creates_blocker(self, project_dir):
        """If sha256 doesn't match render report, blocker is created."""
        control_dir = Path(project_dir, "output/control")
        # Write a render report with a wrong sha256
        preview_dir = Path(project_dir, "output/preview")
        actual_sha = _sha256_of(preview_dir / "preview_lowres.mp4")
        wrong_sha = "a" * 64
        assert actual_sha != wrong_sha

        _write_json(control_dir / "preview_render_report.json", {
            "outputs": {
                "preview_lowres.mp4": {"size_bytes": 5000, "sha256": wrong_sha},
                "preview.gif": {"size_bytes": 3000, "sha256": _sha256_of(preview_dir / "preview.gif")},
                "contact_sheet.jpg": {"size_bytes": 2000, "sha256": _sha256_of(preview_dir / "contact_sheet.jpg")},
            },
        })

        combine_build_preview_operator_delivery(_make_args(project_dir))

        recon = json.loads(Path(project_dir, "output/control/preview_artifact_delivery_reconciliation.json").read_text())
        assert recon["all_sha256_match_render_report"] is False
        assert len(recon["sha256_mismatches"]) == 1
        assert recon["sha256_mismatches"][0]["artifact"] == "preview_lowres.mp4"
