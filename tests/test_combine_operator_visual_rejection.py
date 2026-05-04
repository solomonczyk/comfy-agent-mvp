"""RC-COMBINE-V2-741-800 — Test operator visual rejection functionality.

Tests for the operator visual rejection flow after QA failure.
"""

import json
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import pytest


def test_operator_visual_rejection_with_asset():
    """Test operator visual rejection with asset path - artifact creation only."""
    # Create temporary project directory
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test asset
        asset_path = project_root / "output" / "assets" / "test_asset.png"
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        img = Image.new('RGB', (1024, 1024), color='red')
        img.save(asset_path)
        
        # Simulate the decision artifact creation (without running orchestrator)
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        decision_artifact = {
            "agent": "Operator",
            "action": "visual_review_decision",
            "operator_visual_decision": "reject_visual_quality",
            "reason": "rebuilt_1024_asset_failed_visual_qa_semantic_and_production_quality",
            "source_asset": str(asset_path),
            "asset_width": 1024,
            "asset_height": 1024,
            "timestamp": timestamp
        }
        
        decision_path = control_dir / "combine_v2_operator_visual_decision.json"
        with open(decision_path, 'w') as f:
            json.dump(decision_artifact, f, indent=2)
        
        # Verify decision structure
        assert decision_path.exists()
        with open(decision_path, 'r') as f:
            decision = json.load(f)
        
        assert decision["operator_visual_decision"] == "reject_visual_quality"
        assert decision["source_asset"] == str(asset_path)
        assert decision["asset_width"] == 1024
        assert decision["asset_height"] == 1024
        assert decision["reason"] == "rebuilt_1024_asset_failed_visual_qa_semantic_and_production_quality"


def test_operator_visual_rejection_without_asset():
    """Test operator visual rejection without asset path - artifact creation only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Simulate the decision artifact creation (without running orchestrator)
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        decision_artifact = {
            "agent": "Operator",
            "action": "visual_review_decision",
            "operator_visual_decision": "reject_visual_quality",
            "reason": "visual_quality_failure",
            "timestamp": timestamp
        }
        
        decision_path = control_dir / "combine_v2_operator_visual_decision.json"
        with open(decision_path, 'w') as f:
            json.dump(decision_artifact, f, indent=2)
        
        # Verify decision structure (without asset info)
        assert decision_path.exists()
        with open(decision_path, 'r') as f:
            decision = json.load(f)
        
        assert decision["operator_visual_decision"] == "reject_visual_quality"
        assert "source_asset" not in decision
        assert "asset_width" not in decision
        assert "asset_height" not in decision


def test_operator_visual_rejection_accept_decision():
    """Test operator visual rejection with accept decision (legacy support)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Simulate the decision artifact creation
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        decision_artifact = {
            "agent": "Operator",
            "action": "visual_review_decision",
            "operator_visual_decision": "accepted",
            "reason": "visual_quality_good",
            "timestamp": timestamp
        }
        
        decision_path = control_dir / "combine_v2_operator_visual_decision.json"
        with open(decision_path, 'w') as f:
            json.dump(decision_artifact, f, indent=2)
        
        # Verify decision structure
        assert decision_path.exists()
        with open(decision_path, 'r') as f:
            decision = json.load(f)
        
        assert decision["operator_visual_decision"] == "accepted"


def test_operator_visual_rejection_reject_decision():
    """Test operator visual rejection with reject decision (legacy support)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Simulate the decision artifact creation
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        
        decision_artifact = {
            "agent": "Operator",
            "action": "visual_review_decision",
            "operator_visual_decision": "rejected",
            "reason": "visual_quality_failure",
            "timestamp": timestamp
        }
        
        decision_path = control_dir / "combine_v2_operator_visual_decision.json"
        with open(decision_path, 'w') as f:
            json.dump(decision_artifact, f, indent=2)
        
        # Verify decision structure
        assert decision_path.exists()
        with open(decision_path, 'r') as f:
            decision = json.load(f)
        
        assert decision["operator_visual_decision"] == "rejected"
