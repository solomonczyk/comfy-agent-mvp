#!/usr/bin/env python
"""Test script to diagnose inspect-production-decision-state hang"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.production_cards.state_repair import inspect_real_project_decision_state

project_root = r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01"
print(f"Calling inspect_real_project_decision_state with: {project_root}", file=sys.stderr)
sys.stderr.flush()

result = inspect_real_project_decision_state(project_root)

print("Result:", file=sys.stderr)
import json
print(json.dumps(result, indent=2))
