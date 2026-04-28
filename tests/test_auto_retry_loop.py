"""
Test script for AutoRetryLoop v0.
Tests 3 scenarios:
A: First result = pass (no retry)
B: First result = retry, second better
C: First result = retry, second worse
"""
import asyncio
from app.agent.auto_retry_loop import AutoRetryLoop


async def test_scenario_a():
    """Scenario A: First result = pass (no retry)."""
    print("=" * 80)
    print("Scenario A: First result = pass (no retry)")
    print("=" * 80)

    loop = AutoRetryLoop(max_additional_attempts=1)

    initial_result = {
        "prompt_id": "abc123",
        "judge_status": "pass",
        "orchestrator_report": {
            "final_score": 0.85,
            "final_verdict": "pass",
            "best_next_action": "accept",
        },
        "retry_decision": {
            "action": "accept",
        },
        "seed": 12345,
        "metadata_path": "metadata_a.json",
        "summary_path": "summary_a.txt",
        "images": [{"filename": "image_a.png"}],
    }

    async def mock_rerun(retry_prompt, retry_settings):
        return {
            "prompt_id": "def456",
            "judge_status": "pass",
            "orchestrator_report": {
                "final_score": 0.90,
                "final_verdict": "pass",
                "best_next_action": "accept",
            },
            "retry_decision": {
                "action": "accept",
            },
            "seed": 67890,
            "metadata_path": "metadata_b.json",
            "summary_path": "summary_b.txt",
            "images": [{"filename": "image_b.png"}],
        }

    result = await loop.run_once_retry(
        initial_result=initial_result,
        user_prompt="test prompt",
        final_prompt="test final prompt",
        final_settings={"seed": 12345},
        rerun_callable=mock_rerun,
    )

    print(f"loop_status: {result.loop_status}")
    print(f"selected_attempt_index: {result.selected_attempt_index}")
    print(f"selected_reason: {result.selected_reason}")
    print(f"attempts count: {len(result.attempts)}")
    
    # Verify expectations
    assert result.loop_status == "single_pass", f"Expected single_pass, got {result.loop_status}"
    assert result.selected_attempt_index == 1, f"Expected 1, got {result.selected_attempt_index}"
    assert len(result.attempts) == 1, f"Expected 1 attempt, got {len(result.attempts)}"
    
    print("\n✓ Scenario A PASSED")


async def test_scenario_b():
    """Scenario B: First result = retry, second better."""
    print("\n" + "=" * 80)
    print("Scenario B: First result = retry, second better")
    print("=" * 80)

    loop = AutoRetryLoop(max_additional_attempts=1)

    initial_result = {
        "prompt_id": "abc123",
        "judge_status": "retry",
        "orchestrator_report": {
            "final_score": 0.45,
            "final_verdict": "retry",
            "best_next_action": "retry_seed",
        },
        "retry_decision": {
            "action": "retry_seed",
            "suggested_settings_updates": {},
        },
        "seed": 12345,
        "metadata_path": "metadata_a.json",
        "summary_path": "summary_a.txt",
        "images": [{"filename": "image_a.png"}],
    }

    async def mock_rerun(retry_prompt, retry_settings):
        return {
            "prompt_id": "def456",
            "judge_status": "pass",
            "orchestrator_report": {
                "final_score": 0.82,
                "final_verdict": "pass",
                "best_next_action": "accept",
            },
            "retry_decision": {
                "action": "accept",
            },
            "seed": 67890,
            "metadata_path": "metadata_b.json",
            "summary_path": "summary_b.txt",
            "images": [{"filename": "image_b.png"}],
        }

    result = await loop.run_once_retry(
        initial_result=initial_result,
        user_prompt="test prompt",
        final_prompt="test final prompt",
        final_settings={"seed": 12345},
        rerun_callable=mock_rerun,
    )

    print(f"loop_status: {result.loop_status}")
    print(f"selected_attempt_index: {result.selected_attempt_index}")
    print(f"selected_reason: {result.selected_reason}")
    print(f"attempts count: {len(result.attempts)}")
    
    # Verify expectations
    assert result.loop_status == "retried_once", f"Expected retried_once, got {result.loop_status}"
    assert result.selected_attempt_index == 2, f"Expected 2, got {result.selected_attempt_index}"
    assert "higher_rank" in result.selected_reason or "passed" in result.selected_reason, f"Expected higher_rank or passed, got {result.selected_reason}"
    assert len(result.attempts) == 2, f"Expected 2 attempts, got {len(result.attempts)}"
    
    print("\n✓ Scenario B PASSED")


