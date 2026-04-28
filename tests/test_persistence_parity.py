"""Tests for Persistence + Metadata Parity Hardening v0.

Scenarios 15-20 verify that persisted metadata/summary/terminal report
are aligned with unified agent result contract, including workflow_switch,
retry_loop, and candidate_history.
"""

import json
import tempfile
from pathlib import Path

import pytest

from app.agent.candidate_history import CandidateHistory, AttemptRecord, AttemptRecordBuilder
from app.agent.result_contract import AgentResult, build_agent_result
from app.services.run_metadata import RunMetadataService


class TestPersistenceParity:
    """Test parity between runtime result and persisted metadata."""

    def test_scenario_15_persisted_metadata_contains_candidate_history(self):
        """Scenario 15: persisted metadata contains candidate_history."""
        # Create a candidate history with multiple attempts
        history = CandidateHistory()
        attempt1 = AttemptRecordBuilder() \
            .attempt_index(1) \
            .candidate_id("cand_12345678") \
            .attempt_kind("initial") \
            .workflow_id("sdxl_text_to_image") \
            .task_type("text_to_image") \
            .judge_status("pass") \
            .final_verdict("pass") \
            .final_score(0.85) \
            .selected(True) \
            .selection_reason("initial_candidate_kept") \
            .images([{"filename": "image1.png"}]) \
            .build()
        attempt2 = AttemptRecordBuilder() \
            .attempt_index(2) \
            .candidate_id("cand_87654321") \
            .parent_candidate_id("cand_12345678") \
            .attempt_kind("retry_seed") \
            .workflow_id("sdxl_text_to_image") \
            .task_type("text_to_image") \
            .judge_status("retry") \
            .final_verdict("retry") \
            .final_score(0.72) \
            .selected(False) \
            .images([{"filename": "image2.png"}]) \
            .build()
        history.add_attempt(attempt1)
        history.add_attempt(attempt2)
        history.mark_selected("cand_12345678", 1, "initial_candidate_kept")

        # Create a unified agent result with candidate_history
        result = build_agent_result(
            status="completed",
            user_prompt="test prompt",
            candidate_history=history.to_dict(),
            images=[{"filename": "image1.png"}],
        )

        # Persist the result
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_service = RunMetadataService(tmpdir)
            persisted = metadata_service.persist_terminal_report(result.to_dict())

            # Verify candidate_history is preserved
            assert "candidate_history" in persisted
            assert persisted["candidate_history"] is not None
            assert persisted["candidate_history"]["selected_candidate_id"] == "cand_12345678"
            assert persisted["candidate_history"]["selected_attempt_index"] == 1
            assert len(persisted["candidate_history"]["attempts"]) == 2
            assert persisted["candidate_history"]["attempts"][0]["attempt_index"] == 1
            assert persisted["candidate_history"]["attempts"][1]["attempt_index"] == 2

    def test_scenario_16_persisted_metadata_contains_workflow_switch(self):
        """Scenario 16: persisted metadata contains workflow_switch."""
        # Create a unified agent result with workflow_switch
        workflow_switch = {
            "switch_applied": True,
            "from_workflow_id": "sdxl_text_to_image",
            "to_workflow_id": "sdxl_portrait",
            "switch_reason": "portrait task detected",
            "source_trigger": "judge_decision",
            "switch_allowed": True,
            "missing_inputs": [],
            "notes": [],
            "selected_candidate_workflow_id": "sdxl_portrait",
        }

        result = build_agent_result(
            status="completed",
            user_prompt="test prompt",
            workflow_switch=workflow_switch,
            images=[{"filename": "image1.png"}],
        )

        # Persist the result
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_service = RunMetadataService(tmpdir)
            persisted = metadata_service.persist_terminal_report(result.to_dict())

            # Verify workflow_switch is preserved
            assert "workflow_switch" in persisted
            assert persisted["workflow_switch"] is not None
            assert persisted["workflow_switch"]["switch_applied"] == True
            assert persisted["workflow_switch"]["from_workflow_id"] == "sdxl_text_to_image"
            assert persisted["workflow_switch"]["to_workflow_id"] == "sdxl_portrait"

    def test_scenario_17_summary_reflects_selected_candidate(self):
        """Scenario 17: summary reflects selected candidate."""
        # Create a candidate history with selected candidate
        history = CandidateHistory()
        attempt1 = AttemptRecordBuilder() \
            .attempt_index(1) \
            .candidate_id("cand_12345678") \
            .attempt_kind("initial") \
            .workflow_id("sdxl_text_to_image") \
            .judge_status("pass") \
            .selected(True) \
            .selection_reason("best_score") \
            .images([{"filename": "image1.png"}]) \
            .build()
        attempt2 = AttemptRecordBuilder() \
            .attempt_index(2) \
            .candidate_id("cand_87654321") \
            .parent_candidate_id("cand_12345678") \
            .attempt_kind("workflow_switch") \
            .workflow_id("sdxl_portrait") \
            .judge_status("retry") \
            .selected(False) \
            .images([{"filename": "image2.png"}]) \
            .build()
        history.add_attempt(attempt1)
        history.add_attempt(attempt2)
        history.mark_selected("cand_12345678", 1, "best_score")

        result = build_agent_result(
            status="completed",
            user_prompt="test prompt",
            candidate_history=history.to_dict(),
            images=[{"filename": "image1.png"}],
        )

        # Persist the result
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_service = RunMetadataService(tmpdir)
            persisted = metadata_service.persist_terminal_report(result.to_dict())

            # Read the summary file
            summary_path = Path(persisted["summary_path"])
            summary_text = summary_path.read_text(encoding="utf-8")

            # Verify summary contains selected candidate info
            assert "selected_candidate_id: cand_12345678" in summary_text
            assert "selected_attempt_index: 1" in summary_text
            assert "selection_reason: best_score" in summary_text
            assert "attempts_count: 2" in summary_text

    def test_scenario_18_persisted_paths_match_selected_candidate(self):
        """Scenario 18: persisted paths match selected candidate."""
        # Create a candidate history where second attempt is selected
        history = CandidateHistory()
        attempt1 = AttemptRecordBuilder() \
            .attempt_index(1) \
            .candidate_id("cand_12345678") \
            .attempt_kind("initial") \
            .workflow_id("sdxl_text_to_image") \
            .judge_status("retry") \
            .selected(False) \
            .metadata_path("/path/to/first_metadata.json") \
            .summary_path("/path/to/first_summary.txt") \
            .images([{"filename": "image1.png"}]) \
            .build()
        attempt2 = AttemptRecordBuilder() \
            .attempt_index(2) \
            .candidate_id("cand_87654321") \
            .parent_candidate_id("cand_12345678") \
            .attempt_kind("retry_seed") \
            .workflow_id("sdxl_text_to_image") \
            .judge_status("pass") \
            .selected(True) \
            .selection_reason("retry_candidate_won") \
            .metadata_path("/path/to/second_metadata.json") \
            .summary_path("/path/to/second_summary.txt") \
            .images([{"filename": "image2.png"}]) \
            .build()
        history.add_attempt(attempt1)
        history.add_attempt(attempt2)
        history.mark_selected("cand_87654321", 2, "retry_candidate_won")

        result = build_agent_result(
            status="completed",
            user_prompt="test prompt",
            candidate_history=history.to_dict(),
            images=[{"filename": "image2.png"}],
        )

        # Persist the result
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_service = RunMetadataService(tmpdir)
            persisted = metadata_service.persist_terminal_report(result.to_dict())

            # Verify paths match selected candidate (second attempt)
            assert persisted["metadata_path"] == "/path/to/second_metadata.json"
            assert persisted["summary_path"] == "/path/to/second_summary.txt"

    def test_scenario_19_failed_candidate_preserved_in_metadata(self):
        """Scenario 19: failed candidate preserved in metadata."""
        # Create a candidate history with a failed attempt
        history = CandidateHistory()
        attempt1 = AttemptRecordBuilder() \
            .attempt_index(1) \
            .candidate_id("cand_12345678") \
            .attempt_kind("initial") \
            .workflow_id("sdxl_text_to_image") \
            .judge_status("failed") \
            .error_type("generation_error") \
            .error_code("GENERATION_FAILED") \
            .error("Generation failed: timeout") \
            .selected(False) \
            .images([]) \
            .build()
        attempt2 = AttemptRecordBuilder() \
            .attempt_index(2) \
            .candidate_id("cand_87654321") \
            .parent_candidate_id("cand_12345678") \
            .attempt_kind("retry_seed") \
            .workflow_id("sdxl_text_to_image") \
            .judge_status("pass") \
            .selected(True) \
            .selection_reason("retry_succeeded") \
            .images([{"filename": "image2.png"}]) \
            .build()
        history.add_attempt(attempt1)
        history.add_attempt(attempt2)
        history.mark_selected("cand_87654321", 2, "retry_succeeded")

        result = build_agent_result(
            status="completed",
            user_prompt="test prompt",
            candidate_history=history.to_dict(),
            images=[{"filename": "image2.png"}],
        )

        # Persist the result
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_service = RunMetadataService(tmpdir)
            persisted = metadata_service.persist_terminal_report(result.to_dict())

            # Verify failed candidate is preserved in history
            assert "candidate_history" in persisted
            attempts = persisted["candidate_history"]["attempts"]
            assert len(attempts) == 2
            # Failed attempt (attempt 1) should be preserved
            assert attempts[0]["attempt_index"] == 1
            assert attempts[0]["judge_status"] == "failed"
            assert attempts[0]["error_type"] == "generation_error"
            assert attempts[0]["error_code"] == "GENERATION_FAILED"
            assert attempts[0]["error"] == "Generation failed: timeout"
            # Successful attempt (attempt 2) should also be preserved
            assert attempts[1]["attempt_index"] == 2
            assert attempts[1]["judge_status"] == "pass"

    def test_scenario_20_schema_parity_runtime_to_persisted(self):
        """Scenario 20: schema parity between runtime result and persisted JSON."""
        # Create a comprehensive unified agent result
        history = CandidateHistory()
        attempt1 = AttemptRecordBuilder() \
            .attempt_index(1) \
            .candidate_id("cand_12345678") \
            .attempt_kind("initial") \
            .workflow_id("sdxl_text_to_image") \
            .task_type("text_to_image") \
            .judge_status("pass") \
            .selected(True) \
            .images([{"filename": "image1.png"}]) \
            .build()
        history.add_attempt(attempt1)
        history.mark_selected("cand_12345678", 1, "initial_candidate_kept")

        workflow_switch = {
            "switch_applied": False,
            "from_workflow_id": "sdxl_text_to_image",
            "to_workflow_id": None,
            "switch_reason": None,
            "source_trigger": None,
            "switch_allowed": False,
            "missing_inputs": [],
            "notes": [],
        }

        retry_loop = {
            "loop_status": "not_triggered",
            "attempts": [],
            "selected_attempt_index": 1,
        }

        runtime_result = build_agent_result(
            status="completed",
            user_prompt="test prompt",
            task_selection={"task_type": "text_to_image", "confidence": 0.9},
            execution_plan={"workflow_id": "sdxl_text_to_image", "user_prompt": "test prompt"},
            mutation_report={"applied_changes": {"seed": 12345}},
            judge_status="pass",
            orchestrator_report={"final_verdict": "pass", "final_score": 0.85},
            retry_decision={"action": "accept"},
            retry_loop=retry_loop,
            workflow_switch=workflow_switch,
            candidate_history=history.to_dict(),
            images=[{"filename": "image1.png"}],
        )

        # Persist the result
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_service = RunMetadataService(tmpdir)
            persisted = metadata_service.persist_terminal_report(runtime_result.to_dict())

            # Read the persisted JSON file
            metadata_path = Path(persisted["metadata_path"])
            persisted_json = json.loads(metadata_path.read_text(encoding="utf-8"))

            # Verify all load-bearing fields are present
            load_bearing_fields = [
                "status",
                "user_prompt",
                "task_selection",
                "execution_plan",
                "mutation_report",
                "judge_status",
                "orchestrator_report",
                "retry_decision",
                "retry_loop",
                "workflow_switch",
                "candidate_history",
                "images",
                "metadata_path",
                "summary_path",
            ]

            for field in load_bearing_fields:
                assert field in persisted_json, f"Field {field} missing from persisted JSON"

            # Verify values match runtime result
            assert persisted_json["status"] == runtime_result.status
            assert persisted_json["user_prompt"] == runtime_result.user_prompt
            assert persisted_json["candidate_history"]["selected_candidate_id"] == "cand_12345678"
            assert persisted_json["workflow_switch"]["switch_applied"] == False
            assert persisted_json["retry_loop"]["loop_status"] == "not_triggered"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
