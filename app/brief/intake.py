"""Brief Intake Contract Layer — convert user input into canonical brief artifacts.

This module implements the RC-COMBINE-V2-54001-62000 Brief Intake layer:
  - Defines the intake contract data model
  - Parses/normalizes user input into canonical brief fields
  - Validates required fields and constraints
  - Creates success/failure/blocked branches
  - Creates all canonical brief artifacts
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data schema
# ---------------------------------------------------------------------------

@dataclass
class BriefIntakeData:
    """Canonical brief intake contract consumed by DirectorPlannerAgent."""

    project_id: str = ""
    source_input: str = ""
    normalized_task_summary: str = ""
    content_type: str = "unknown"
    target_audience: str = ""
    goal: str = ""
    expected_output: str = ""
    duration_target: Optional[str] = None
    format_hint: Optional[str] = None
    aspect_ratio: Optional[str] = None
    language: str = "en"
    style_tone: Optional[str] = None
    topic_domain: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    readiness_for_director_planner: bool = False
    operator_review_required: bool = True
    production_accepted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BriefValidationReport:
    """Result of brief intake validation."""

    brief_contract_created: bool = False
    brief_validation_passed: bool = False
    classification: str = "blocked_invalid_input"
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    needs_operator_clarification: bool = False
    blocked_path_reached: bool = False
    blocker_reported: bool = False
    blocker_reason: str = ""
    brief_is_ready_for_director_planner: bool = False
    operator_review_required: bool = True
    production_accepted: bool = False
    generation_performed: bool = False
    downstream_executed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectConstraints:
    """Project-level constraints extracted from brief intake."""

    duration_target: Optional[str] = None
    format_hint: Optional[str] = None
    aspect_ratio: Optional[str] = None
    language: str = "en"
    style_tone: Optional[str] = None
    topic_domain: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    technical_restrictions: List[str] = field(default_factory=list)
    budget_hint: Optional[str] = None
    timeline_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContentIntent:
    """Content intent extracted from brief intake."""

    content_type: str = "unknown"
    goal: str = ""
    target_audience: str = ""
    expected_output: str = ""
    primary_purpose: str = ""
    secondary_purposes: List[str] = field(default_factory=list)
    key_message: Optional[str] = None
    call_to_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SuccessCriteria:
    """Success criteria for the brief."""

    criteria: List[str] = field(default_factory=list)
    quality_bars: List[str] = field(default_factory=list)
    acceptance_requirements: List[str] = field(default_factory=list)
    generated_defaults: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ForbiddenActions:
    """Actions explicitly forbidden for this brief."""

    forbidden_actions: List[str] = field(default_factory=list)
    dangerous_actions_blocked: List[str] = field(default_factory=list)
    generation_blocked: bool = True
    comfyui_submit_blocked: bool = True
    assembly_blocked: bool = True
    downstream_blocked: bool = True
    production_acceptance_blocked: bool = True
    visual_qa_skip_blocked: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Field extraction helpers
# ---------------------------------------------------------------------------

_CONTENT_TYPE_PATTERNS = [
    (r"\b(tutorial|walkthrough|guide|instructional)\b", "tutorial"),
    (r"\b(educational|explainer|how.to|lesson)\b", "educational"),
    (r"\b(promotional|advertisement|commercial|marketing|promo)\b", "promotional"),
    (r"\b(entertainment|entertaining|fun|humor|comedy)\b", "entertainment"),
    (r"\b(documentary|documentation|informational|informative)\b", "documentary"),
    (r"\b(product.?visual|product.?showcase|catalog|showcase)\b", "product_visual"),
    (r"\b(portrait|headshot|character|persona)\b", "portrait"),
    (r"\b(narrative|story|storytelling|cinematic|film)\b", "narrative"),
    (r"\b(social.?media|short|reel|tiktok|shorts)\b", "social_media"),
]

_AUDIENCE_PATTERNS = [
    (r"\b(beginners|beginner|novice|new.?to)\b", "beginners"),
    (r"\b(experts|expert|advanced)\b", "experts"),
    (r"\b(professionals|professional|industry)\b", "professionals"),
    (r"\b(children|kids|child)\b", "children"),
    (r"\b(adults|adult|general.?audience)\b", "adults"),
    (r"\b(students|student|academic)\b", "students"),
    (r"\b(developers|developer|engineers|engineer|technical)\b", "developers"),
]

_DURATION_PATTERNS = [
    (r"(\d+)\s*(?:second|sec|s)\b", "{} seconds"),
    (r"(\d+)\s*(?:minute|min|m)\b", "{} minutes"),
]

_FORMAT_PATTERNS = [
    (r"\b(16:?9|horizontal|landscape)\b", "16:9"),
    (r"\b(9:?16|vertical|portrait|reel|tiktok|shorts)\b", "9:16"),
    (r"\b(1:?1|square)\b", "1:1"),
    (r"\b(4:?3)\b", "4:3"),
]

_STYLE_PATTERNS = [
    (r"\b(professional|corporate|clean|polished)\b", "professional"),
    (r"\b( casual|friendly|conversational|relaxed)\b", "casual"),
    (r"\b(dramatic|cinematic|epic|intense)\b", "dramatic"),
    (r"\b(creative|artistic|stylized|abstract)\b", "creative"),
    (r"\b(minimalist|minimal|simple|clean)\b", "minimalist"),
    (r"\b(educational|clear|practical|instructive)\b", "clear_practical"),
    (r"\b(fun|playful|humorous|whimsical)\b", "fun"),
]

_LANGUAGE_PATTERNS = [
    (r"\b(ukrainian|ua|українськ)\b", "uk"),
    (r"\b(spanish|español|es)\b", "es"),
    (r"\b(french|français|fr)\b", "fr"),
    (r"\b(german|deutsch|de)\b", "de"),
    (r"\b(japanese|日本語|ja)\b", "ja"),
    (r"\b(chinese|中文|zh)\b", "zh"),
]


def _extract_content_type(text: str) -> str:
    for pattern, ctype in _CONTENT_TYPE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return ctype
    return "unknown"


def _extract_audience(text: str) -> str:
    for pattern, audience in _AUDIENCE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return audience
    return ""


def _extract_duration(text: str) -> Optional[str]:
    for pattern, template in _DURATION_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return template.format(m.group(1))
    return None


def _extract_format(text: str) -> Optional[str]:
    for pattern, fmt in _FORMAT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return fmt
    return None


def _extract_style(text: str) -> Optional[str]:
    for pattern, style in _STYLE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return style
    return None


def _extract_language(text: str) -> str:
    for pattern, lang in _LANGUAGE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return lang
    return "en"


def _extract_topic_domain(text: str) -> Optional[str]:
    """Try to identify the topic domain from the input text."""
    # Common domain patterns
    domains = [
        (r"\b(AI|artificial.?intelligence|machine.?learning|deep.?learning)\b", "artificial_intelligence"),
        (r"\b(pipeline|workflow|automation|production)\b", "production_pipeline"),
        (r"\b(animation|vfx|motion.?graphics|3D|CGI)\b", "animation_vfx"),
        (r"\b(education|e.?learning|course|training)\b", "education"),
        (r"\b(gaming|game|gamedev)\b", "gaming"),
        (r"\b(marketing|brand|branding)\b", "marketing"),
        (r"\b(health|medical|healthcare|wellness)\b", "healthcare"),
        (r"\b(finance|financial|banking|crypto)\b", "finance"),
        (r"\b(science|research|scientific|lab)\b", "science"),
        (r"\b(art|design|creative|visual)\b", "art_design"),
    ]
    for pattern, domain in domains:
        if re.search(pattern, text, re.IGNORECASE):
            return domain
    return None


def _extract_goal(text: str) -> str:
    """Extract or construct a goal statement from input text."""
    # Try to find explicit goal markers
    goal_patterns = [
        r"(?:goal|objective|purpose|aim)\s*(?:is|:)?\s*(.+?)(?:\.|$)",
        r"(?:create|build|make|develop|produce|generate)\s*(.+?)(?:\.|$)",
        r"(?:to|in order to)\s*(.+?)(?:\.|$)",
    ]
    for pat in goal_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    # Fallback: use first sentence
    first_sentence = text.split(".")[0].strip()
    if first_sentence:
        return first_sentence
    return ""


def _extract_expected_output(text: str) -> str:
    """Extract expected output description."""
    output_patterns = [
        r"(?:output|deliverable|produce|create|generate)\s*(?:a|an|the)?\s*(.+?)(?:\.|,|$)",
        r"(?:video|animation|explainer|clip|short|film|sequence)\s*(.+?)(?:\.|,|$)",
    ]
    for pat in output_patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return ("video " + m.group(1).strip()).strip()
    return ""


def _detect_dangerous_actions(text: str) -> List[str]:
    """Detect mentions of actions that should be forbidden."""
    dangerous = []
    dangerous_patterns = [
        (r"\b(skip.?review|skip.?qa|bypass|no.?review|auto.?accept)\b",
         "skip_quality_review"),
        (r"\b(generate|render|produce).{0,40}(without|no).{0,20}(review|check)\b",
         "generation_without_review"),
        (r"\b(production.?accept|finalize|ship|publish|release)\b",
         "premature_production_acceptance"),
        (r"\b(comfyui|workflow).{0,20}(submit|execute|run)\b",
         "unauthorized_workflow_execution"),
    ]
    for pattern, action in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            dangerous.append(action)
    return dangerous


def _generate_default_success_criteria(content_type: str, goal: str) -> List[str]:
    """Generate sensible default success criteria based on content type."""
    defaults = [
        "All generated assets are valid and readable",
        "Visual quality meets minimum threshold (no artifacts, proper framing)",
        "Content matches the specified intent and goal",
    ]
    if content_type == "educational":
        defaults.append("Information is clear and accurate")
        defaults.append("Visual aids support the educational content")
    elif content_type == "promotional":
        defaults.append("brand messaging is consistent and on-target")
        defaults.append("Visual appeal meets marketing standards")
    elif content_type == "portrait":
        defaults.append("Subject is properly framed and lit")
        defaults.append("Identity fidelity is preserved")
    return defaults


# ---------------------------------------------------------------------------
# Main pipeline functions
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _paths(project_root: str) -> Dict[str, Path]:
    root = Path(project_root)
    brief_dir = root / "output" / "control" / "brief"
    return {
        "root": root,
        "brief_dir": brief_dir,
        "contract": brief_dir / "brief_contract.json",
        "validation_report": brief_dir / "brief_validation_report.json",
        "constraints": brief_dir / "project_constraints.json",
        "content_intent": brief_dir / "content_intent.json",
        "success_criteria": brief_dir / "success_criteria.json",
        "forbidden_actions": brief_dir / "forbidden_actions.json",
        "operator_review_packet": brief_dir / "brief_operator_review_packet.json",
        "artifact_index": root / "output" / "control" / "artifact_index.json",
        "episode_ledger": root / "output" / "control" / "episode_ledger.json",
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _normalize_text(text: str) -> str:
    """Clean and normalize input text."""
    text = text.strip()
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text


def build_brief_intake(
    project_root: str,
    input_text: str,
) -> Dict[str, Any]:
    """Build all brief intake artifacts from raw user input.

    Returns a result dict with status, paths, and control flags.
    """
    # Check for blocked path first
    if not input_text or not input_text.strip():
        return _blocked_result(project_root, "Empty input: no user task text provided.")

    input_text = _normalize_text(input_text)

    # Danger detection
    dangerous = _detect_dangerous_actions(input_text)
    if dangerous:
        return _blocked_result(
            project_root,
            f"Input contains dangerous action references: {dangerous}. "
            "Generation, review-skipping, and production acceptance are not allowed in this layer.",
        )

    # --- Extract canonical fields ---
    content_type = _extract_content_type(input_text)
    audience = _extract_audience(input_text)
    goal = _extract_goal(input_text)
    expected_output = _extract_expected_output(input_text)
    duration = _extract_duration(input_text)
    fmt = _extract_format(input_text)
    style = _extract_style(input_text)
    language = _extract_language(input_text)
    topic = _extract_topic_domain(input_text)

    # Track missing fields
    missing = []
    if not goal:
        missing.append("goal")
    if not expected_output:
        missing.append("expected_output")
    if content_type == "unknown":
        missing.append("content_type")
    if not audience:
        missing.append("target_audience")
    if not topic:
        missing.append("topic_domain")

    # Construct normalized summary
    normalized = input_text

    # Default forbidden actions
    forbidden = [
        "generation_without_operator_authorization",
        "comfyui_submit",
        "final_render",
        "production_acceptance",
        "assembly_execution",
        "downstream_execution",
        "visual_qa_skip",
        "preview_render",
    ] + dangerous

    constraints = []
    if duration:
        constraints.append(f"Target duration: {duration}")
    if fmt:
        constraints.append(f"Format: {fmt}")

    # Default assumptions
    assumptions = [
        "Pipeline will stop at operator review for approval",
        "No generation will be performed without authorization",
        "All artifacts are validation/preparation only",
        "Production acceptance requires explicit operator sign-off",
    ]
    if content_type == "unknown":
        assumptions.append("Content type was not explicitly stated; defaulting to general video")
    if not audience:
        assumptions.append("Target audience not explicitly stated; will use general audience defaults")

    # Generate default success criteria if none provided
    success_criteria = _generate_default_success_criteria(content_type, goal)

    # Determine readiness
    is_ready = (
        bool(goal)
        and bool(expected_output)
        and content_type != "unknown"
        and len(missing) <= 2
    )

    # --- Build contract data ---
    contract = BriefIntakeData(
        project_id=Path(project_root).name,
        source_input=input_text,
        normalized_task_summary=normalized,
        content_type=content_type,
        target_audience=audience,
        goal=goal,
        expected_output=expected_output,
        duration_target=duration,
        format_hint=fmt,
        aspect_ratio=fmt,
        language=language,
        style_tone=style,
        topic_domain=topic,
        constraints=constraints,
        forbidden_actions=forbidden,
        success_criteria=success_criteria,
        missing_fields=missing,
        assumptions=assumptions,
        readiness_for_director_planner=is_ready,
        operator_review_required=True,
        production_accepted=False,
    )

    # --- Build constraints object ---
    constraints_obj = ProjectConstraints(
        duration_target=duration,
        format_hint=fmt,
        aspect_ratio=fmt,
        language=language,
        style_tone=style,
        topic_domain=topic,
        constraints=constraints,
        technical_restrictions=[
            "No real generation allowed at this layer",
            "All actions are dry-run / preparation only",
            "Operator review required before proceeding",
        ],
    )

    # --- Build content intent ---
    intent = ContentIntent(
        content_type=content_type,
        goal=goal,
        target_audience=audience,
        expected_output=expected_output,
        primary_purpose=goal if goal else "undetermined",
    )

    # --- Build success criteria object ---
    sc = SuccessCriteria(
        criteria=success_criteria,
        quality_bars=[
            "Assets must be valid and readable",
            "Content must match specified intent",
        ],
        acceptance_requirements=[
            "Operator review and approval required",
            "Production acceptance must be explicitly set",
        ],
        generated_defaults=not input_text.lower().count("success") > 0,
    )

    # --- Build forbidden actions object ---
    fa = ForbiddenActions(
        forbidden_actions=forbidden,
        dangerous_actions_blocked=dangerous,
        generation_blocked=True,
        comfyui_submit_blocked=True,
        assembly_blocked=True,
        downstream_blocked=True,
        production_acceptance_blocked=True,
        visual_qa_skip_blocked=True,
    )

    # --- Write all artifacts ---
    paths = _paths(project_root)
    timestamp = _now_iso()

    _write_json(paths["contract"], {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "schema_version": "1.0",
        "created_timestamp": timestamp,
        **contract.to_dict(),
    })

    _write_json(paths["constraints"], {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "created_timestamp": timestamp,
        **constraints_obj.to_dict(),
    })

    _write_json(paths["content_intent"], {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "created_timestamp": timestamp,
        **intent.to_dict(),
    })

    _write_json(paths["success_criteria"], {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "created_timestamp": timestamp,
        **sc.to_dict(),
    })

    _write_json(paths["forbidden_actions"], {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "created_timestamp": timestamp,
        **fa.to_dict(),
    })

    # --- Determine validation path ---
    if missing and not is_ready:
        # Incomplete but valid clarification path
        validation = BriefValidationReport(
            brief_contract_created=True,
            brief_validation_passed=False,
            classification="needs_operator_clarification",
            missing_fields=missing,
            needs_operator_clarification=True,
            operator_review_required=True,
            production_accepted=False,
        )
    else:
        # Success path
        validation = BriefValidationReport(
            brief_contract_created=True,
            brief_validation_passed=True,
            classification="valid_for_director_planning",
            brief_is_ready_for_director_planner=True,
            operator_review_required=True,
            production_accepted=False,
        )

    _write_json(paths["validation_report"], {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "created_timestamp": timestamp,
        **validation.to_dict(),
    })

    # --- Update artifact_index ---
    _update_artifact_index(paths, timestamp)

    # --- Update episode_ledger ---
    classification = validation.classification
    _update_episode_ledger(paths, timestamp, classification)

    # --- Update state to brief_operator_review_required ---
    _force_artifact_index_state(paths, "brief_operator_review_required")

    # --- Build result ---
    result = {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "brief_contract_created": True,
        "brief_validation_already_passed": validation.brief_validation_passed,
        "brief_is_ready_for_director_planner": validation.brief_is_ready_for_director_planner,
        "needs_operator_clarification": validation.needs_operator_clarification,
        "missing_fields": missing,
        "operator_review_required": True,
        "current_state": "brief_operator_review_required",
        "next_allowed_action": "brief_operator_review_required",
        "production_accepted": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "artifacts_created": [
            str(paths["contract"].relative_to(paths["root"])),
            str(paths["validation_report"].relative_to(paths["root"])),
            str(paths["constraints"].relative_to(paths["root"])),
            str(paths["content_intent"].relative_to(paths["root"])),
            str(paths["success_criteria"].relative_to(paths["root"])),
            str(paths["forbidden_actions"].relative_to(paths["root"])),
        ],
    }
    return result


def validate_brief_intake(project_root: str) -> Dict[str, Any]:
    """Validate existing brief intake artifacts.

    Reads the brief_contract.json and re-validates.
    Returns the validation report.
    """
    paths = _paths(project_root)
    timestamp = _now_iso()

    contract_data = _load_json(paths["contract"])
    if contract_data is None:
        result = {
            "brief_contract_created": False,
            "brief_validation_passed": False,
            "classification": "blocked_invalid_input",
            "blocked_path_reached": True,
            "blocker_reported": True,
            "blocker_reason": "brief_contract.json not found — build brief intake first",
            "operator_review_required": True,
            "production_accepted": False,
            "generation_performed": False,
            "downstream_executed": False,
        }
        _write_json(paths["validation_report"], {
            "task_id": "RC-COMBINE-V2-54001-62000",
            "created_timestamp": timestamp,
            **result,
        })
        return result

    # Re-validate from stored contract
    missing = contract_data.get("missing_fields", [])
    is_ready = contract_data.get("readiness_for_director_planner", False)
    prod_accepted = contract_data.get("production_accepted", False)

    if prod_accepted:
        return {
            "brief_contract_created": True,
            "brief_validation_passed": False,
            "classification": "blocked_invalid_input",
            "blocked_path_reached": True,
            "blocker_reported": True,
            "blocker_reason": "production_accepted is true in contract — invalid for intake layer",
            "operator_review_required": True,
            "production_accepted": True,
            "generation_performed": False,
            "downstream_executed": False,
        }

    if missing and not is_ready:
        validation = {
            "brief_contract_created": True,
            "brief_validation_passed": False,
            "classification": "needs_operator_clarification",
            "missing_fields": missing,
            "needs_operator_clarification": True,
            "operator_review_required": True,
            "production_accepted": False,
            "generation_performed": False,
            "downstream_executed": False,
        }
    else:
        validation = {
            "brief_contract_created": True,
            "brief_validation_passed": True,
            "classification": "valid_for_director_planning",
            "brief_is_ready_for_director_planner": True,
            "operator_review_required": True,
            "production_accepted": False,
            "generation_performed": False,
            "downstream_executed": False,
        }

    _write_json(paths["validation_report"], {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "created_timestamp": timestamp,
        **validation,
    })
    return validation


def build_brief_operator_review(project_root: str) -> Dict[str, Any]:
    """Build the operator review packet summarizing the brief intake."""
    paths = _paths(project_root)
    timestamp = _now_iso()

    contract_data = _load_json(paths["contract"]) or {}
    validation_data = _load_json(paths["validation_report"]) or {}
    constraints_data = _load_json(paths["constraints"]) or {}
    intent_data = _load_json(paths["content_intent"]) or {}
    sc_data = _load_json(paths["success_criteria"]) or {}
    fa_data = _load_json(paths["forbidden_actions"]) or {}

    classification = validation_data.get("classification", "unknown")
    missing = contract_data.get("missing_fields", validation_data.get("missing_fields", []))
    is_ready = contract_data.get("readiness_for_director_planner", False) or validation_data.get("brief_is_ready_for_director_planner", False)

    packet = {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "packet_type": "brief_operator_review",
        "created_timestamp": timestamp,
        "normalized_brief": {
            "project_id": contract_data.get("project_id", ""),
            "content_type": contract_data.get("content_type", "unknown"),
            "goal": contract_data.get("goal", ""),
            "expected_output": contract_data.get("expected_output", ""),
            "target_audience": contract_data.get("target_audience", ""),
            "duration_target": contract_data.get("duration_target", ""),
            "format_hint": contract_data.get("format_hint", ""),
            "style_tone": contract_data.get("style_tone", ""),
            "topic_domain": contract_data.get("topic_domain", ""),
        },
        "missing_fields": missing,
        "assumptions": contract_data.get("assumptions", []),
        "risks": [
            "Missing fields may cause downstream planning to guess incorrectly",
            "No generation has been performed — all artifacts are preparation only",
            "Operator review required before proceeding to Director Planning",
            "Dangerous actions detected in input are blocked",
        ],
        "forbidden_actions": fa_data.get("forbidden_actions", contract_data.get("forbidden_actions", [])),
        "dangerous_actions_blocked": fa_data.get("dangerous_actions_blocked", []),
        "success_criteria": sc_data.get("criteria", contract_data.get("success_criteria", [])),
        "constraints": constraints_data.get("constraints", contract_data.get("constraints", [])),
        "readiness_for_director_planner": is_ready,
        "validation_classification": classification,
        "operator_review_required": True,
        "production_accepted": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "next_recommended_layer": "RC-COMBINE-V2-62001-70000 Director Planning and Shot Contract Layer",
        "notes": "Operator must review the normalized brief, confirm or correct missing fields, then authorize proceeding to Director Planning.",
    }

    _write_json(paths["operator_review_packet"], {
        **packet,
    })
    return packet


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _blocked_result(project_root: str, reason: str) -> Dict[str, Any]:
    """Build a blocked-path result."""
    paths = _paths(project_root)
    timestamp = _now_iso()

    result = {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "brief_contract_created": False,
        "brief_validation_passed": False,
        "blocked_path_reached": True,
        "blocker_reported": True,
        "blocker_reason": reason,
        "operator_review_required": True,
        "current_state": "brief_operator_review_required",
        "next_allowed_action": "brief_operator_review_required",
        "production_accepted": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "visual_qa_executed": False,
    }

    _write_json(paths["validation_report"], {
        "task_id": "RC-COMBINE-V2-54001-62000",
        "created_timestamp": timestamp,
        "brief_contract_created": False,
        "brief_validation_passed": False,
        "classification": "blocked_invalid_input",
        "blocked_path_reached": True,
        "blocker_reported": True,
        "blocker_reason": reason,
        "operator_review_required": True,
        "production_accepted": False,
        "generation_performed": False,
        "downstream_executed": False,
    })

    _update_artifact_index(paths, timestamp)
    _update_episode_ledger(paths, timestamp, "blocked_invalid_input")
    _force_artifact_index_state(paths, "brief_operator_review_required")
    return result


def _update_artifact_index(paths: Dict[str, Path], timestamp: str) -> None:
    """Update artifact_index.json with brief intake artifact paths."""
    index = _load_json(paths["artifact_index"])
    if index is None:
        index = {}

    brief_artifacts = [
        "brief/brief_contract.json",
        "brief/brief_validation_report.json",
        "brief/project_constraints.json",
        "brief/content_intent.json",
        "brief/success_criteria.json",
        "brief/forbidden_actions.json",
    ]

    existing = index.get("artifacts", [])
    for artifact in brief_artifacts:
        if artifact not in existing:
            existing.append(artifact)

    index["artifacts"] = existing
    index["task_id"] = "RC-COMBINE-V2-54001-62000"
    index["created_timestamp"] = timestamp
    index["total_artifacts"] = len(existing)
    index["brief_intake_layer_completed"] = True
    _write_json(paths["artifact_index"], index)


def _force_artifact_index_state(paths: Dict[str, Path], state: str) -> None:
    """Force the artifact_index current_state to a specific value."""
    index = _load_json(paths["artifact_index"])
    if index is None:
        index = {}
    index["current_state"] = state
    index["next_allowed_action"] = state
    _write_json(paths["artifact_index"], index)


def _update_episode_ledger(
    paths: Dict[str, Path],
    timestamp: str,
    classification: str,
) -> None:
    """Append a brief intake layer event to the episode ledger."""
    ledger_path = paths["episode_ledger"]
    ledger = _load_json(ledger_path)
    if ledger is None:
        ledger = []

    event = {
        "event": "brief_intake_layer_completed",
        "task_id": "RC-COMBINE-V2-54001-62000",
        "status": "brief_operator_review_required",
        "classification": classification,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "visual_qa_executed": False,
        "preview_render_executed": False,
        "voice_generation_executed": False,
        "current_state": "brief_operator_review_required",
        "next_allowed_action": "brief_operator_review_required",
        "previous_layer": "RC-COMBINE-V2-46001-54000",
        "next_layer": "RC-COMBINE-V2-62001-70000 Director Planning and Shot Contract Layer",
        "timestamp": timestamp,
    }

    if isinstance(ledger, list):
        ledger.append(event)
    elif isinstance(ledger, dict):
        events = ledger.get("events", [])
        events.append(event)
        ledger["events"] = events
        ledger["current_state"] = "brief_operator_review_required"
        ledger["next_allowed_action"] = "brief_operator_review_required"
        ledger["production_accepted"] = False

    _write_json(ledger_path, ledger)
