"""
Test script for Judge Layer v0 pipeline with repairs.
Demonstrates the full judge workflow with 3 scenarios:
- good: high-quality image → pass
- semantic_wrong: semantically incorrect → retry_prompt
- technical_broken: technically broken → retry_settings or reject
"""
import json
from pathlib import Path

from app.judges.base_types import JudgeInput
from app.judges.technical_judge import TechnicalJudge
from app.judges.semantic_judge import SemanticJudge
from app.judges.artistic_judge import ArtisticJudge
from app.judges.judge_orchestrator import JudgeOrchestrator
from app.judges.retry_controller import RetryController
from app.judges.mock_vision_client import MockVisionJudgeClient


# removed: test_scenario helper function and test_judge_pipeline - requires external dependencies
