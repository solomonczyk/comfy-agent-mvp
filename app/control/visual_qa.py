"""
Visual QA module for frame evaluation against shot contract and beat specs.
Minimal implementation with manual-review-compatible heuristics.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class VisualQA:
    """Evaluates generated frames against shot contract and beat specifications."""
    
    def __init__(self, shot_contract_path: str, beat_specs_path: str):
        self.shot_contract_path = Path(shot_contract_path)
        self.beat_specs_path = Path(beat_specs_path)
        self.shot_contract = self._load_json(self.shot_contract_path)
        self.beat_specs = self._load_json(self.beat_specs_path)
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def evaluate_frame(
        self, 
        frame_path: str, 
        beat_id: str
    ) -> Dict[str, Any]:
        """
        Evaluate a single frame against its beat specification.
        
        Returns a structured evaluation with checks and verdict.
        """
        beat_spec = self._find_beat_spec(beat_id)
        if not beat_spec:
            raise ValueError(f"Beat spec not found: {beat_id}")
        
        # Initialize checks with null values (manual review required)
        checks = {
            "phone_visible": None,
            "screen_visible": None,
            "phone_dominant": None,
            "face_dominant_allowed": beat_spec.get("face_priority") in ["medium", "high"],
            "overlay_safe": None,
            "character_anchor_ok": None,
            "environment_anchor_ok": None
        }
        
        # Determine verdict based on beat requirements
        verdict = self._determine_verdict(beat_spec, checks)
        reasons = self._generate_reasons(beat_spec, checks, verdict)
        
        return {
            "frame_id": Path(frame_path).name,
            "beat_id": beat_id,
            "verdict": verdict,
            "checks": checks,
            "reasons": reasons
        }
    
    def _find_beat_spec(self, beat_id: str) -> Optional[Dict[str, Any]]:
        """Find beat specification by ID."""
        for beat in self.beat_specs.get("beats", []):
            if beat["beat_id"] == beat_id:
                return beat
        return None
    
    def _determine_verdict(self, beat_spec: Dict[str, Any], checks: Dict[str, Any]) -> str:
        """
        Determine verdict based on beat requirements and check results.
        
        Returns: "pass" | "fail" | "needs_manual_review"
        
        Hard rule: Never mark a frame as pass unless all required checks are satisfied.
        If automatic detection is unavailable, use "needs_manual_review".
        """
        # For now, all checks are null (manual review required)
        # This prevents false passes
        return "needs_manual_review"
    
    def _generate_reasons(
        self, 
        beat_spec: Dict[str, Any], 
        checks: Dict[str, Any],
        verdict: str
    ) -> list:
        """Generate human-readable reasons for the verdict."""
        reasons = []
        
        if verdict == "needs_manual_review":
            reasons.append("Automatic visual detection not yet implemented")
            reasons.append("Manual visual review required to verify:")
            
            if beat_spec.get("phone_required"):
                reasons.append(f"- Phone visibility (required: {beat_spec.get('phone_required')})")
            
            if beat_spec.get("phone_screen_required"):
                reasons.append(f"- Screen visibility (required: {beat_spec.get('phone_screen_required')})")
            
            if beat_spec.get("phone_priority") == "very_high":
                reasons.append(f"- Phone dominance (priority: very_high)")
                min_ratio = beat_spec.get("required_screen_area_ratio_min")
                if min_ratio:
                    reasons.append(f"- Screen area ratio >= {min_ratio * 100}%")
            
            if beat_spec.get("composition"):
                reasons.append(f"- Composition: {beat_spec.get('composition')}")
        
        return reasons
    
    def evaluate_frames(
        self, 
        frame_paths: list, 
        beat_ids: list
    ) -> Dict[str, Any]:
        """
        Evaluate multiple frames against their beat specifications.
        
        Returns a complete visual QA report.
        """
        if len(frame_paths) != len(beat_ids):
            raise ValueError("Frame paths and beat IDs must have same length")
        
        evaluations = []
        for frame_path, beat_id in zip(frame_paths, beat_ids):
            evaluation = self.evaluate_frame(frame_path, beat_id)
            evaluations.append(evaluation)
        
        # Calculate overall verdict
        all_pass = all(e["verdict"] == "pass" for e in evaluations)
        any_fail = any(e["verdict"] == "fail" for e in evaluations)
        needs_review = any(e["verdict"] == "needs_manual_review" for e in evaluations)
        
        if all_pass:
            overall_verdict = "pass"
        elif any_fail:
            overall_verdict = "fail"
        else:
            overall_verdict = "needs_manual_review"
        
        return {
            "episode_id": self.shot_contract.get("episode_id"),
            "shot_id": self.shot_contract.get("shot_id"),
            "overall_verdict": overall_verdict,
            "total_frames": len(evaluations),
            "passed_frames": sum(1 for e in evaluations if e["verdict"] == "pass"),
            "failed_frames": sum(1 for e in evaluations if e["verdict"] == "fail"),
            "needs_review_frames": sum(1 for e in evaluations if e["verdict"] == "needs_manual_review"),
            "evaluations": evaluations
        }
    
    def save_report(self, report: Dict[str, Any], output_path: str) -> None:
        """Save visual QA report to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


def load_visual_qa_report(project_root: str, episode_id: str, shot_id: str) -> Optional[Dict[str, Any]]:
    """
    Load visual QA report from project root.
    
    Supports multiple report formats:
    - visual_qa_report.json (legacy format with overall_verdict)
    - qc_report.json (new format with final_verdict.decision)
    - ep01_shot01_qc_report.json (new format with final_verdict.decision)
    
    Args:
        project_root: Path to project root directory
        episode_id: Episode ID to match
        shot_id: Shot ID to match
    
    Returns:
        Visual QA report dict if found and matches episode/shot, else None
    """
    project_path = Path(project_root)
    
    # Try multiple report file names in order of preference
    report_paths = [
        project_path / "output" / "control" / f"{episode_id}_{shot_id}_qc_report.json",
        project_path / "output" / "control" / "qc_report.json",
        project_path / "output" / "control" / "visual_qa_report.json",
    ]
    
    for report_path in report_paths:
        if not report_path.exists():
            continue
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            # Verify episode and shot match
            if report.get("episode_id") == episode_id and report.get("shot_id") == shot_id:
                return report
            
        except (json.JSONDecodeError, IOError):
            continue
    
    return None


def main():
    """CLI entry point for visual QA."""
    import sys
    
    if len(sys.argv) < 5:
        print("Usage: python -m app.control.visual_qa <shot_contract> <beat_specs> <frame_paths> <beat_ids> <output>")
        print("Example: python -m app.control.visual_qa shot_contract.json beat_specs.json frame1.png,frame2.png,frame3.png beat_01,beat_02,beat_03 report.json")
        sys.exit(1)
    
    shot_contract_path = sys.argv[1]
    beat_specs_path = sys.argv[2]
    frame_paths = sys.argv[3].split(',')
    beat_ids = sys.argv[4].split(',')
    output_path = sys.argv[5]
    
    qa = VisualQA(shot_contract_path, beat_specs_path)
    report = qa.evaluate_frames(frame_paths, beat_ids)
    qa.save_report(report, output_path)
    
    print(f"Visual QA report saved to: {output_path}")
    print(f"Overall verdict: {report['overall_verdict']}")


if __name__ == "__main__":
    main()