async def test_scenario_c():
    """Scenario C: First result = retry, second worse."""
    print("\n" + "=" * 80)
    print("Scenario C: First result = retry, second worse")
    print("=" * 80)

    loop = AutoRetryLoop(max_additional_attempts=1)

    initial_result = {
        "prompt_id": "abc123",
        "judge_status": "retry",
        "orchestrator_report": {
            "final_score": 0.55,
            "final_verdict": "retry",
            "best_next_action": "retry_seed",
        },
        "retry_decision": {
            "action": "retry_seed",
            "suggested_settings_updates": {},
        },
        "seed": 12345,
        "metadata_path": "metadata_a.json",
        "summary_path": "summary_a.txt",
        "images": [{"filename": "image_a.png"}],
    }

    async def mock_rerun(retry_prompt, retry_settings):
        return {
            "prompt_id": "def456",
            "judge_status": "retry",
            "orchestrator_report": {
                "final_score": 0.40,
                "final_verdict": "retry",
                "best_next_action": "retry_seed",
            },
            "retry_decision": {
                "action": "retry_seed",
                "suggested_settings_updates": {},
            },
            "seed": 67890,
            "metadata_path": "metadata_b.json",
            "summary_path": "summary_b.txt",
            "images": [{"filename": "image_b.png"}],
        }

    result = await loop.run_once_retry(
        initial_result=initial_result,
        user_prompt="test prompt",
        final_prompt="test final prompt",
        final_settings={"seed": 12345},
        rerun_callable=mock_rerun,
    )

    print(f"loop_status: {result.loop_status}")
    print(f"selected_attempt_index: {result.selected_attempt_index}")
    print(f"selected_reason: {result.selected_reason}")
    print(f"attempts count: {len(result.attempts)}")
    
    # Verify expectations
    assert result.loop_status == "retried_once", f"Expected retried_once, got {result.loop_status}"
    assert result.selected_attempt_index == 1, f"Expected 1, got {result.selected_attempt_index}"
    assert "higher_score" in result.selected_reason or "kept" in result.selected_reason, f"Expected higher_score or kept in reason, got {result.selected_reason}"
    assert len(result.attempts) == 2, f"Expected 2 attempts, got {len(result.attempts)}"
    
    print("\n✓ Scenario C PASSED")


