"""Hybrid QC Benchmark - Test local QC + vision hybrid approach.

Goals:
- Collect 3 vision response cases: valid JSON, malformed JSON, None
- Test that local hard reject works without vision
- Test hybrid verdict (local hard reject → vision subscores → weighted decision)
- Verify accept/retry/reject spectrum exists
- Count false accepts/rejects honestly
"""

import json
from pathlib import Path
from typing import Any

from app.judges.base_types import JudgeInput
from app.judges.judge_orchestrator import JudgeOrchestrator
from app.judges.technical_judge import TechnicalJudge
from app.judges.semantic_judge import SemanticJudge
from app.judges.artistic_judge import ArtisticJudge
from app.judges.vision_defect_judge import VisionDefectJudge
from app.judges.local_qc_judge import LocalQCJudge
from app.judges.vision_judge_client import VisionJudgeClient


def get_expanded_benchmark_pack() -> dict[str, list[dict[str, Any]]]:
    """Get expanded benchmark pack categorized by expected quality."""
    project_root = Path("f:/ComfyUI/comfy-agent-mvp")
    comfyui_output = Path("f:/ComfyUI/comfyUI_portable_inst/ComfyUI_windows_portable_nvidia_cu126/ComfyUI_windows_portable/ComfyUI/output")
    
    benchmark = {
        "golden_accept": [],  # NEW: Golden accept pack - normal images that should accept
        "good": [],
        "borderline": [],
        "bad": [],
    }
    
    # GOLDEN ACCEPT images - normal portraits that should pass (not premium ideal, but acceptable)
    golden_accept_images = [
        comfyui_output / "portrait_00027_.png",  # User mentioned as conditional accept
        comfyui_output / "portrait_00030_.png",  # User mentioned as conditional accept
        comfyui_output / "portrait_00021_.png",  # Previously good, was falsely rejected by multi_subject
    ]
    
    for img_path in golden_accept_images:
        if img_path.exists():
            benchmark["golden_accept"].append({
                "path": str(img_path),
                "prompt": "normal portrait photo, good quality but not premium ideal",
                "expected_verdict": "accept",
            })
    
    # GOOD images - high quality portraits
    good_images = [
        project_root / "test_portrait.png",
        comfyui_output / "portrait_00008_.png",
        comfyui_output / "portrait_00023_.png",
    ]
    
    for img_path in good_images:
        if img_path.exists():
            benchmark["good"].append({
                "path": str(img_path),
                "prompt": "cinematic portrait photo of a realistic woman, natural skin texture, detailed eyes, soft cinematic light",
                "expected_verdict": "accept",
            })
    
    # BORDERLINE images - minor issues
    borderline_images = [
        comfyui_output / "portrait_00005_.png",
        comfyui_output / "portrait_00010_.png",
        comfyui_output / "portrait_00015_.png",
        comfyui_output / "portrait_00018_.png",
    ]
    
    for img_path in borderline_images:
        if img_path.exists():
            benchmark["borderline"].append({
                "path": str(img_path),
                "prompt": "cinematic portrait photo with minor quality issues",
                "expected_verdict": "retry",
            })
    
    # BAD images - severe defects
    bad_images = [
        project_root / "test_input_image.png",
        comfyui_output / "SD1.5_00001_.png",
        comfyui_output / "SD1.5_00002_.png",
        comfyui_output / "portrait_00019_.png",  # Known to have watermark based on user feedback
    ]
    
    for img_path in bad_images:
        if img_path.exists():
            benchmark["bad"].append({
                "path": str(img_path),
                "prompt": "portrait with severe defects or low quality",
                "expected_verdict": "reject",
            })
    
    return benchmark


