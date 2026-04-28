#!/usr/bin/env python3
"""
RC Artifact Validation Script

Validates the RC proof pack artifacts for completeness, correctness, and honesty.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any


class RCValidator:
    def __init__(self, project_root: str, episode_id: str, shot_id: str):
        self.project_root = Path(project_root)
        self.episode_id = episode_id
        self.shot_id = shot_id
        self.output_dir = self.project_root / "output"
        self.control_dir = self.output_dir / "control"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed_checks: List[str] = []

    def log_error(self, message: str):
        self.errors.append(message)
        print(f"❌ ERROR: {message}")

    def log_warning(self, message: str):
        self.warnings.append(message)
        print(f"⚠️  WARNING: {message}")

    def log_pass(self, message: str):
        self.passed_checks.append(message)
        print(f"✅ PASS: {message}")

    def validate_file_exists(self, path: Path, description: str) -> bool:
        if path.exists():
            self.log_pass(f"{description} exists: {path}")
            return True
        else:
            self.log_error(f"{description} missing: {path}")
            return False

    def validate_json_parse(self, path: Path, description: str) -> bool:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                json.load(f)
            self.log_pass(f"{description} parses correctly")
            return True
        except Exception as e:
            self.log_error(f"{description} parse failed: {e}")
            return False

    def validate_file_non_empty(self, path: Path, description: str) -> bool:
        if path.stat().st_size > 0:
            self.log_pass(f"{description} is non-empty ({path.stat().st_size} bytes)")
            return True
        else:
            self.log_error(f"{description} is empty")
            return False

    def validate_no_forbidden_paths(self, data: Any, description: str) -> bool:
        forbidden = ["AppData", "Temp", "pytest-of-"]
        data_str = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
        
        has_forbidden = False
        for forbidden_term in forbidden:
            if forbidden_term in data_str:
                self.log_error(f"{description} contains forbidden path '{forbidden_term}'")
                has_forbidden = True
        
        if not has_forbidden:
            self.log_pass(f"{description} has no forbidden paths")
            return True
        return False

    def validate_artifact_index_references(self) -> bool:
        artifact_index_path = self.control_dir / "artifact_index.json"
        if not artifact_index_path.exists():
            self.log_error("artifact_index.json missing")
            return False

        try:
            with open(artifact_index_path, 'r', encoding='utf-8') as f:
                artifact_index = json.load(f)
        except Exception as e:
            self.log_error(f"artifact_index.json parse failed: {e}")
            return False

        all_valid = True
        for artifact in artifact_index.get("artifacts", []):
            artifact_path = Path(artifact.get("path", ""))
            if not artifact_path.exists():
                self.log_error(f"artifact_index references missing file: {artifact_path}")
                all_valid = False
            else:
                self.log_pass(f"artifact_index reference exists: {artifact_path.name}")

        return all_valid

    def validate_ledger_transitions(self) -> bool:
        ledger_path = self.control_dir / f"{self.episode_id}_{self.shot_id}_ledger.json"
        if not ledger_path.exists():
            self.log_error(f"{self.episode_id}_{self.shot_id}_ledger.json missing")
            return False

        try:
            with open(ledger_path, 'r', encoding='utf-8') as f:
                ledger = json.load(f)
        except Exception as e:
            self.log_error(f"{self.episode_id}_{self.shot_id}_ledger.json parse failed: {e}")
            return False

        required_transitions = [
            "ready_for_generation",
            "frames_generated",
            "scene_assembled",
            "qa_passed",
            "audio_attached",
            "episode_rendered"
        ]

        records = ledger.get("records", [])
        found_states = set()
        
        for record in records:
            state = record.get("current_state")
            if state:
                found_states.add(state)

        all_found = True
        for required in required_transitions:
            if required in found_states:
                self.log_pass(f"Ledger contains transition: {required}")
            else:
                # audio_attached may be skipped for no-audio policy
                if required == "audio_attached":
                    self.log_warning(f"Ledger missing transition: {required} (may be skipped for no-audio policy)")
                else:
                    self.log_error(f"Ledger missing transition: {required}")
                    all_found = False

        return all_found

    def validate_terminal_state(self) -> bool:
        state_path = self.control_dir / self.episode_id / f"{self.shot_id}_state.json"
        if not state_path.exists():
            self.log_error(f"{self.episode_id}/{self.shot_id}_state.json missing")
            return False

        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except Exception as e:
            self.log_error(f"{self.episode_id}/{self.shot_id}_state.json parse failed: {e}")
            return False

        current_state = state.get("current_state")
        expected_next = state.get("expected_next_action")

        if current_state == "episode_rendered":
            self.log_pass(f"Terminal state: {current_state}")
        else:
            self.log_error(f"Non-terminal state: {current_state} (expected: episode_rendered)")
            return False

        if expected_next in ["none", None, "complete"]:
            self.log_pass(f"Expected next action: {expected_next}")
        else:
            self.log_error(f"Non-terminal expected_next_action: {expected_next}")
            return False

        return True

    def validate_no_fake_audio(self) -> bool:
        audio_manifest_path = self.control_dir / f"{self.episode_id}_{self.shot_id}_audio_manifest.json"
        if not audio_manifest_path.exists():
            self.log_error(f"{self.episode_id}_{self.shot_id}_audio_manifest.json missing")
            return False

        try:
            with open(audio_manifest_path, 'r', encoding='utf-8') as f:
                audio_manifest = json.load(f)
        except Exception as e:
            self.log_error(f"{self.episode_id}_{self.shot_id}_audio_manifest.json parse failed: {e}")
            return False

        audio_required = audio_manifest.get("audio_required")
        audio_policy = audio_manifest.get("policy")

        if audio_required is False:
            self.log_pass("audio_required is False (no fake audio claim)")
        else:
            self.log_error(f"audio_required is {audio_required} (expected: False)")
            return False

        if audio_policy == "no_audio_for_rc":
            self.log_pass(f"audio_policy is '{audio_policy}' (honest limitation)")
        else:
            self.log_error(f"audio_policy is '{audio_policy}' (expected: no_audio_for_rc)")
            return False

        return True

    def validate_no_fake_final_mp4(self) -> bool:
        final_manifest_path = self.control_dir / f"{self.episode_id}_{self.shot_id}_final_manifest.json"
        if not final_manifest_path.exists():
            self.log_error(f"{self.episode_id}_{self.shot_id}_final_manifest.json missing")
            return False

        try:
            with open(final_manifest_path, 'r', encoding='utf-8') as f:
                final_manifest = json.load(f)
        except Exception as e:
            self.log_error(f"{self.episode_id}_{self.shot_id}_final_manifest.json parse failed: {e}")
            return False

        audio_attached = final_manifest.get("audio_attached")
        audio_policy = final_manifest.get("audio_policy")
        limitation = final_manifest.get("limitation")

        if audio_attached is False:
            self.log_pass("final_manifest audio_attached is False (no fake final MP4 claim)")
        else:
            self.log_error(f"final_manifest audio_attached is {audio_attached} (expected: False)")
            return False

        if audio_policy == "no_audio_for_rc":
            self.log_pass(f"final_manifest audio_policy is '{audio_policy}'")
        else:
            self.log_error(f"final_manifest audio_policy is '{audio_policy}' (expected: no_audio_for_rc)")
            return False

        if limitation and "RC" in limitation:
            self.log_pass(f"final_manifest limitation documented: {limitation}")
        else:
            self.log_warning(f"final_manifest limitation not clearly documented: {limitation}")

        return True

    def validate_frame_exists_and_non_empty(self) -> bool:
        frame_path = self.output_dir / "frames" / f"{self.episode_id}_{self.shot_id}" / "000001.png"
        if not self.validate_file_exists(frame_path, "Generated frame"):
            return False
        return self.validate_file_non_empty(frame_path, "Generated frame")

    def validate_scene_mp4_exists_and_non_empty(self) -> bool:
        scene_path = self.output_dir / "scenes" / f"{self.episode_id}_{self.shot_id}" / "scene.mp4"
        if not self.validate_file_exists(scene_path, "Scene video"):
            return False
        return self.validate_file_non_empty(scene_path, "Scene video")

    def validate_final_manifest_preserves_no_audio(self) -> bool:
        final_manifest_path = self.control_dir / f"{self.episode_id}_{self.shot_id}_final_manifest.json"
        if not final_manifest_path.exists():
            self.log_error(f"{self.episode_id}_{self.shot_id}_final_manifest.json missing")
            return False

        try:
            with open(final_manifest_path, 'r', encoding='utf-8') as f:
                final_manifest = json.load(f)
        except Exception as e:
            self.log_error(f"{self.episode_id}_{self.shot_id}_final_manifest.json parse failed: {e}")
            return False

        audio_policy = final_manifest.get("audio_policy")
        if audio_policy == "no_audio_for_rc":
            self.log_pass("final_manifest preserves no-audio policy")
            return True
        else:
            self.log_error(f"final_manifest does not preserve no-audio policy: {audio_policy}")
            return False

    def run_all_validations(self) -> bool:
        print(f"\n{'='*60}")
        print(f"RC Artifact Validation")
        print(f"Project Root: {self.project_root}")
        print(f"Episode: {self.episode_id}, Shot: {self.shot_id}")
        print(f"{'='*60}\n")

        # 1. Project/Profile artifacts
        print("\n--- 1. Project/Profile Artifacts ---")
        self.validate_file_exists(self.control_dir / "project_profile.json", "project_profile.json")
        self.validate_json_parse(self.control_dir / "project_profile.json", "project_profile.json")
        self.validate_file_exists(self.control_dir / "prompt_pack.json", "prompt_pack.json")
        self.validate_json_parse(self.control_dir / "prompt_pack.json", "prompt_pack.json")

        # 2. Runtime/Proof artifacts
        print("\n--- 2. Runtime/Proof Artifacts ---")
        self.validate_file_exists(self.control_dir / f"{self.episode_id}_{self.shot_id}_preflight.json", "preflight.json")
        self.validate_json_parse(self.control_dir / f"{self.episode_id}_{self.shot_id}_preflight.json", "preflight.json")
        self.validate_file_exists(self.control_dir / f"{self.episode_id}_{self.shot_id}_submitted_workflow.json", "submitted_workflow.json")
        self.validate_json_parse(self.control_dir / f"{self.episode_id}_{self.shot_id}_submitted_workflow.json", "submitted_workflow.json")
        self.validate_file_exists(self.control_dir / f"{self.episode_id}_{self.shot_id}_observed_settings.json", "observed_settings.json")
        self.validate_json_parse(self.control_dir / f"{self.episode_id}_{self.shot_id}_observed_settings.json", "observed_settings.json")

        # 3. Frame generation artifacts
        print("\n--- 3. Frame Generation Artifacts ---")
        self.validate_file_exists(self.control_dir / "frames_manifest.json", "frames_manifest.json")
        self.validate_json_parse(self.control_dir / "frames_manifest.json", "frames_manifest.json")
        self.validate_frame_exists_and_non_empty()

        # 4. QC/Retry artifacts
        print("\n--- 4. QC/Retry Artifacts ---")
        qc_report_path = self.control_dir / f"{self.episode_id}_{self.shot_id}_qc_report.json"
        if not qc_report_path.exists():
            qc_report_path = self.control_dir / "qc_report.json"
        self.validate_file_exists(qc_report_path, "qc_report.json")
        self.validate_json_parse(qc_report_path, "qc_report.json")
        self.validate_file_exists(self.control_dir / "retry_decision.json", "retry_decision.json")
        self.validate_json_parse(self.control_dir / "retry_decision.json", "retry_decision.json")

        # 5. Scene artifacts
        print("\n--- 5. Scene Artifacts ---")
        self.validate_file_exists(self.control_dir / f"{self.episode_id}_{self.shot_id}_scene_manifest.json", "scene_manifest.json")
        self.validate_json_parse(self.control_dir / f"{self.episode_id}_{self.shot_id}_scene_manifest.json", "scene_manifest.json")
        self.validate_scene_mp4_exists_and_non_empty()

        # 6. QA artifacts
        print("\n--- 6. QA Artifacts ---")
        self.validate_file_exists(self.control_dir / "qa_report.json", "qa_report.json")
        self.validate_json_parse(self.control_dir / "qa_report.json", "qa_report.json")

        # 7. Audio policy artifacts
        print("\n--- 7. Audio Policy Artifacts ---")
        self.validate_file_exists(self.control_dir / f"{self.episode_id}_{self.shot_id}_audio_manifest.json", "audio_manifest.json")
        self.validate_json_parse(self.control_dir / f"{self.episode_id}_{self.shot_id}_audio_manifest.json", "audio_manifest.json")
        self.validate_no_fake_audio()

        # 8. Final render artifacts
        print("\n--- 8. Final Render Artifacts ---")
        self.validate_file_exists(self.control_dir / f"{self.episode_id}_{self.shot_id}_final_manifest.json", "final_manifest.json")
        self.validate_json_parse(self.control_dir / f"{self.episode_id}_{self.shot_id}_final_manifest.json", "final_manifest.json")
        self.validate_no_fake_final_mp4()
        self.validate_final_manifest_preserves_no_audio()

        # 9. State/Provenance artifacts
        print("\n--- 9. State/Provenance Artifacts ---")
        self.validate_file_exists(self.control_dir / "artifact_index.json", "artifact_index.json")
        self.validate_json_parse(self.control_dir / "artifact_index.json", "artifact_index.json")
        self.validate_file_exists(self.control_dir / f"{self.episode_id}_{self.shot_id}_ledger.json", "shot_ledger.json")
        self.validate_json_parse(self.control_dir / f"{self.episode_id}_{self.shot_id}_ledger.json", "shot_ledger.json")
        self.validate_file_exists(self.control_dir / self.episode_id / f"{self.shot_id}_state.json", "shot_state.json")
        self.validate_json_parse(self.control_dir / self.episode_id / f"{self.shot_id}_state.json", "shot_state.json")

        # 10. Artifact index references
        print("\n--- 10. Artifact Index References ---")
        self.validate_artifact_index_references()

        # 11. Ledger transitions
        print("\n--- 11. Ledger Transitions ---")
        self.validate_ledger_transitions()

        # 12. Terminal state
        print("\n--- 12. Terminal State ---")
        self.validate_terminal_state()

        # 13. Forbidden paths
        print("\n--- 13. Forbidden Paths Check ---")
        artifact_index_path = self.control_dir / "artifact_index.json"
        if artifact_index_path.exists():
            with open(artifact_index_path, 'r', encoding='utf-8') as f:
                artifact_index = json.load(f)
            self.validate_no_forbidden_paths(artifact_index, "artifact_index.json")

        # Print summary
        print(f"\n{'='*60}")
        print(f"Validation Summary")
        print(f"{'='*60}")
        print(f"Passed: {len(self.passed_checks)}")
        print(f"Warnings: {len(self.warnings)}")
        print(f"Errors: {len(self.errors)}")
        print(f"{'='*60}\n")

        if self.errors:
            print("❌ VALIDATION FAILED")
            for error in self.errors:
                print(f"  - {error}")
            return False
        else:
            print("✅ VALIDATION PASSED")
            if self.warnings:
                print("\nWarnings:")
                for warning in self.warnings:
                    print(f"  - {warning}")
            return True


def main():
    parser = argparse.ArgumentParser(description="Validate RC artifacts")
    parser.add_argument("--project-root", required=True, help="Project root directory")
    parser.add_argument("--episode", required=True, help="Episode ID")
    parser.add_argument("--shot", required=True, help="Shot ID")
    args = parser.parse_args()

    validator = RCValidator(args.project_root, args.episode, args.shot)
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