async def test_scenario_d():
    """Scenario D: First result = retry, second attempt fails with exception."""
    print("\n" + "=" * 80)
    print("Scenario D: First result = retry, second attempt fails with exception")
    print("=" * 80)

    loop = AutoRetryLoop(max_additional_attempts=1)

    initial_result = {
        "prompt_id": "abc123",
        "judge_status": "retry",
        "orchestrator_report": {
            "final_score": 0.45,
            "final_verdict": "retry",
            "best_next_action": "retry_seed",
        },
        "retry_decision": {
            "action": "retry_seed",
            "suggested_settings_updates": {},
        },
        "seed": 12345,
        "metadata_path": "metadata_a.json",
        "summary_path": "summary_a.txt",
        "images": [{"filename": "image_a.png"}],
    }

    async def mock_rerun_fail(retry_prompt, retry_settings):
        raise RuntimeError("ComfyUI connection timeout during generation")

    result = await loop.run_once_retry(
        initial_result=initial_result,
        user_prompt="test prompt",
        final_prompt="test final prompt",
        final_settings={"seed": 12345},
        rerun_callable=mock_rerun_fail,
    )

    print(f"loop_status: {result.loop_status}")
    print(f"selected_attempt_index: {result.selected_attempt_index}")
    print(f"selected_reason: {result.selected_reason}")
    print(f"attempts count: {len(result.attempts)}")
    
    # Check failed attempt details
    failed_attempt = result.attempts[1]
    print(f"Failed attempt error_type: {failed_attempt.error_type}")
    print(f"Failed attempt error: {failed_attempt.error}")
    print(f"Failed attempt applied_retry_prompt: {failed_attempt.applied_retry_prompt}")
    
    # Verify expectations
    assert result.loop_status == "failed", f"Expected failed, got {result.loop_status}"
    assert result.selected_attempt_index == 1, f"Expected 1 (keep first on failure), got {result.selected_attempt_index}"
    assert "retry_failed" in result.selected_reason, f"Expected retry_failed in reason, got {result.selected_reason}"
    assert len(result.attempts) == 2, f"Expected 2 attempts, got {len(result.attempts)}"
    assert failed_attempt.error_type == "RuntimeError", f"Expected RuntimeError, got {failed_attempt.error_type}"
    assert failed_attempt.error == "ComfyUI connection timeout during generation"
    
    print("\n✓ Scenario D PASSED")


async def test_scenario_e():
    """Scenario E: First result = retry, second attempt returns status=failed dict."""
    print("\n" + "=" * 80)
    print("Scenario E: First result = retry, second attempt returns status=failed dict")
    print("=" * 80)

    loop = AutoRetryLoop(max_additional_attempts=1)

    initial_result = {
        "prompt_id": "abc123",
        "judge_status": "retry",
        "orchestrator_report": {
            "final_score": 0.45,
            "final_verdict": "retry",
            "best_next_action": "retry_seed",
        },
        "retry_decision": {
            "action": "retry_seed",
            "suggested_settings_updates": {},
        },
        "seed": 12345,
        "metadata_path": "metadata_a.json",
        "summary_path": "summary_a.txt",
        "images": [{"filename": "image_a.png"}],
    }

    async def mock_rerun_failed_dict(retry_prompt, retry_settings):
        return {
            "status": "failed",
            "failed_stage": "artifact_validation",
            "error": "Artifact validation failed: no images found",
            "error_type": "ArtifactValidationError",
            "prompt_id": "def456",
            "metadata_path": "metadata_b.json",
            "summary_path": "summary_b.txt",
        }

    result = await loop.run_once_retry(
        initial_result=initial_result,
        user_prompt="test prompt",
        final_prompt="test final prompt",
        final_settings={"seed": 12345},
        rerun_callable=mock_rerun_failed_dict,
    )

    print(f"loop_status: {result.loop_status}")
    print(f"selected_attempt_index: {result.selected_attempt_index}")
    print(f"selected_reason: {result.selected_reason}")
    print(f"attempts count: {len(result.attempts)}")
    
    # Check failed attempt details
    failed_attempt = result.attempts[1]
    print(f"Failed attempt error_type: {failed_attempt.error_type}")
    print(f"Failed attempt error: {failed_attempt.error}")
    print(f"Failed attempt metadata_path: {failed_attempt.metadata_path}")
    print(f"Failed attempt summary_path: {failed_attempt.summary_path}")
    print(f"Failed attempt applied_retry_prompt: {failed_attempt.applied_retry_prompt}")
    
    # Verify expectations
    assert result.loop_status == "failed", f"Expected failed, got {result.loop_status}"
    assert result.selected_attempt_index == 1, f"Expected 1 (keep first on failure), got {result.selected_attempt_index}"
    assert "retry_failed" in result.selected_reason, f"Expected retry_failed in reason, got {result.selected_reason}"
    assert len(result.attempts) == 2, f"Expected 2 attempts, got {len(result.attempts)}"
    assert failed_attempt.error_type == "ArtifactValidationError", f"Expected ArtifactValidationError, got {failed_attempt.error_type}"
    assert failed_attempt.error == "Artifact validation failed: no images found"
    assert failed_attempt.metadata_path == "metadata_b.json"
    assert failed_attempt.summary_path == "summary_b.txt"
    
    print("\n✓ Scenario E PASSED")


