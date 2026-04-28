from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


JudgeVerdict = Literal["pass", "retry", "reject"]
NextAction = Literal[
    "accept",
    "retry_seed",
    "retry_prompt",
    "retry_settings",
    "switch_workflow",
    "reject",
]


@dataclass
class JudgeIssue:
    code: str
    message: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"


@dataclass
class JudgeReport:
    judge_name: Literal["technical", "semantic", "artistic"]
    score: float
    verdict: JudgeVerdict
    blocking_issues: list[JudgeIssue] = field(default_factory=list)
    issues: list[JudgeIssue] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    recommended_repairs: list[str] = field(default_factory=list)
    subscores: dict[str, float] = field(default_factory=dict)
    raw_notes: dict[str, Any] = field(default_factory=dict)


@dataclass
class JudgeInput:
    user_prompt: str
    final_positive_prompt: str | None
    preset_name: str | None
    rewrite_mode: str | None
    seed: int | None
    images: list[dict[str, Any]]
    primary_image_path: str
    width: int | None = None
    height: int | None = None
    metadata_path: str | None = None


@dataclass
class OrchestratorReport:
    final_score: float
    final_verdict: JudgeVerdict
    technical: JudgeReport
    semantic: JudgeReport
    artistic: JudgeReport
    global_blockers: list[JudgeIssue] = field(default_factory=list)
    global_repairs: list[str] = field(default_factory=list)
    best_next_action: NextAction = "reject"
    raw_notes: dict[str, Any] = field(default_factory=dict)
    quality_report: Any = None  # QualityReport from judge_orchestrator
