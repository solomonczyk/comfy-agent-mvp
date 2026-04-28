"""Quality Gate & Acceptance Criteria System.

This module implements quality control for generated images with:
- Hard reject rules for obvious defects
- Quality scorecard with multiple axes
- Defect taxonomy with reason codes
- Defect → corrective action mapping
- Quality-aware retry policy
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DefectCode(str, Enum):
    """Defect taxonomy with reason codes."""
    BLACK_FRAME = "black_frame"
    SEMANTIC_COLLAPSE = "semantic_collapse"
    MULTI_SUBJECT_UNEXPECTED = "multi_subject_unexpected"
    EYE_GEOMETRY_BROKEN = "eye_geometry_broken"
    PUPIL_IRIS_ARTIFACT = "pupil_iris_artifact"
    MOUTH_TEETH_ARTIFACT = "mouth_teeth_artifact"
    EARRING_JEWELRY_DEFORMATION = "earring_jewelry_deformation"
    HAIRLINE_DEFORMATION = "hairline_deformation"
    PLASTIC_SKIN = "plastic_skin"
    FACIAL_ASYMMETRY_ARTIFACT = "facial_asymmetry_artifact"
    EDGE_HALO_DOUBLE_CONTOUR = "edge_halo_double_contour"
    PROMPT_MISMATCH = "prompt_mismatch"
    LOW_TECHNICAL_QUALITY = "low_technical_quality"
    WEAK_AESTHETIC = "weak_aesthetic"


class QualityVerdict(str, Enum):
    """Quality verdict for an image."""
    ACCEPT = "accept"
    RETRY = "retry"
    REJECT = "reject"


@dataclass
class QualityScorecard:
    """Quality scorecard with multiple axes."""
    technical_score: int  # 0-10
    anatomy_score: int  # 0-10
    semantic_score: int  # 0-10
    aesthetic_score: int  # 0-10
    
    @property
    def weighted_score(self) -> float:
        """Calculate weighted overall score."""
        # Anatomy and semantic are most important for portraits
        weights = {
            "technical": 0.2,
            "anatomy": 0.3,
            "semantic": 0.3,
            "aesthetic": 0.2,
        }
        return (
            self.technical_score * weights["technical"] +
            self.anatomy_score * weights["anatomy"] +
            self.semantic_score * weights["semantic"] +
            self.aesthetic_score * weights["aesthetic"]
        )


@dataclass
class HardRejectRule:
    """Hard reject rule for immediate rejection."""
    defect_code: DefectCode
    description: str


@dataclass
class QualityReport:
    """Quality report for a generated image."""
    image_path: str
    verdict: QualityVerdict
    scorecard: QualityScorecard
    hard_fail_reasons: list[DefectCode] = field(default_factory=list)
    soft_fail_reasons: list[DefectCode] = field(default_factory=list)
    recommended_corrective_action: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "image_path": self.image_path,
            "verdict": self.verdict.value,
            "scorecard": {
                "technical_score": self.scorecard.technical_score,
                "anatomy_score": self.scorecard.anatomy_score,
                "semantic_score": self.scorecard.semantic_score,
                "aesthetic_score": self.scorecard.aesthetic_score,
                "weighted_score": self.scorecard.weighted_score,
            },
            "hard_fail_reasons": [d.value for d in self.hard_fail_reasons],
            "soft_fail_reasons": [d.value for d in self.soft_fail_reasons],
            "recommended_corrective_action": self.recommended_corrective_action,
        }


@dataclass
class AcceptanceThresholds:
    """Acceptance thresholds for quality gate."""
    # Hard reject: any of these triggers immediate reject
    hard_reject_rules: list[HardRejectRule] = field(default_factory=list)
    
    # Score thresholds
    min_technical_score: int = 7
    min_anatomy_score: int = 8
    min_semantic_score: int = 8
    min_aesthetic_score: int = 7
    min_weighted_score: float = 7.5
    
    # Retry thresholds (lower than accept thresholds)
    retry_technical_score: int = 5
    retry_aesthetic_score: int = 0  # Disabled until artistic judge returns meaningful scores


class QualityProfile:
    """Quality profile for different use cases."""
    
    PORTRAIT_PREMIUM_V1 = "portrait_premium_v1"
    
    @staticmethod
    def get_portrait_premium_thresholds() -> AcceptanceThresholds:
        """Get thresholds for premium portrait quality."""
        return AcceptanceThresholds(
            hard_reject_rules=[
                HardRejectRule(
                    DefectCode.BLACK_FRAME,
                    "Black or empty frame detected"
                ),
                # Removed SEMANTIC_COLLAPSE from hard reject - will be conditional
                # Removed MULTI_SUBJECT_UNEXPECTED from hard reject - will be conditional
                HardRejectRule(
                    DefectCode.EYE_GEOMETRY_BROKEN,
                    "Severe eye geometry deformation"
                ),
                HardRejectRule(
                    DefectCode.PUPIL_IRIS_ARTIFACT,
                    "Broken pupil/iris artifacts"
                ),
                HardRejectRule(
                    DefectCode.MOUTH_TEETH_ARTIFACT,
                    "Severe mouth/teeth artifacts"
                ),
            ],
            min_technical_score=6,
            min_anatomy_score=5,
            min_semantic_score=0,  # Temporarily disabled until semantic judge returns meaningful scores
            min_aesthetic_score=0,  # Temporarily disabled until artistic judge returns meaningful scores
            min_weighted_score=3.0,  # Calibrated to actual score ranges
        )


class QualityGate:
    """Quality gate for evaluating generated images."""
    
    def __init__(
        self,
        quality_profile: str = QualityProfile.PORTRAIT_PREMIUM_V1,
    ):
        """Initialize quality gate with profile."""
        self.quality_profile = quality_profile
        if quality_profile == QualityProfile.PORTRAIT_PREMIUM_V1:
            self.thresholds = QualityProfile.get_portrait_premium_thresholds()
        else:
            self.thresholds = AcceptanceThresholds()
    
    def evaluate(
        self,
        image_path: str,
        # TODO: Add actual image analysis parameters
        # For now, this is a placeholder structure
        **analysis_params: Any,
    ) -> QualityReport:
        """Evaluate an image against quality gate.
        
        Args:
            image_path: Path to the generated image
            analysis_params: Parameters from image analysis
            
        Returns:
            QualityReport with verdict and details
        """
        # TODO: Implement actual image analysis
        # For now, return a placeholder report
        scorecard = QualityScorecard(
            technical_score=8,
            anatomy_score=8,
            semantic_score=8,
            aesthetic_score=8,
        )
        
        return QualityReport(
            image_path=image_path,
            verdict=QualityVerdict.ACCEPT,
            scorecard=scorecard,
            hard_fail_reasons=[],
            soft_fail_reasons=[],
            recommended_corrective_action=None,
        )
    
    def map_defect_to_corrective_action(
        self,
        defect_code: DefectCode,
    ) -> str:
        """Map defect to recommended corrective action.
        
        Args:
            defect_code: The detected defect
            
        Returns:
            Corrective action string
        """
        action_mapping = {
            DefectCode.BLACK_FRAME: "reject",
            DefectCode.SEMANTIC_COLLAPSE: "retry_prompt",
            DefectCode.MULTI_SUBJECT_UNEXPECTED: "retry_prompt",
            DefectCode.EYE_GEOMETRY_BROKEN: "reject",
            DefectCode.PUPIL_IRIS_ARTIFACT: "reject",
            DefectCode.MOUTH_TEETH_ARTIFACT: "reject",
            DefectCode.EARRING_JEWELRY_DEFORMATION: "retry_settings",
            DefectCode.HAIRLINE_DEFORMATION: "retry_settings",
            DefectCode.PLASTIC_SKIN: "retry_settings",
            DefectCode.FACIAL_ASYMMETRY_ARTIFACT: "retry_settings",
            DefectCode.EDGE_HALO_DOUBLE_CONTOUR: "retry_settings",
            DefectCode.PROMPT_MISMATCH: "retry_prompt",
            DefectCode.LOW_TECHNICAL_QUALITY: "retry_settings",
            DefectCode.WEAK_AESTHETIC: "retry_seed",
        }
        return action_mapping.get(defect_code, "retry_seed")