async def test_scenario_f():
    """Scenario F: Retry disabled (max_additional_attempts=0)."""
    print("\n" + "=" * 80)
    print("Scenario F: Retry disabled")
    print("=" * 80)

    loop = AutoRetryLoop(max_additional_attempts=0)

    initial_result = {
        "prompt_id": "abc123",
        "judge_status": "retry",
        "orchestrator_report": {
            "final_score": 0.45,
            "final_verdict": "retry",
            "best_next_action": "retry_seed",
        },
        "retry_decision": {
            "action": "retry_seed",
            "suggested_settings_updates": {},
        },
        "seed": 12345,
        "metadata_path": "metadata_a.json",
        "summary_path": "summary_a.txt",
        "images": [{"filename": "image_a.png"}],
    }

    async def mock_rerun(retry_prompt, retry_settings):
        return {
            "prompt_id": "def456",
            "judge_status": "pass",
            "orchestrator_report": {
                "final_score": 0.90,
                "final_verdict": "pass",
                "best_next_action": "accept",
            },
            "retry_decision": {
                "action": "accept",
            },
            "seed": 67890,
            "metadata_path": "metadata_b.json",
            "summary_path": "summary_b.txt",
            "images": [{"filename": "image_b.png"}],
        }

    result = await loop.run_once_retry(
        initial_result=initial_result,
        user_prompt="test prompt",
        final_prompt="test final prompt",
        final_settings={"seed": 12345},
        rerun_callable=mock_rerun,
    )

    print(f"loop_status: {result.loop_status}")
    print(f"selected_attempt_index: {result.selected_attempt_index}")
    print(f"selected_reason: {result.selected_reason}")
    print(f"attempts count: {len(result.attempts)}")
    
    # Verify expectations
    assert result.loop_status == "single_pass", f"Expected single_pass, got {result.loop_status}"
    assert result.selected_attempt_index == 1, f"Expected 1, got {result.selected_attempt_index}"
    assert result.selected_reason == "retry_disabled", f"Expected retry_disabled, got {result.selected_reason}"
    assert len(result.attempts) == 1, f"Expected 1 attempt, got {len(result.attempts)}"
    
    print("\n✓ Scenario F PASSED")


async def test_scenario_g():
    """Scenario G: Initial result not retry (judge_status=pass)."""
    print("\n" + "=" * 80)
    print("Scenario G: Initial result not retry")
    print("=" * 80)

    loop = AutoRetryLoop(max_additional_attempts=1)

    initial_result = {
        "prompt_id": "abc123",
        "judge_status": "pass",
        "orchestrator_report": {
            "final_score": 0.85,
            "final_verdict": "pass",
            "best_next_action": "accept",
        },
        "retry_decision": {
            "action": "accept",
        },
        "seed": 12345,
        "metadata_path": "metadata_a.json",
        "summary_path": "summary_a.txt",
        "images": [{"filename": "image_a.png"}],
    }

    async def mock_rerun(retry_prompt, retry_settings):
        return {
            "prompt_id": "def456",
            "judge_status": "pass",
            "orchestrator_report": {
                "final_score": 0.90,
                "final_verdict": "pass",
                "best_next_action": "accept",
            },
            "retry_decision": {
                "action": "accept",
            },
            "seed": 67890,
            "metadata_path": "metadata_b.json",
            "summary_path": "summary_b.txt",
            "images": [{"filename": "image_b.png"}],
        }

    result = await loop.run_once_retry(
        initial_result=initial_result,
        user_prompt="test prompt",
        final_prompt="test final prompt",
        final_settings={"seed": 12345},
        rerun_callable=mock_rerun,
    )

    print(f"loop_status: {result.loop_status}")
    print(f"selected_attempt_index: {result.selected_attempt_index}")
    print(f"selected_reason: {result.selected_reason}")
    print(f"attempts count: {len(result.attempts)}")
    
    # Verify expectations
    assert result.loop_status == "single_pass", f"Expected single_pass, got {result.loop_status}"
    assert result.selected_attempt_index == 1, f"Expected 1, got {result.selected_attempt_index}"
    assert result.selected_reason == "initial_result_not_retry", f"Expected initial_result_not_retry, got {result.selected_reason}"
    assert len(result.attempts) == 1, f"Expected 1 attempt, got {len(result.attempts)}"
    
    print("\n✓ Scenario G PASSED")