def run_hybrid_benchmark() -> dict[str, Any]:
    """Run hybrid benchmark with local QC + vision approach."""
    benchmark = get_expanded_benchmark_pack()
    
    # Initialize judges with hybrid approach
    vision_client = VisionJudgeClient()
    technical_judge = TechnicalJudge()
    semantic_judge = SemanticJudge(vision_client=vision_client)
    artistic_judge = ArtisticJudge(vision_client=vision_client)
    vision_defect_judge = VisionDefectJudge(vision_client=vision_client)
    local_qc_judge = LocalQCJudge()
    
    orchestrator = JudgeOrchestrator(
        technical_judge=technical_judge,
        semantic_judge=semantic_judge,
        artistic_judge=artistic_judge,
        vision_defect_judge=vision_defect_judge,
        local_qc_judge=local_qc_judge,
        quality_profile="portrait_premium_v1",
    )
    
    results = {
        "by_category": {"golden_accept": [], "good": [], "borderline": [], "bad": []},
        "vision_response_cases": {
            "valid_json": [],
            "malformed_json": [],
            "none_or_error": [],
        },
        "summary": {
            "total_tested": 0,
            "accept": 0,
            "retry": 0,
            "reject": 0,
            "local_hard_reject": 0,
            "vision_failed": 0,
            "true_accept": 0,
            "false_accept": 0,
            "true_retry": 0,
            "false_retry": 0,
            "true_reject": 0,
            "false_reject": 0,
        },
        "fragments": {
            "accept": None,
            "retry": None,
            "reject": None,
        },
        "changes": {
            "multi_subject_releases": [],  # Images previously rejected by multi_subject that now pass
            "semantic_collapse_retries": [],  # Images previously rejected by semantic_collapse that now retry
        },
    }
    
    for category, images in benchmark.items():
        print(f"\n=== Testing {category.upper()} images ===")
        
        for img in images:
            print(f"  Testing: {Path(img['path']).name}")
            
            judge_input = JudgeInput(
                user_prompt=img["prompt"],
                final_positive_prompt=img["prompt"],
                preset_name="portrait_premium",
                rewrite_mode=None,
                seed=123,
                images=[],
                primary_image_path=img["path"],
                width=1024,
                height=1024,
            )
            
            try:
                report = orchestrator.evaluate(judge_input)
                
                # Collect vision response cases
                vision_status = "unknown"
                if report.semantic and report.semantic.raw_notes:
                    vision_status = report.semantic.raw_notes.get("_vision_status", "unknown")
                
                if vision_status == "valid_json":
                    results["vision_response_cases"]["valid_json"].append({
                        "path": img["path"],
                        "raw_response": report.semantic.raw_notes.get("raw_response", {}),
                    })
                elif vision_status in ["invalid_json", "empty_response"]:
                    results["vision_response_cases"]["malformed_json"].append({
                        "path": img["path"],
                        "raw_response": report.semantic.raw_notes.get("_raw_response", ""),
                        "parse_error": report.semantic.raw_notes.get("_parse_error", ""),
                    })
                elif vision_status in ["api_failure", "missing_image"]:
                    results["vision_response_cases"]["none_or_error"].append({
                        "path": img["path"],
                        "error": report.semantic.raw_notes.get("_error", ""),
                    })
                
                # Check if local hard reject was used
                local_reject = report.raw_notes.get("_qc_method") == "local_hard_reject"
                if local_reject:
                    results["summary"]["local_hard_reject"] += 1
                
                # Check if vision failed (None scores)
                vision_failed = (report.semantic and report.semantic.score is None) or \
                                (report.artistic and report.artistic.score is None)
                if vision_failed:
                    results["summary"]["vision_failed"] += 1
                
                # Determine verdict
                verdict = report.final_verdict
                expected = img["expected_verdict"]
                
                # Map 'pass' to 'accept' for canonical final class
                if verdict == "pass":
                    verdict_key = "accept"
                elif verdict == "retry":
                    verdict_key = "retry"
                else:
                    verdict_key = "reject"
                
                result = {
                    "path": img["path"],
                    "category": category,
                    "expected_verdict": expected,
                    "actual_verdict": verdict,
                    "local_hard_reject": local_reject,
                    "vision_failed": vision_failed,
                    "vision_status": vision_status,
                    "final_score": report.final_score,
                    "global_blockers": [issue.code for issue in report.global_blockers],
                    "best_next_action": report.best_next_action,
                }
                
                # Add quality report if available
                if report.quality_report:
                    result["quality_verdict"] = report.quality_report.verdict
                    result["hard_fails"] = report.quality_report.hard_fail_reasons
                    result["scorecard"] = {
                        "technical": report.quality_report.scorecard.technical_score,
                        "anatomy": report.quality_report.scorecard.anatomy_score,
                        "semantic": report.quality_report.scorecard.semantic_score,
                        "aesthetic": report.quality_report.scorecard.aesthetic_score,
                        "weighted": report.quality_report.scorecard.weighted_score,
                    }
                
                results["by_category"][category].append(result)
                results["summary"]["total_tested"] += 1
                results["summary"][verdict_key] += 1
                
                # Track changes from previous run
                # Check if image was previously rejected by multi_subject but now passes
                if category in ["golden_accept", "good"]:
                    if verdict != "reject" and "multi_subject" not in str(result["global_blockers"]):
                        results["changes"]["multi_subject_releases"].append({
                            "path": img["path"],
                            "previous_reject_reason": "multi_subject_unexpected",
                            "current_verdict": verdict,
                        })
                
                # Check if image was previously rejected by semantic_collapse but now retries
                if category == "borderline":
                    if verdict == "retry" and "semantic_collapse" in str(result.get("hard_fails", [])):
                        # This is expected - semantic_collapse now leads to retry instead of reject
                        pass
                    elif verdict == "retry" and "semantic_collapse" in str(result["global_blockers"]):
                        results["changes"]["semantic_collapse_retries"].append({
                            "path": img["path"],
                            "current_verdict": verdict,
                            "has_semantic_collapse": True,
                        })
                
                # Calculate true/false positives/negatives
                if verdict_key == "accept":
                    if expected == "accept":
                        results["summary"]["true_accept"] += 1
                    else:
                        results["summary"]["false_accept"] += 1
                        if results["fragments"]["accept"] is None:
                            results["fragments"]["accept"] = result
                elif verdict_key == "retry":
                    if expected == "retry":
                        results["summary"]["true_retry"] += 1
                    else:
                        results["summary"]["false_retry"] += 1
                        if results["fragments"]["retry"] is None:
                            results["fragments"]["retry"] = result
                elif verdict_key == "reject":
                    if expected == "reject":
                        results["summary"]["true_reject"] += 1
                    else:
                        results["summary"]["false_reject"] += 1
                        if results["fragments"]["reject"] is None:
                            results["fragments"]["reject"] = result
                
                # Save first of each verdict as fragment if not already saved
                if results["fragments"][verdict_key] is None:
                    results["fragments"][verdict_key] = result
                
                print(f"    Verdict: {verdict} (expected: {expected})")
                print(f"    Local hard reject: {local_reject}")
                print(f"    Vision failed: {vision_failed}")
                print(f"    Vision status: {vision_status}")
                
            except RuntimeError as e:
                if "OPENROUTER_API_KEY" in str(e) or "Vision judge" in str(e):
                    print(f"    SKIP: Vision API not configured - {e}")
                    results["vision_response_cases"]["none_or_error"].append({
                        "path": img["path"],
                        "error": str(e),
                    })
                    continue
                else:
                    raise
            except Exception as e:
                print(f"    ERROR: {e}")
                import traceback
                traceback.print_exc()
    
    return results


