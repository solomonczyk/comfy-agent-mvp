from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetryLoopAttempt:
    attempt_index: int
    prompt_id: str | None
    judge_status: str
    final_verdict: str | None
    final_score: float | None
    retry_action: str | None
    seed: int | None
    metadata_path: str | None = None
    summary_path: str | None = None
    images: list[dict[str, Any]] = field(default_factory=list)
    orchestrator_report: dict[str, Any] | None = None
    retry_decision: dict[str, Any] | None = None
    error_type: str | None = None
    error: str | None = None
    applied_retry_prompt: str | None = None
    applied_retry_settings: dict[str, Any] | None = None


@dataclass
class RetryLoopResult:
    attempts: list[RetryLoopAttempt]
    selected_attempt_index: int
    selected_reason: str
    loop_status: str   # single_pass | retried_once | failed
    best_result: dict[str, Any]


class AutoRetryLoop:
    def __init__(self, max_additional_attempts: int = 1) -> None:
        self.max_additional_attempts = max_additional_attempts

    @staticmethod
    def _extract_attempt(result: dict[str, Any], attempt_index: int) -> RetryLoopAttempt:
        orchestrator_report = result.get("orchestrator_report")
        retry_decision = result.get("retry_decision")

        return RetryLoopAttempt(
            attempt_index=attempt_index,
            prompt_id=result.get("prompt_id"),
            judge_status=result.get("judge_status", "unknown"),
            final_verdict=(orchestrator_report or {}).get("final_verdict"),
            final_score=(orchestrator_report or {}).get("final_score"),
            retry_action=(retry_decision or {}).get("action"),
            seed=result.get("seed"),
            metadata_path=result.get("metadata_path"),
            summary_path=result.get("summary_path"),
            images=copy.deepcopy(result.get("images", [])),
            orchestrator_report=copy.deepcopy(orchestrator_report),
            retry_decision=copy.deepcopy(retry_decision),
        )

    @staticmethod
    def _score_of(result: dict[str, Any]) -> float:
        report = result.get("orchestrator_report") or {}
        try:
            return float(report.get("final_score", 0.0))
        except Exception:
            return 0.0

    @staticmethod
    def _is_pass(result: dict[str, Any]) -> bool:
        return (result.get("judge_status") == "pass") or (
            (result.get("orchestrator_report") or {}).get("final_verdict") == "pass"
        )

    @staticmethod
    def _get_rank(result: dict[str, Any]) -> int:
        """Get rank of result: pass=3, retry=2, reject=1, failed=0."""
        if result.get("judge_status") == "failed":
            return 0
        if (result.get("judge_status") == "pass") or (
            (result.get("orchestrator_report") or {}).get("final_verdict") == "pass"
        ):
            return 3
        if (result.get("judge_status") == "reject") or (
            (result.get("orchestrator_report") or {}).get("final_verdict") == "reject"
        ):
            return 1
        return 2  # retry

    @staticmethod
    def _choose_better(first: dict[str, Any], second: dict[str, Any]) -> tuple[int, str, dict[str, Any]]:
        first_rank = AutoRetryLoop._get_rank(first)
        second_rank = AutoRetryLoop._get_rank(second)

        # Rank priority: pass > retry > reject > failed
        if second_rank > first_rank:
            return 2, f"second_attempt_higher_rank({second_rank})", second
        if first_rank > second_rank:
            return 1, f"first_attempt_higher_rank({first_rank})", first

        # Equal ranks - compare scores
        first_score = AutoRetryLoop._score_of(first)
        second_score = AutoRetryLoop._score_of(second)

        if second_score > first_score:
            return 2, "second_attempt_higher_score", second
        if first_score > second_score:
            return 1, "first_attempt_higher_score", first

        # Equal scores - keep first
        return 1, "first_attempt_kept_equal_rank_score", first

    @staticmethod
    def _apply_retry_decision(
        *,
        base_prompt: str,
        base_settings: dict[str, Any],
        retry_decision: dict[str, Any] | None,
    ) -> tuple[str, dict[str, Any]]:
        new_prompt = base_prompt
        new_settings = copy.deepcopy(base_settings)
        retry_decision = retry_decision or {}

        action = retry_decision.get("action")

        if action == "retry_seed":
            new_settings["seed"] = random.randint(1, 2**31 - 1)

        elif action == "retry_prompt":
            suffixes = retry_decision.get("suggested_prompt_suffixes") or []
            if suffixes:
                new_prompt = f"{base_prompt}. " + ", ".join(str(x) for x in suffixes)

        elif action == "retry_settings":
            updates = retry_decision.get("suggested_settings_updates") or {}
            for key, value in updates.items():
                new_settings[key] = value

            negative_additions = retry_decision.get("suggested_negative_additions") or []
            if negative_additions:
                current_negative = str(new_settings.get("negative_prompt") or "")
                extra = ", ".join(str(x) for x in negative_additions)
                new_settings["negative_prompt"] = (
                    f"{current_negative}, {extra}" if current_negative else extra
                )

        return new_prompt, new_settings

    async def run_once_retry(
        self,
        *,
        initial_result: dict[str, Any],
        user_prompt: str,
        final_prompt: str,
        final_settings: dict[str, Any],
        rerun_callable,
    ) -> RetryLoopResult:
        attempts: list[RetryLoopAttempt] = [
            self._extract_attempt(initial_result, attempt_index=1)
        ]

        if self.max_additional_attempts < 1:
            return RetryLoopResult(
                attempts=attempts,
                selected_attempt_index=1,
                selected_reason="retry_disabled",
                loop_status="single_pass",
                best_result=initial_result,
            )

        if initial_result.get("judge_status") != "retry":
            return RetryLoopResult(
                attempts=attempts,
                selected_attempt_index=1,
                selected_reason="initial_result_not_retry",
                loop_status="single_pass",
                best_result=initial_result,
            )

        retry_decision = initial_result.get("retry_decision") or {}
        retried_prompt, retried_settings = self._apply_retry_decision(
            base_prompt=final_prompt,
            base_settings=final_settings,
            retry_decision=retry_decision,
        )

        try:
            second_result = await rerun_callable(
                retry_prompt=retried_prompt,
                retry_settings=retried_settings,
            )

            # Check if second attempt failed (returned status=failed instead of raising exception)
            if second_result.get("status") == "failed":
                failed_attempt = RetryLoopAttempt(
                    attempt_index=2,
                    prompt_id=second_result.get("prompt_id"),
                    judge_status="failed",
                    final_verdict=None,
                    final_score=None,
                    retry_action=retry_decision.get("action"),
                    seed=retried_settings.get("seed"),
                    metadata_path=second_result.get("metadata_path"),
                    summary_path=second_result.get("summary_path"),
                    images=[],
                    orchestrator_report=None,
                    retry_decision=retry_decision,
                )
                # Add error info from failed result
                failed_attempt.error_type = second_result.get("error_type") or "GenerationFailed"
                failed_attempt.error = second_result.get("error") or second_result.get("failed_stage", "Unknown failure")
                failed_attempt.applied_retry_prompt = retried_prompt
                failed_attempt.applied_retry_settings = retried_settings

                attempts.append(failed_attempt)

                return RetryLoopResult(
                    attempts=attempts,
                    selected_attempt_index=1,
                    selected_reason=f"retry_failed: {second_result.get('failed_stage', 'status_failed')}",
                    loop_status="failed",
                    best_result=initial_result,
                )

            attempts.append(self._extract_attempt(second_result, attempt_index=2))
            # Add applied retry info to successful second attempt
            attempts[-1].applied_retry_prompt = retried_prompt
            attempts[-1].applied_retry_settings = retried_settings

            selected_attempt_index, selected_reason, best_result = self._choose_better(
                initial_result,
                second_result,
            )

            return RetryLoopResult(
                attempts=attempts,
                selected_attempt_index=selected_attempt_index,
                selected_reason=selected_reason,
                loop_status="retried_once",
                best_result=best_result,
            )

        except Exception as exc:
            # Rerun failed - create failed attempt record
            failed_attempt = RetryLoopAttempt(
                attempt_index=2,
                prompt_id=None,
                judge_status="failed",
                final_verdict=None,
                final_score=None,
                retry_action=retry_decision.get("action"),
                seed=retried_settings.get("seed"),
                metadata_path=None,
                summary_path=None,
                images=[],
                orchestrator_report=None,
                retry_decision=retry_decision,
            )
            # Add error info to the attempt
            failed_attempt.error_type = exc.__class__.__name__
            failed_attempt.error = str(exc)
            failed_attempt.applied_retry_prompt = retried_prompt
            failed_attempt.applied_retry_settings = retried_settings

            attempts.append(failed_attempt)

            return RetryLoopResult(
                attempts=attempts,
                selected_attempt_index=1,
                selected_reason=f"retry_failed: {exc.__class__.__name__}",
                loop_status="failed",
                best_result=initial_result,
            )