async def test_scenario_h():
    """Scenario H: Ranking guard - retry beats reject even with lower score."""
    print("\n" + "=" * 80)
    print("Scenario H: Ranking guard (retry vs reject)")
    print("=" * 80)

    loop = AutoRetryLoop(max_additional_attempts=1)

    initial_result = {
        "prompt_id": "abc123",
        "judge_status": "retry",
        "orchestrator_report": {
            "final_score": 0.55,
            "final_verdict": "retry",
            "best_next_action": "retry_seed",
        },
        "retry_decision": {
            "action": "retry_seed",
            "suggested_settings_updates": {},
        },
        "seed": 12345,
        "metadata_path": "metadata_a.json",
        "summary_path": "summary_a.txt",
        "images": [{"filename": "image_a.png"}],
    }

    async def mock_rerun(retry_prompt, retry_settings):
        return {
            "prompt_id": "def456",
            "judge_status": "reject",
            "orchestrator_report": {
                "final_score": 0.80,  # Higher score but lower rank (reject < retry)
                "final_verdict": "reject",
                "best_next_action": "reject",
            },
            "retry_decision": {
                "action": "reject",
            },
            "seed": 67890,
            "metadata_path": "metadata_b.json",
            "summary_path": "summary_b.txt",
            "images": [{"filename": "image_b.png"}],
        }

    result = await loop.run_once_retry(
        initial_result=initial_result,
        user_prompt="test prompt",
        final_prompt="test final prompt",
        final_settings={"seed": 12345},
        rerun_callable=mock_rerun,
    )

    print(f"loop_status: {result.loop_status}")
    print(f"selected_attempt_index: {result.selected_attempt_index}")
    print(f"selected_reason: {result.selected_reason}")
    print(f"attempts count: {len(result.attempts)}")
    
    # Verify expectations
    assert result.loop_status == "retried_once", f"Expected retried_once, got {result.loop_status}"
    assert result.selected_attempt_index == 1, f"Expected 1 (retry beats reject), got {result.selected_attempt_index}"
    assert "higher_rank" in result.selected_reason, f"Expected higher_rank in reason, got {result.selected_reason}"
    assert "higher_score" not in result.selected_reason.lower(), f"Reason should not mention higher_score, got {result.selected_reason}"
    assert len(result.attempts) == 2, f"Expected 2 attempts, got {len(result.attempts)}"
    
    print("\n✓ Scenario H PASSED")


async def main():
    """Run all test scenarios."""
    print("\n" + "=" * 80)
    print("AutoRetryLoop v0 Test Suite - Full Matrix A-H")
    print("=" * 80)
    
    await test_scenario_a()
    await test_scenario_b()
    await test_scenario_c()
    await test_scenario_d()
    await test_scenario_e()
    await test_scenario_f()
    await test_scenario_g()
    await test_scenario_h()
    
    print("\n" + "=" * 80)
    print("All scenarios A-H PASSED!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
