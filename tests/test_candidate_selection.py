"""Tests for Candidate Selection Policy Hardening v0.

Scenarios 21-28 verify that the unified candidate selection policy
works correctly across retry, workflow switch, and general multi-attempt scenarios.
"""

import pytest

from app.agent.candidate_selection import (
    CandidateSelectionPolicy,
    SelectionReason,
    VerdictRank,
)


class TestCandidateSelectionPolicy:
    """Test unified candidate selection policy."""

    def test_scenario_21_pass_beats_retry_even_with_lower_score(self):
        """Scenario 21: pass beats retry even with lower score."""
        policy = CandidateSelectionPolicy()
        
        candidates = [
            {
                "candidate_id": "cand_a",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "retry",
                "orchestrator_report": {"final_verdict": "retry", "final_score": 9.5},
            },
            {
                "candidate_id": "cand_b",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "pass",
                "orchestrator_report": {"final_verdict": "pass", "final_score": 7.5},
            },
        ]
        
        decision = policy.select_best_candidate(candidates)
        
        assert decision.selected_candidate_id == "cand_b"
        assert decision.selected_attempt_index == 2
        assert decision.selection_reason == SelectionReason.HIGHER_VERDICT_RANK
        assert decision.ranking_snapshot[0]["candidate_id"] == "cand_b"
        assert decision.ranking_snapshot[0]["rank"] == 1
        assert decision.ranking_snapshot[1]["candidate_id"] == "cand_a"
        assert decision.ranking_snapshot[1]["rank"] == 2

    def test_scenario_22_retry_beats_reject_even_with_higher_score(self):
        """Scenario 22: retry beats reject even if reject score is numerically higher."""
        policy = CandidateSelectionPolicy()
        
        candidates = [
            {
                "candidate_id": "cand_a",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "reject",
                "orchestrator_report": {"final_verdict": "reject", "final_score": 9.0},
            },
            {
                "candidate_id": "cand_b",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "retry",
                "orchestrator_report": {"final_verdict": "retry", "final_score": 6.0},
            },
        ]
        
        decision = policy.select_best_candidate(candidates)
        
        assert decision.selected_candidate_id == "cand_b"
        assert decision.selected_attempt_index == 2
        assert decision.selection_reason == SelectionReason.HIGHER_VERDICT_RANK

    def test_scenario_23_reject_beats_failed(self):
        """Scenario 23: reject beats failed."""
        policy = CandidateSelectionPolicy()
        
        candidates = [
            {
                "candidate_id": "cand_a",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "failed",
                "orchestrator_report": {"final_verdict": "failed", "final_score": 0.0},
            },
            {
                "candidate_id": "cand_b",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "reject",
                "orchestrator_report": {"final_verdict": "reject", "final_score": 0.0},
            },
        ]
        
        decision = policy.select_best_candidate(candidates)
        
        assert decision.selected_candidate_id == "cand_b"
        assert decision.selected_attempt_index == 2
        assert decision.selection_reason == SelectionReason.HIGHER_VERDICT_RANK

    def test_scenario_24_tie_keeps_earlier_candidate(self):
        """Scenario 24: tie keeps earlier candidate."""
        policy = CandidateSelectionPolicy()
        
        candidates = [
            {
                "candidate_id": "cand_a",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "pass",
                "orchestrator_report": {"final_verdict": "pass", "final_score": 8.5},
            },
            {
                "candidate_id": "cand_b",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "pass",
                "orchestrator_report": {"final_verdict": "pass", "final_score": 8.5},
            },
        ]
        
        decision = policy.select_best_candidate(candidates)
        
        assert decision.selected_candidate_id == "cand_a"
        assert decision.selected_attempt_index == 1
        assert decision.selection_reason == SelectionReason.TIE_KEEP_EARLIER_CANDIDATE

    def test_scenario_25_missing_score_handled_safely(self):
        """Scenario 25: missing score handled safely."""
        policy = CandidateSelectionPolicy()
        
        candidates = [
            {
                "candidate_id": "cand_a",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "pass",
                "orchestrator_report": {"final_verdict": "pass"},  # No final_score
            },
            {
                "candidate_id": "cand_b",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "retry",
                "orchestrator_report": {"final_verdict": "retry", "final_score": 7.0},
            },
        ]
        
        decision = policy.select_best_candidate(candidates)
        
        # Should not crash, and pass should still win due to verdict rank
        assert decision.selected_candidate_id == "cand_a"
        assert decision.selected_attempt_index == 1
        assert decision.selection_reason == SelectionReason.HIGHER_VERDICT_RANK

    def test_scenario_26_workflow_switch_and_retry_use_same_selection_policy(self):
        """Scenario 26: workflow switch and retry use same selection policy."""
        policy = CandidateSelectionPolicy()
        
        # Simulate retry scenario
        retry_candidates = [
            {
                "candidate_id": "cand_initial",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "retry",
                "orchestrator_report": {"final_verdict": "retry", "final_score": 6.0},
            },
            {
                "candidate_id": "cand_retry",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "pass",
                "orchestrator_report": {"final_verdict": "pass", "final_score": 8.0},
            },
        ]
        
        retry_decision = policy.select_best_candidate(retry_candidates)
        
        # Simulate workflow switch scenario
        switch_candidates = [
            {
                "candidate_id": "cand_initial",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "retry",
                "orchestrator_report": {"final_verdict": "retry", "final_score": 6.0},
            },
            {
                "candidate_id": "cand_switched",
                "execution_plan": {"workflow_id": "sdxl_portrait"},
                "judge_status": "pass",
                "orchestrator_report": {"final_verdict": "pass", "final_score": 7.5},
            },
        ]
        
        switch_decision = policy.select_best_candidate(switch_candidates)
        
        # Both should select the pass candidate (higher verdict rank)
        assert retry_decision.selected_candidate_id == "cand_retry"
        assert switch_decision.selected_candidate_id == "cand_switched"
        # Both should have the same selection reason (higher verdict rank)
        assert retry_decision.selection_reason == SelectionReason.HIGHER_VERDICT_RANK
        assert switch_decision.selection_reason == SelectionReason.HIGHER_VERDICT_RANK

    def test_scenario_27_summary_shows_selected_workflow_task_retry_loop_status(self):
        """Scenario 27: summary shows selected workflow/task/retry_loop_status."""
        from app.services.run_metadata import RunMetadataService
        import tempfile
        
        # Create a result with candidate_selection
        result = {
            "status": "completed",
            "user_prompt": "test prompt",
            "candidate_history": {
                "selected_candidate_id": "cand_b",
                "selected_attempt_index": 2,
                "selection_reason": "higher_verdict_rank",
                "attempts": [
                    {
                        "attempt_index": 1,
                        "candidate_id": "cand_a",
                        "workflow_id": "sdxl_text_to_image",
                        "task_type": "text_to_image",
                        "judge_status": "retry",
                    },
                    {
                        "attempt_index": 2,
                        "candidate_id": "cand_b",
                        "workflow_id": "sdxl_portrait",
                        "task_type": "portrait",
                        "judge_status": "pass",
                    },
                ],
            },
            "candidate_selection": {
                "selected_candidate_id": "cand_b",
                "selected_attempt_index": 2,
                "selection_reason": "higher_verdict_rank",
                "selected_workflow_id": "sdxl_portrait",
                "ranking_snapshot": [],
            },
            "retry_loop": {
                "loop_status": "completed",
                "attempts": [],
                "selected_attempt_index": 2,
            },
            "images": [{"filename": "image.png"}],
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_service = RunMetadataService(tmpdir)
            persisted = metadata_service.persist_terminal_report(result)
            
            # Read the summary file
            summary_path = persisted["summary_path"]
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_text = f.read()
            
            # Verify summary contains the required fields
            assert "selected_workflow_id: sdxl_portrait" in summary_text
            assert "selected_task_type: portrait" in summary_text
            assert "retry_loop_status: completed" in summary_text
            assert "candidate_selection_reason: higher_verdict_rank" in summary_text

    def test_scenario_28_candidate_selection_block_matches_top_level_selected_result(self):
        """Scenario 28: candidate_selection block matches top-level selected result."""
        policy = CandidateSelectionPolicy()
        
        candidates = [
            {
                "candidate_id": "cand_a",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "retry",
                "orchestrator_report": {"final_verdict": "retry", "final_score": 6.0},
            },
            {
                "candidate_id": "cand_b",
                "execution_plan": {"workflow_id": "sdxl_portrait"},
                "judge_status": "pass",
                "orchestrator_report": {"final_verdict": "pass", "final_score": 8.5},
            },
        ]
        
        decision = policy.select_best_candidate(candidates)
        
        # The decision should match the best candidate
        assert decision.selected_candidate_id == "cand_b"
        assert decision.selected_attempt_index == 2
        assert decision.selected_workflow_id == "sdxl_portrait"
        
        # Verify ranking snapshot has correct order
        assert len(decision.ranking_snapshot) == 2
        assert decision.ranking_snapshot[0]["candidate_id"] == "cand_b"
        assert decision.ranking_snapshot[0]["rank"] == 1
        assert decision.ranking_snapshot[1]["candidate_id"] == "cand_a"
        assert decision.ranking_snapshot[1]["rank"] == 2

    def test_only_candidate_available(self):
        """Test that single candidate returns only_candidate_available reason."""
        policy = CandidateSelectionPolicy()
        
        candidates = [
            {
                "candidate_id": "cand_a",
                "execution_plan": {"workflow_id": "sdxl_text_to_image"},
                "judge_status": "pass",
                "orchestrator_report": {"final_verdict": "pass", "final_score": 8.5},
            },
        ]
        
        decision = policy.select_best_candidate(candidates)
        
        assert decision.selected_candidate_id == "cand_a"
        assert decision.selected_attempt_index == 1
        assert decision.selection_reason == SelectionReason.ONLY_CANDIDATE_AVAILABLE

    def test_verdict_normalization(self):
        """Test verdict normalization handles various formats."""
        policy = CandidateSelectionPolicy()
        
        # Test different verdict formats
        assert policy._normalize_verdict("pass") == VerdictRank.PASS
        assert policy._normalize_verdict("PASS") == VerdictRank.PASS
        assert policy._normalize_verdict("Pass") == VerdictRank.PASS
        assert policy._normalize_verdict("retry") == VerdictRank.RETRY
        assert policy._normalize_verdict("RETRY") == VerdictRank.RETRY
        assert policy._normalize_verdict("reject") == VerdictRank.REJECT
        assert policy._normalize_verdict("failed") == VerdictRank.FAILED
        assert policy._normalize_verdict("unknown") == VerdictRank.UNKNOWN
        assert policy._normalize_verdict(None) == VerdictRank.UNKNOWN
        assert policy._normalize_verdict("some_pass_result") == VerdictRank.PASS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