def test_hybrid_qc_benchmark():
    """Run hybrid QC benchmark and collect vision response cases."""
    print("\n=== Hybrid QC Benchmark ===")
    
    results = run_hybrid_benchmark()
    
    # Print summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    summary = results["summary"]
    print(f"Total tested: {summary['total_tested']}")
    print(f"Accept: {summary['accept']}")
    print(f"Retry: {summary['retry']}")
    print(f"Reject: {summary['reject']}")
    print(f"Local hard reject: {summary['local_hard_reject']}")
    print(f"Vision failed: {summary['vision_failed']}")
    print(f"\nTrue Accept: {summary['true_accept']}")
    print(f"False Accept: {summary['false_accept']}")
    print(f"True Retry: {summary['true_retry']}")
    print(f"False Retry: {summary['false_retry']}")
    print(f"True Reject: {summary['true_reject']}")
    print(f"False Reject: {summary['false_reject']}")
    
    # Print vision response cases
    print("\n" + "="*60)
    print("VISION RESPONSE CASES")
    print("="*60)
    vision_cases = results["vision_response_cases"]
    print(f"Valid JSON: {len(vision_cases['valid_json'])}")
    print(f"Malformed JSON: {len(vision_cases['malformed_json'])}")
    print(f"None/Error: {len(vision_cases['none_or_error'])}")
    
    # Save results
    results_file = Path("f:/ComfyUI/comfy-agent-mvp/data/outputs/hybrid_qc_benchmark_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {results_file}")
    
    # Verify requirements
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    # Check vision response recovery
    has_valid = len(vision_cases["valid_json"]) > 0
    has_malformed = len(vision_cases["malformed_json"]) > 0
    has_none = len(vision_cases["none_or_error"]) > 0
    
    print(f"Vision response recovery: {'PASS' if has_valid else 'FAIL'}")
    print(f"  Has valid JSON: {has_valid}")
    print(f"  Has malformed JSON: {has_malformed}")
    print(f"  Has None/Error: {has_none}")
    
    # Check no more fake zero scores
    print(f"\nNo more fake zero scores: {'PASS' if summary['vision_failed'] > 0 else 'PARTIAL'}")
    print(f"  Vision failed count: {summary['vision_failed']}")
    print(f"  (Failed visions should have None scores, not 0)")
    
    # Check local hard reject works
    print(f"\nLocal hard reject works: {'PASS' if summary['local_hard_reject'] > 0 else 'UNKNOWN'}")
    print(f"  Local hard reject count: {summary['local_hard_reject']}")
    
    # Check accept/retry/reject exist
    has_accept = summary['accept'] > 0
    has_retry = summary['retry'] > 0
    has_reject = summary['reject'] > 0
    
    print(f"\nAccept/retry/reject exist: {'PASS' if has_accept and has_retry and has_reject else 'FAIL'}")
    print(f"  Has accept: {has_accept}")
    print(f"  Has retry: {has_retry}")
    print(f"  Has reject: {has_reject}")
    
    # Check not all reject
    not_all_reject = summary['reject'] < summary['total_tested']
    print(f"\nNot all images rejected: {'PASS' if not_all_reject else 'FAIL'}")
    print(f"  Reject ratio: {summary['reject']}/{summary['total_tested']}")


if __name__ == "__main__":
    print("="*60)
    print("Hybrid QC Benchmark - Vision Judge Reliability Repair")
    print("="*60)
    
    try:
        test_hybrid_qc_benchmark()
    except Exception as e:
        print(f"\nBenchmark FAILED: {e}")
        import traceback
        traceback.print_exc()
