"""Candidate selection policy for unified multi-attempt agent.

This module provides a single source of truth for selecting the best candidate
across retry, workflow switch, and general multi-attempt scenarios.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SelectionReason(str, Enum):
    """Normalized selection reason codes."""
    
    ONLY_CANDIDATE_AVAILABLE = "only_candidate_available"
    HIGHER_VERDICT_RANK = "higher_verdict_rank"
    HIGHER_FINAL_SCORE = "higher_final_score"
    TIE_KEEP_EARLIER_CANDIDATE = "tie_keep_earlier_candidate"
    FAILED_CANDIDATE_REJECTED = "failed_candidate_rejected"
    WORKFLOW_SWITCH_CANDIDATE_WON = "workflow_switch_candidate_won"
    RETRY_CANDIDATE_WON = "retry_candidate_won"
    INITIAL_CANDIDATE_KEPT = "initial_candidate_kept"


class VerdictRank(str, Enum):
    """Normalized verdict ranking for candidate comparison."""
    
    PASS = "pass"
    RETRY = "retry"
    REJECT = "reject"
    FAILED = "failed"
    NO_IMAGES = "no_images"
    UNKNOWN = "unknown"


@dataclass
class CandidateSelectionDecision:
    """Decision result from candidate selection policy.
    
    This dataclass represents the canonical selection decision with full
    ranking snapshot for debugging and operational visibility.
    """
    selected_candidate_id: str
    selected_attempt_index: int
    selection_reason: SelectionReason
    selected_workflow_id: str | None = None
    ranking_snapshot: list[dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "selected_candidate_id": self.selected_candidate_id,
            "selected_attempt_index": self.selected_attempt_index,
            "selection_reason": self.selection_reason.value,
            "selected_workflow_id": self.selected_workflow_id,
            "ranking_snapshot": self.ranking_snapshot,
        }


class CandidateSelectionPolicy:
    """Unified policy for selecting the best candidate from multiple attempts.
    
    This policy provides a single source of truth for candidate selection
    across retry, workflow switch, and general multi-attempt scenarios.
    """
    
    # Verdict priority: lower value = higher priority
    VERDICT_PRIORITY = {
        VerdictRank.PASS: 0,
        VerdictRank.RETRY: 1,
        VerdictRank.REJECT: 2,
        VerdictRank.FAILED: 3,
        VerdictRank.NO_IMAGES: 4,
        VerdictRank.UNKNOWN: 5,
    }
    
    def select_best_candidate(
        self,
        candidates: list[dict[str, Any]],
    ) -> CandidateSelectionDecision:
        """Select the best candidate from a list of candidates.
        
        Args:
            candidates: List of candidate dictionaries with judge data
            
        Returns:
            CandidateSelectionDecision with selected candidate and ranking snapshot
        """
        if not candidates:
            raise ValueError("No candidates to select from")
        
        if len(candidates) == 1:
            return self._build_single_candidate_decision(candidates[0], 1)
        
        # Rank all candidates
        ranked_candidates = self._rank_candidates(candidates)
        
        # Select the best (highest rank = lowest priority value)
        best_ranked = ranked_candidates[0]
        selected_index = best_ranked["attempt_index"]
        selected_candidate = candidates[selected_index - 1]  # Convert to 0-based
        
        # Determine selection reason
        selection_reason = self._determine_selection_reason(
            ranked_candidates,
            selected_index,
        )
        
        # Build ranking snapshot
        ranking_snapshot = [
            {
                "candidate_id": rc["candidate_id"],
                "attempt_index": rc["attempt_index"],
                "workflow_id": rc["workflow_id"],
                "judge_status": rc["judge_status"],
                "final_verdict": rc["final_verdict"],
                "final_score": rc["final_score"],
                "rank": idx + 1,  # 1-based rank
            }
            for idx, rc in enumerate(ranked_candidates)
        ]
        
        return CandidateSelectionDecision(
            selected_candidate_id=best_ranked["candidate_id"],
            selected_attempt_index=selected_index,
            selection_reason=selection_reason,
            selected_workflow_id=best_ranked["workflow_id"],
            ranking_snapshot=ranking_snapshot,
        )
    
    def _build_single_candidate_decision(
        self,
        candidate: dict[str, Any],
        attempt_index: int,
    ) -> CandidateSelectionDecision:
        """Build decision when only one candidate is available."""
        # Extract candidate_id from candidate dict or generate one
        candidate_id = candidate.get("candidate_id") or f"cand_{attempt_index}"
        workflow_id = candidate.get("execution_plan", {}).get("workflow_id")
        
        return CandidateSelectionDecision(
            selected_candidate_id=candidate_id,
            selected_attempt_index=attempt_index,
            selection_reason=SelectionReason.ONLY_CANDIDATE_AVAILABLE,
            selected_workflow_id=workflow_id,
            ranking_snapshot=[
                {
                    "candidate_id": candidate_id,
                    "attempt_index": attempt_index,
                    "workflow_id": workflow_id,
                    "judge_status": candidate.get("judge_status"),
                    "final_verdict": candidate.get("orchestrator_report", {}).get("final_verdict"),
                    "final_score": candidate.get("orchestrator_report", {}).get("final_score"),
                    "rank": 1,
                }
            ],
        )
    
    def _rank_candidates(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Rank candidates by verdict priority and score.
        
        Args:
            candidates: List of candidate dictionaries
            
        Returns:
            List of ranked candidates (best first)
        """
        # Extract ranking data from each candidate
        ranking_data = []
        for idx, candidate in enumerate(candidates):
            attempt_index = idx + 1  # 1-based
            judge_status = candidate.get("judge_status", "unknown")
            orchestrator_report = candidate.get("orchestrator_report", {})
            final_verdict = orchestrator_report.get("final_verdict", judge_status)
            final_score = orchestrator_report.get("final_score", 0.0)
            workflow_id = candidate.get("execution_plan", {}).get("workflow_id")
            candidate_id = candidate.get("candidate_id") or f"cand_{attempt_index}"
            
            # Normalize verdict to enum
            verdict_rank = self._normalize_verdict(final_verdict)
            
            ranking_data.append({
                "candidate_id": candidate_id,
                "attempt_index": attempt_index,
                "workflow_id": workflow_id,
                "judge_status": judge_status,
                "final_verdict": final_verdict,
                "final_score": final_score,
                "verdict_rank": verdict_rank,
            })
        
        # Sort by verdict priority (lower = better), then by score (higher = better), then by attempt_index (lower = earlier)
        ranking_data.sort(key=lambda x: (
            self.VERDICT_PRIORITY.get(x["verdict_rank"], 99),
            -x["final_score"],  # Negative for descending sort
            x["attempt_index"],
        ))
        
        return ranking_data
    
    def _normalize_verdict(self, verdict: str | None) -> VerdictRank:
        """Normalize verdict string to VerdictRank enum.
        
        Args:
            verdict: Verdict string from judge
            
        Returns:
            Normalized VerdictRank
        """
        if not verdict:
            return VerdictRank.UNKNOWN
        
        verdict_lower = verdict.lower()
        
        # Direct matches
        if verdict_lower == "pass":
            return VerdictRank.PASS
        if verdict_lower == "retry":
            return VerdictRank.RETRY
        if verdict_lower == "reject":
            return VerdictRank.REJECT
        if verdict_lower == "failed":
            return VerdictRank.FAILED
        if verdict_lower == "no_images":
            return VerdictRank.NO_IMAGES
        
        # Fuzzy matches
        if "pass" in verdict_lower:
            return VerdictRank.PASS
        if "retry" in verdict_lower:
            return VerdictRank.RETRY
        if "reject" in verdict_lower:
            return VerdictRank.REJECT
        if "fail" in verdict_lower:
            return VerdictRank.FAILED
        
        return VerdictRank.UNKNOWN
    
    def _determine_selection_reason(
        self,
        ranked_candidates: list[dict[str, Any]],
        selected_index: int,
    ) -> SelectionReason:
        """Determine the normalized selection reason.
        
        Args:
            ranked_candidates: List of ranked candidates
            selected_index: Index of selected candidate (1-based)
            
        Returns:
            Normalized SelectionReason
        """
        if len(ranked_candidates) == 1:
            return SelectionReason.ONLY_CANDIDATE_AVAILABLE
        
        best = ranked_candidates[0]
        second = ranked_candidates[1] if len(ranked_candidates) > 1 else None
        
        if not second:
            return SelectionReason.ONLY_CANDIDATE_AVAILABLE
        
        # Check if selected by verdict rank
        if best["verdict_rank"] != second["verdict_rank"]:
            return SelectionReason.HIGHER_VERDICT_RANK
        
        # Check if selected by score
        if best["final_score"] != second["final_score"]:
            return SelectionReason.HIGHER_FINAL_SCORE
        
        # Tie - keep earlier candidate
        return SelectionReason.TIE_KEEP_EARLIER_CANDIDATE
