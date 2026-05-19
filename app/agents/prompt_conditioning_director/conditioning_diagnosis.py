"""
Conditioning Failure Diagnosis

Diagnosis of why previous conditioning caused face-crop failure.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ConditioningDiagnosis:
    """
    Diagnosis of conditioning failure.

    Explains why previous generations produced crop failure and
    identifies root causes.
    """

    diagnosis_type: str = "conditioning_failure_diagnosis"
    rejection_reason: str = ""

    # Root causes
    root_causes: List[str] = field(default_factory=list)

    # Detailed findings
    findings: Dict[str, Any] = field(default_factory=dict)

    # Conditioning issues
    conditioning_issues: List[str] = field(default_factory=list)

    # Reference role issues
    reference_role_issues: List[str] = field(default_factory=list)

    # Workflow issues
    workflow_issues: List[str] = field(default_factory=list)

    # Previous curator limitations
    previous_curator_limitations: List[str] = field(default_factory=list)

    # Recommended fixes
    recommended_fixes: List[str] = field(default_factory=list)

    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    task_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert diagnosis to dictionary."""
        return {
            "diagnosis_type": self.diagnosis_type,
            "rejection_reason": self.rejection_reason,
            "root_causes": self.root_causes,
            "findings": self.findings,
            "conditioning_issues": self.conditioning_issues,
            "reference_role_issues": self.reference_role_issues,
            "workflow_issues": self.workflow_issues,
            "previous_curator_limitations": self.previous_curator_limitations,
            "recommended_fixes": self.recommended_fixes,
            "created_at": self.created_at,
            "task_id": self.task_id,
        }

    def diagnose_crop_failure(
        self,
        rejection_reason: str,
        context_pack: Dict[str, Any],
    ) -> None:
        """
        Diagnose crop failure from rejection reason and context.

        Args:
            rejection_reason: Operator rejection reason
            context_pack: Context pack with references and previous generation info
        """
        self.rejection_reason = rejection_reason

        # Analyze rejection reason
        if "crop" in rejection_reason.lower() or "face" in rejection_reason.lower():
            self.root_causes.extend([
                "close-up / eyes / face quality reference leaked into composition role",
                "quality reference was treated as framing/pose conditioning",
                "prompt did not strongly enforce medium/full normal framing",
                "workflow allowed face-region conditioning to dominate output",
                "reference role separation was insufficient",
                "previous curator was rule-based, not brain decision layer",
            ])

        # Analyze quality references
        quality_refs = context_pack.get("quality_references", [])
        if quality_refs:
            self.findings["quality_references_found"] = len(quality_refs)
            self.reference_role_issues.extend([
                "quality close-up references present without explicit role separation",
                "quality references likely influenced camera distance",
                "eyes/face closeups may have been used as composition references",
            ])

        # Analyze conditioning
        self.conditioning_issues.extend([
            "face-region conditioning weight too high",
            "lack of explicit framing constraints in prompt",
            "no composition control separate from quality calibration",
        ])

        # Analyze workflow
        self.workflow_issues.extend([
            "workflow does not separate quality from composition conditioning",
            "camera distance not explicitly controlled",
            "framing policy not enforced at workflow level",
        ])

        # Previous curator limitations
        self.previous_curator_limitations.extend([
            "rule-based curator cannot understand visual intent",
            "no brain decision layer for reference role assignment",
            "quality references automatically applied without role awareness",
        ])

        # Recommended fixes
        self.recommended_fixes.extend([
            "implement brain-enabled reference role assignment",
            "separate quality calibration from composition control",
            "add explicit framing policy to prompt",
            "reduce face-region conditioning weight",
            "add composition control from explicit framing policy",
            "disable close-up reference influence on camera distance",
        ])

    def save(self, path: str) -> None:
        """Save diagnosis to JSON file."""
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> "ConditioningDiagnosis":
        """Load diagnosis from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
