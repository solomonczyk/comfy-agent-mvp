"""
Tests for Knowledge Gate.
"""

import pytest
import json
from pathlib import Path

from app.kb.gate import KnowledgeGate
from app.kb.models import (
    GateDecision,
    ReferenceLockContract,
    KBReadinessReport,
)


class TestKnowledgeGate:
    """Test KnowledgeGate functionality."""
    
    @pytest.fixture
    def gate(self, tmp_path):
        """Create a gate with temp output dir."""
        return KnowledgeGate(base_output_dir=str(tmp_path))
    
    @pytest.fixture
    def project_dir(self, tmp_path):
        """Create a project directory structure."""
        project_dir = tmp_path / "test_project" / "output" / "control"
        project_dir.mkdir(parents=True)
        return project_dir
    
    def test_knowledge_gate_denies_generation_when_project_manifest_missing(self, gate, tmp_path):
        """Test that KnowledgeGate denies generation when project_manifest missing."""
        project_root = tmp_path / "test_project" / "output" / "control"
        
        decision = gate.can_generate(project_root)
        
        assert decision.allowed is False
        assert "project_manifest.json" in decision.reason or "Missing required artifacts" in decision.reason
    
    def test_knowledge_gate_denies_generation_when_reference_lock_contract_missing(self, gate, project_dir):
        """Test that KnowledgeGate denies generation when reference_lock_contract missing."""
        # Create project_manifest but not reference_lock
        (project_dir / "project_manifest.json").write_text('{"project_id": "test"}')
        (project_dir / "series_bible.json").write_text('{"title": "test"}')
        (project_dir / "character_registry.json").write_text('{"characters": []}')
        (project_dir / "style_bible.json").write_text('{}')
        (project_dir / "kb_readiness_report.json").write_text('{"kb_ready": false}')
        
        decision = gate.can_generate(project_dir)
        
        assert decision.allowed is False
        assert "reference_lock_contract" in decision.reason.lower()
    
    def test_knowledge_gate_denies_generation_when_downstream_generation_allowed_false(self, gate, project_dir):
        """Test that KnowledgeGate denies generation when downstream_generation_allowed=false."""
        # Create reference lock with downstream_generation_allowed=false
        reference_lock = ReferenceLockContract(
            downstream_generation_allowed=False,
            lock_reason="test lock",
        )
        (project_dir / "reference_lock_contract.json").write_text(
            json.dumps(reference_lock.to_dict())
        )
        
        # Create other required artifacts
        (project_dir / "project_manifest.json").write_text('{"project_id": "test"}')
        (project_dir / "series_bible.json").write_text('{"title": "test"}')
        (project_dir / "character_registry.json").write_text('{"characters": []}')
        (project_dir / "style_bible.json").write_text('{}')
        
        readiness_report = KBReadinessReport(
            kb_ready=False,
            ready_for_generation=False,
        )
        (project_dir / "kb_readiness_report.json").write_text(
            json.dumps(readiness_report.to_dict())
        )
        
        decision = gate.can_generate(project_dir)
        
        assert decision.allowed is False
        assert "not approved" in decision.reason.lower()
    
    def test_knowledge_gate_allows_generation_only_when_all_required_artifacts_exist_and_downstream_generation_allowed_true(
        self, gate, project_dir
    ):
        """Test that KnowledgeGate allows generation only when all required artifacts exist and downstream_generation_allowed=true."""
        # Create all required artifacts with approval
        reference_lock = ReferenceLockContract(
            downstream_generation_allowed=True,
            lock_reason="",
        )
        (project_dir / "reference_lock_contract.json").write_text(
            json.dumps(reference_lock.to_dict())
        )
        
        (project_dir / "project_manifest.json").write_text('{"project_id": "test"}')
        (project_dir / "series_bible.json").write_text('{"title": "test"}')
        (project_dir / "character_registry.json").write_text('{"characters": []}')
        (project_dir / "style_bible.json").write_text('{}')
        
        readiness_report = KBReadinessReport(
            kb_ready=True,
            ready_for_generation=True,
        )
        (project_dir / "kb_readiness_report.json").write_text(
            json.dumps(readiness_report.to_dict())
        )
        
        decision = gate.can_generate(project_dir)
        
        assert decision.allowed is True
        assert "approved" in decision.reason.lower() or "ready" in decision.reason.lower()
    
    def test_gate_decision_denied_json_format(self, gate, project_dir):
        """Test that denied GateDecision JSON format is correct."""
        (project_dir / "project_manifest.json").write_text('{"project_id": "test"}')
        
        decision = gate.can_generate(project_dir)
        
        decision_dict = decision.to_dict()
        assert decision_dict["allowed"] is False
        assert "reason" in decision_dict
        assert "missing_artifacts" in decision_dict
    
    def test_gate_decision_allowed_json_format(self, gate, project_dir):
        """Test that allowed GateDecision JSON format is correct."""
        # Create all required artifacts with approval
        reference_lock = ReferenceLockContract(
            downstream_generation_allowed=True,
        )
        (project_dir / "reference_lock_contract.json").write_text(
            json.dumps(reference_lock.to_dict())
        )
        
        (project_dir / "project_manifest.json").write_text('{"project_id": "test"}')
        (project_dir / "series_bible.json").write_text('{"title": "test"}')
        (project_dir / "character_registry.json").write_text('{"characters": []}')
        (project_dir / "style_bible.json").write_text('{}')
        
        readiness_report = KBReadinessReport(
            kb_ready=True,
            ready_for_generation=True,
        )
        (project_dir / "kb_readiness_report.json").write_text(
            json.dumps(readiness_report.to_dict())
        )
        
        decision = gate.can_generate(project_dir)
        
        decision_dict = decision.to_dict()
        assert decision_dict["allowed"] is True
        assert "reason" in decision_dict
