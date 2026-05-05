"""RC-COMBINE-V2-861-920 — Test Corrective Retry Result Review.

Tests for the combine-review-corrective-retry-result CLI command.
Verifies result review:
- Branch A (success): asset collected -> stop before Visual QA
- Branch B (failed_collection): zero assets -> stop at result review
- Visual QA not executed
- Assembly not executed
- Downstream not executed
- Production accepted is false
"""

import json
import pytest
from pathlib import Path
from argparse import Namespace
import sys
import os

# Add app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.cli import combine_review_corrective_retry_result


class TestCorrectiveRetryResultReview:
    """Test corrective retry generation result review and gating."""

    def test_requires_generation_result(self, tmp_path):
        """Review must fail without generation result artifact."""
        args = Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result = combine_review_corrective_retry_result(args)
        assert result == 1

    def test_success_branch_stops_before_visual_qa(self, tmp_path):
        """Success branch must stop before visual QA (next_allowed_action = corrective_retry_visual_qa_preflight_required)."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create generation result with one asset
        gen_result = {
            "stage": "corrective_retry_generate_assets",
            "corrective_retry_package_used": True,
            "generation_attempts": 1,
            "max_generations": 1,
            "generated_assets": ["output/assets/test_asset.png"]
        }
        with open(control_dir / "combine_v2_corrective_retry_generation_result.json", 'w') as f:
            json.dump(gen_result, f)

        args = Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result = combine_review_corrective_retry_result(args)
        assert result == 0

        # Verify result review artifact
        review_path = control_dir / "combine_v2_corrective_retry_result_review.json"
        assert review_path.exists()
        with open(review_path) as f:
            review = json.load(f)

        assert review["branch_selected"] == "success"
        assert review["generated_assets_count"] == 1
        assert review["result_review_executed"] is True
        assert review["next_allowed_action"] == "corrective_retry_visual_qa_preflight_required"
        assert review["visual_qa_executed"] is False
        assert review["real_visual_qa_started"] is False
        assert review["operator_visual_decision_executed"] is False
        assert review["assembly_executed"] is False
        assert review["downstream_executed"] is False
        assert review["production_accepted"] is False

    def test_failed_collection_branch_stops_at_result_review(self, tmp_path):
        """Failed collection branch must stop at result review (next_allowed_action = corrective_retry_result_review_required)."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create generation result with zero assets
        gen_result = {
            "stage": "corrective_retry_generate_assets",
            "corrective_retry_package_used": True,
            "generation_attempts": 1,
            "max_generations": 1,
            "generated_assets": []
        }
        with open(control_dir / "combine_v2_corrective_retry_generation_result.json", 'w') as f:
            json.dump(gen_result, f)

        args = Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result = combine_review_corrective_retry_result(args)
        assert result == 0

        # Verify result review artifact
        review_path = control_dir / "combine_v2_corrective_retry_result_review.json"
        assert review_path.exists()
        with open(review_path) as f:
            review = json.load(f)

        assert review["branch_selected"] == "failed_collection"
        assert review["generated_assets_count"] == 0
        assert review["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"
        assert review["result_review_executed"] is True
        assert review["next_allowed_action"] == "corrective_retry_result_review_required"
        assert review["visual_qa_executed"] is False
        assert review["real_visual_qa_started"] is False
        assert review["assembly_executed"] is False
        assert review["downstream_executed"] is False
        assert review["production_accepted"] is False

    def test_visual_qa_entry_decision_created_for_success(self, tmp_path):
        """Visual QA entry decision artifact must be created for success branch."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        gen_result = {
            "stage": "corrective_retry_generate_assets",
            "generated_assets": ["output/assets/test.png"]
        }
        with open(control_dir / "combine_v2_corrective_retry_generation_result.json", 'w') as f:
            json.dump(gen_result, f)

        args = Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result = combine_review_corrective_retry_result(args)
        assert result == 0

        visual_qa_path = control_dir / "combine_v2_corrective_retry_visual_qa_entry_decision.json"
        assert visual_qa_path.exists()
        with open(visual_qa_path) as f:
            vqa = json.load(f)

        assert vqa["visual_qa_required"] is True
        assert vqa["visual_qa_executed"] is False
        assert vqa["real_visual_qa_started"] is False
        assert vqa["operator_visual_decision_required"] is True
        assert vqa["production_accepted"] is False

    def test_visual_qa_entry_decision_created_for_failure(self, tmp_path):
        """Visual QA entry decision artifact must be created for failed_collection branch."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        gen_result = {
            "stage": "corrective_retry_generate_assets",
            "generated_assets": []
        }
        with open(control_dir / "combine_v2_corrective_retry_generation_result.json", 'w') as f:
            json.dump(gen_result, f)

        args = Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result = combine_review_corrective_retry_result(args)
        assert result == 0

        visual_qa_path = control_dir / "combine_v2_corrective_retry_visual_qa_entry_decision.json"
        assert visual_qa_path.exists()
        with open(visual_qa_path) as f:
            vqa = json.load(f)

        assert vqa["visual_qa_required"] is False
        assert vqa["visual_qa_executed"] is False
        assert vqa["real_visual_qa_started"] is False
        assert vqa["operator_visual_decision_required"] is False
        assert vqa["production_accepted"] is False

    def test_artifact_index_updated(self, tmp_path):
        """Artifact index must be updated with review state."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        gen_result = {
            "stage": "corrective_retry_generate_assets",
            "generated_assets": []
        }
        with open(control_dir / "combine_v2_corrective_retry_generation_result.json", 'w') as f:
            json.dump(gen_result, f)

        args = Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result = combine_review_corrective_retry_result(args)
        assert result == 0

        index_path = control_dir / "artifact_index.json"
        assert index_path.exists()
        with open(index_path) as f:
            index = json.load(f)

        assert index["branch_selected"] == "failed_collection"
        assert index["generated_assets_count"] == 0
        assert index["result_review_executed"] is True
        assert index["visual_qa_executed"] is False
        assert index["real_visual_qa_started"] is False
        assert index["assembly_executed"] is False
        assert index["downstream_executed"] is False
        assert index["production_accepted"] is False

    def test_ledger_updated(self, tmp_path):
        """Episode ledger must record review event."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        gen_result = {
            "stage": "corrective_retry_generate_assets",
            "generated_assets": ["output/assets/test.png"]
        }
        with open(control_dir / "combine_v2_corrective_retry_generation_result.json", 'w') as f:
            json.dump(gen_result, f)

        args = Namespace(
            project_root=str(tmp_path),
            json=True
        )

        result = combine_review_corrective_retry_result(args)
        assert result == 0

        ledger_path = control_dir / "episode_ledger.json"
        assert ledger_path.exists()
        with open(ledger_path) as f:
            ledger = json.load(f)

        assert isinstance(ledger, list)
        assert len(ledger) >= 1
        last_event = ledger[-1]
        assert last_event["event_type"] == "corrective_retry_result_review_completed"
        assert last_event["result_review_executed"] is True
        assert last_event["branch_selected"] == "success"
        assert last_event["visual_qa_executed"] is False
        assert last_event["assembly_executed"] is False
        assert last_event["downstream_executed"] is False
