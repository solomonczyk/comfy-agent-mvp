"""RC-COMBINE-V2-1521-1580 — Test Corrective Retry V3 Output Collector Audit.

Tests for auditing corrective retry V3 output collector behavior and failure.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime, timezone
import sys

# Add app directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cli import combine_audit_corrective_retry_v3_output_collector


@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project directory structure."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    assets_dir = project_root / "output" / "assets"
    assets_dir.mkdir(parents=True)
    
    return project_root


class TestCorrectiveRetryV3OutputCollectorAudit:
    """Test suite for corrective retry V3 output collector audit."""
    
    def test_stub_generation_detected_true(self, temp_project_dir):
        """Test that stub generation is detected in generation result."""
        control_dir = temp_project_dir / "output" / "control"
        assets_dir = temp_project_dir / "output" / "assets"
        
        # Create V3 generation result with stub_generation
        v3_generation_result = {
            "stub_generation": True,
            "generation_performed": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
            json.dump(v3_generation_result, f)
        
        # Create V3 outputs manifest
        v3_outputs_manifest = {
            "generated_assets": ["output/assets/corrupted_v3_asset.png"],
            "stub_asset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
            json.dump(v3_outputs_manifest, f)
        
        # Create V3 generation trace
        v3_generation_trace = {
            "events": [
                {"event": "output_collection", "status": "pending"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_trace.json", 'w') as f:
            json.dump(v3_generation_trace, f)
        
        # Create corrupted asset file
        with open(assets_dir / "corrupted_v3_asset.png", 'wb') as f:
            f.write(b'stub')
        
        # Execute audit
        args = type('Args', (), {
            'project_root': str(temp_project_dir),
            'shot_id': 'shot01',
            'json': True
        })()
        
        result = combine_audit_corrective_retry_v3_output_collector(args)
        
        # Load audit report
        with open(control_dir / "combine_v2_corrective_retry_v3_output_collector_audit.json", 'r') as f:
            audit = json.load(f)
        
        assert audit["stub_generation_detected"] is True
        assert result == 0
    
    def test_stub_asset_detected_true(self, temp_project_dir):
        """Test that stub asset is detected in manifest."""
        control_dir = temp_project_dir / "output" / "control"
        assets_dir = temp_project_dir / "output" / "assets"
        
        # Create V3 generation result
        v3_generation_result = {
            "stub_generation": True,
            "generation_performed": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
            json.dump(v3_generation_result, f)
        
        # Create V3 outputs manifest with stub_asset
        v3_outputs_manifest = {
            "generated_assets": ["output/assets/corrupted_v3_asset.png"],
            "stub_asset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
            json.dump(v3_outputs_manifest, f)
        
        # Create V3 generation trace
        v3_generation_trace = {
            "events": [
                {"event": "output_collection", "status": "pending"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_trace.json", 'w') as f:
            json.dump(v3_generation_trace, f)
        
        # Create corrupted asset file
        with open(assets_dir / "corrupted_v3_asset.png", 'wb') as f:
            f.write(b'stub')
        
        # Execute audit
        args = type('Args', (), {
            'project_root': str(temp_project_dir),
            'shot_id': 'shot01',
            'json': True
        })()
        
        result = combine_audit_corrective_retry_v3_output_collector(args)
        
        # Load audit report
        with open(control_dir / "combine_v2_corrective_retry_v3_output_collector_audit.json", 'r') as f:
            audit = json.load(f)
        
        assert audit["stub_asset_detected"] is True
        assert result == 0
    
    def test_output_collection_status_pending(self, temp_project_dir):
        """Test that output collection status is detected as pending."""
        control_dir = temp_project_dir / "output" / "control"
        assets_dir = temp_project_dir / "output" / "assets"
        
        # Create V3 generation result
        v3_generation_result = {
            "stub_generation": True,
            "generation_performed": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
            json.dump(v3_generation_result, f)
        
        # Create V3 outputs manifest
        v3_outputs_manifest = {
            "generated_assets": ["output/assets/corrupted_v3_asset.png"],
            "stub_asset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
            json.dump(v3_outputs_manifest, f)
        
        # Create V3 generation trace with pending output collection
        v3_generation_trace = {
            "events": [
                {"event": "output_collection", "status": "pending"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_trace.json", 'w') as f:
            json.dump(v3_generation_trace, f)
        
        # Create corrupted asset file
        with open(assets_dir / "corrupted_v3_asset.png", 'wb') as f:
            f.write(b'stub')
        
        # Execute audit
        args = type('Args', (), {
            'project_root': str(temp_project_dir),
            'shot_id': 'shot01',
            'json': True
        })()
        
        result = combine_audit_corrective_retry_v3_output_collector(args)
        
        # Load audit report
        with open(control_dir / "combine_v2_corrective_retry_v3_output_collector_audit.json", 'r') as f:
            audit = json.load(f)
        
        assert audit["output_collection_status"] == "pending"
        assert audit["output_collection_executed"] is False
        assert result == 0
    
    def test_output_collection_not_executed(self, temp_project_dir):
        """Test that output collection was not executed."""
        control_dir = temp_project_dir / "output" / "control"
        assets_dir = temp_project_dir / "output" / "assets"
        
        # Create V3 generation result
        v3_generation_result = {
            "stub_generation": True,
            "generation_performed": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
            json.dump(v3_generation_result, f)
        
        # Create V3 outputs manifest
        v3_outputs_manifest = {
            "generated_assets": ["output/assets/corrupted_v3_asset.png"],
            "stub_asset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
            json.dump(v3_outputs_manifest, f)
        
        # Create V3 generation trace with pending output collection
        v3_generation_trace = {
            "events": [
                {"event": "output_collection", "status": "pending"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_trace.json", 'w') as f:
            json.dump(v3_generation_trace, f)
        
        # Create corrupted asset file
        with open(assets_dir / "corrupted_v3_asset.png", 'wb') as f:
            f.write(b'stub')
        
        # Execute audit
        args = type('Args', (), {
            'project_root': str(temp_project_dir),
            'shot_id': 'shot01',
            'json': True
        })()
        
        result = combine_audit_corrective_retry_v3_output_collector(args)
        
        # Load audit report
        with open(control_dir / "combine_v2_corrective_retry_v3_output_collector_audit.json", 'r') as f:
            audit = json.load(f)
        
        assert audit["output_collection_executed"] is False
        assert result == 0
    
    def test_comfyui_execution_stubbed_true(self, temp_project_dir):
        """Test that ComfyUI execution was stubbed."""
        control_dir = temp_project_dir / "output" / "control"
        assets_dir = temp_project_dir / "output" / "assets"
        
        # Create V3 generation result
        v3_generation_result = {
            "stub_generation": True,
            "generation_performed": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
            json.dump(v3_generation_result, f)
        
        # Create V3 outputs manifest
        v3_outputs_manifest = {
            "generated_assets": ["output/assets/corrupted_v3_asset.png"],
            "stub_asset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
            json.dump(v3_outputs_manifest, f)
        
        # Create V3 generation trace with stubbed ComfyUI execution
        v3_generation_trace = {
            "events": [
                {"event": "comfyui_execution", "executed": True, "stub": True},
                {"event": "output_collection", "status": "pending"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_trace.json", 'w') as f:
            json.dump(v3_generation_trace, f)
        
        # Create corrupted asset file
        with open(assets_dir / "corrupted_v3_asset.png", 'wb') as f:
            f.write(b'stub')
        
        # Execute audit
        args = type('Args', (), {
            'project_root': str(temp_project_dir),
            'shot_id': 'shot01',
            'json': True
        })()
        
        result = combine_audit_corrective_retry_v3_output_collector(args)
        
        # Load audit report
        with open(control_dir / "combine_v2_corrective_retry_v3_output_collector_audit.json", 'r') as f:
            audit = json.load(f)
        
        assert audit["comfyui_execution_stubbed"] is True
        assert result == 0
    
    def test_collector_reliability_guard_preserved_true(self, temp_project_dir):
        """Test that collector reliability guard was preserved."""
        control_dir = temp_project_dir / "output" / "control"
        assets_dir = temp_project_dir / "output" / "assets"
        
        # Create V3 generation result with collector_reliability_guard_preserved
        v3_generation_result = {
            "stub_generation": True,
            "generation_performed": True,
            "collector_reliability_guard_preserved": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
            json.dump(v3_generation_result, f)
        
        # Create V3 outputs manifest
        v3_outputs_manifest = {
            "generated_assets": ["output/assets/corrupted_v3_asset.png"],
            "stub_asset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
            json.dump(v3_outputs_manifest, f)
        
        # Create V3 generation trace
        v3_generation_trace = {
            "events": [
                {"event": "output_collection", "status": "pending"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_trace.json", 'w') as f:
            json.dump(v3_generation_trace, f)
        
        # Create corrupted asset file
        with open(assets_dir / "corrupted_v3_asset.png", 'wb') as f:
            f.write(b'stub')
        
        # Execute audit
        args = type('Args', (), {
            'project_root': str(temp_project_dir),
            'shot_id': 'shot01',
            'json': True
        })()
        
        result = combine_audit_corrective_retry_v3_output_collector(args)
        
        # Load audit report
        with open(control_dir / "combine_v2_corrective_retry_v3_output_collector_audit.json", 'r') as f:
            audit = json.load(f)
        
        assert audit["collector_reliability_guard_preserved"] is True
        assert result == 0
    
    def test_output_path_contract_preserved_true(self, temp_project_dir):
        """Test that output path contract was preserved."""
        control_dir = temp_project_dir / "output" / "control"
        assets_dir = temp_project_dir / "output" / "assets"
        
        # Create V3 generation result with output_path_contract_preserved
        v3_generation_result = {
            "stub_generation": True,
            "generation_performed": True,
            "output_path_contract_preserved": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
            json.dump(v3_generation_result, f)
        
        # Create V3 outputs manifest
        v3_outputs_manifest = {
            "generated_assets": ["output/assets/corrupted_v3_asset.png"],
            "stub_asset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
            json.dump(v3_outputs_manifest, f)
        
        # Create V3 generation trace
        v3_generation_trace = {
            "events": [
                {"event": "output_collection", "status": "pending"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_trace.json", 'w') as f:
            json.dump(v3_generation_trace, f)
        
        # Create corrupted asset file
        with open(assets_dir / "corrupted_v3_asset.png", 'wb') as f:
            f.write(b'stub')
        
        # Execute audit
        args = type('Args', (), {
            'project_root': str(temp_project_dir),
            'shot_id': 'shot01',
            'json': True
        })()
        
        result = combine_audit_corrective_retry_v3_output_collector(args)
        
        # Load audit report
        with open(control_dir / "combine_v2_corrective_retry_v3_output_collector_audit.json", 'r') as f:
            audit = json.load(f)
        
        assert audit["output_path_contract_preserved"] is True
        assert result == 0
    
    def test_collector_failure_confirmed_true(self, temp_project_dir):
        """Test that collector failure is confirmed when stub generation detected."""
        control_dir = temp_project_dir / "output" / "control"
        assets_dir = temp_project_dir / "output" / "assets"
        
        # Create V3 generation result
        v3_generation_result = {
            "stub_generation": True,
            "generation_performed": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
            json.dump(v3_generation_result, f)
        
        # Create V3 outputs manifest
        v3_outputs_manifest = {
            "generated_assets": ["output/assets/corrupted_v3_asset.png"],
            "stub_asset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
            json.dump(v3_outputs_manifest, f)
        
        # Create V3 generation trace
        v3_generation_trace = {
            "events": [
                {"event": "output_collection", "status": "pending"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_trace.json", 'w') as f:
            json.dump(v3_generation_trace, f)
        
        # Create corrupted asset file
        with open(assets_dir / "corrupted_v3_asset.png", 'wb') as f:
            f.write(b'stub')
        
        # Execute audit
        args = type('Args', (), {
            'project_root': str(temp_project_dir),
            'shot_id': 'shot01',
            'json': True
        })()
        
        result = combine_audit_corrective_retry_v3_output_collector(args)
        
        # Load audit report
        with open(control_dir / "combine_v2_corrective_retry_v3_output_collector_audit.json", 'r') as f:
            audit = json.load(f)
        
        assert audit["collector_failure_confirmed"] is True
        assert audit["failure_mode"] == "stub_generation_layer"
        assert result == 0
    
    def test_v3_asset_corrupted_true(self, temp_project_dir):
        """Test that V3 asset is detected as corrupted."""
        control_dir = temp_project_dir / "output" / "control"
        assets_dir = temp_project_dir / "output" / "assets"
        
        # Create V3 generation result
        v3_generation_result = {
            "stub_generation": True,
            "generation_performed": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
            json.dump(v3_generation_result, f)
        
        # Create V3 outputs manifest
        v3_outputs_manifest = {
            "generated_assets": ["output/assets/corrupted_v3_asset.png"],
            "stub_asset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
            json.dump(v3_outputs_manifest, f)
        
        # Create V3 generation trace
        v3_generation_trace = {
            "events": [
                {"event": "output_collection", "status": "pending"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_trace.json", 'w') as f:
            json.dump(v3_generation_trace, f)
        
        # Create corrupted asset file (8 bytes)
        with open(assets_dir / "corrupted_v3_asset.png", 'wb') as f:
            f.write(b'stub')
        
        # Execute audit
        args = type('Args', (), {
            'project_root': str(temp_project_dir),
            'shot_id': 'shot01',
            'json': True
        })()
        
        result = combine_audit_corrective_retry_v3_output_collector(args)
        
        # Load audit report
        with open(control_dir / "combine_v2_corrective_retry_v3_output_collector_audit.json", 'r') as f:
            audit = json.load(f)
        
        assert audit["v3_asset_corrupted"] is True
        assert audit["v3_asset_size_bytes"] == 4
        assert result == 0
    
    def test_audit_findings_include_stub_generation(self, temp_project_dir):
        """Test that audit findings include stub generation detection."""
        control_dir = temp_project_dir / "output" / "control"
        assets_dir = temp_project_dir / "output" / "assets"
        
        # Create V3 generation result
        v3_generation_result = {
            "stub_generation": True,
            "generation_performed": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
            json.dump(v3_generation_result, f)
        
        # Create V3 outputs manifest
        v3_outputs_manifest = {
            "generated_assets": ["output/assets/corrupted_v3_asset.png"],
            "stub_asset": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
            json.dump(v3_outputs_manifest, f)
        
        # Create V3 generation trace
        v3_generation_trace = {
            "events": [
                {"event": "output_collection", "status": "pending"}
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v3_generation_trace.json", 'w') as f:
            json.dump(v3_generation_trace, f)
        
        # Create corrupted asset file
        with open(assets_dir / "corrupted_v3_asset.png", 'wb') as f:
            f.write(b'stub')
        
        # Execute audit
        args = type('Args', (), {
            'project_root': str(temp_project_dir),
            'shot_id': 'shot01',
            'json': True
        })()
        
        result = combine_audit_corrective_retry_v3_output_collector(args)
        
        # Load audit report
        with open(control_dir / "combine_v2_corrective_retry_v3_output_collector_audit.json", 'r') as f:
            audit = json.load(f)
        
        assert "Generation was stubbed - no real ComfyUI execution occurred" in audit["audit_findings"]
        assert result == 0
