"""
Tests for reference set CLI commands.
"""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from datetime import datetime

from app.cli_commands.reference_set import reference_set, create_contract_template
from app.reference_set import DropzoneContract, ReferenceSlot, ValidationPolicy, SlotRole


@pytest.fixture
def runner():
    """Click CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_contract_path(tmp_path):
    """Temporary contract file path."""
    return str(tmp_path / "contract.json")


@pytest.fixture
def sample_contract_data(tmp_path):
    """Sample contract data for testing."""
    return {
        "contract_version": "1.0.0",
        "blueprint_stage_id": "test_blueprint",
        "dropzone_root_path": str(tmp_path / "dropzone"),
        "required_reference_slots": [
            {
                "slot_id": "slot_001",
                "slot_role": "identity_reference",
                "required": True,
                "allowed_formats": ["jpg", "jpeg", "png", "webp"],
                "min_dimensions": None,
                "max_file_size_mb": None
            }
        ],
        "validation_policy": {
            "validate_existence": True,
            "validate_readability": True,
            "validate_sha256": True,
            "validate_size": True,
            "validate_dimensions": True,
            "fail_on_missing_required": True
        },
        "intake_manifest_path": "output/project_agnostic/reference_set/reference_file_intake_manifest.json",
        "created_at": datetime.now().isoformat(),
        "operator_instructions": "Test instructions"
    }


class TestCreateContractTemplate:
    """Test create-contract-template command."""
    
    def test_create_template(self, runner, temp_contract_path):
        """Test creating contract template."""
        result = runner.invoke(reference_set, ['create-contract-template', temp_contract_path])
        assert result.exit_code == 0
        assert "Created contract template" in result.output
        
        # Verify file was created
        contract_path = Path(temp_contract_path)
        assert contract_path.exists()
        
        # Verify template structure
        with open(contract_path) as f:
            data = json.load(f)
        assert "contract_version" in data
        assert "required_reference_slots" in data
        assert "validation_policy" in data


class TestInspectCommand:
    """Test inspect command."""
    
    def test_inspect_contract(self, runner, temp_contract_path, sample_contract_data):
        """Test inspecting a contract."""
        # Create contract file
        with open(temp_contract_path, 'w') as f:
            json.dump(sample_contract_data, f)
        
        result = runner.invoke(reference_set, ['inspect', temp_contract_path])
        assert result.exit_code == 0
        assert "Dropzone Contract" in result.output
        assert "test_blueprint" in result.output
        assert "identity_reference" in result.output


class TestValidateCommand:
    """Test validate command."""
    
    def test_validate_empty_dropzone(self, runner, temp_contract_path, sample_contract_data, tmp_path):
        """Test validating with empty dropzone."""
        # Create contract file
        dropzone_path = tmp_path / "dropzone"
        dropzone_path.mkdir()
        sample_contract_data["dropzone_root_path"] = str(dropzone_path)
        
        with open(temp_contract_path, 'w') as f:
            json.dump(sample_contract_data, f)
        
        output_dir = str(tmp_path / "output")
        result = runner.invoke(reference_set, ['validate', temp_contract_path, 'test_blueprint', '--output-dir', output_dir])
        assert result.exit_code == 0
        assert "Validation Summary" in result.output
        assert "Overall status" in result.output


class TestReadinessReportCommand:
    """Test readiness-report command."""
    
    def test_readiness_report(self, runner, temp_contract_path, sample_contract_data, tmp_path):
        """Test generating readiness report."""
        # Create contract file
        dropzone_path = tmp_path / "dropzone"
        dropzone_path.mkdir()
        sample_contract_data["dropzone_root_path"] = str(dropzone_path)
        
        with open(temp_contract_path, 'w') as f:
            json.dump(sample_contract_data, f)
        
        output_dir = str(tmp_path / "output")
        result = runner.invoke(reference_set, ['readiness-report', temp_contract_path, 'test_blueprint', '--output-dir', output_dir])
        assert result.exit_code == 0
        assert "Readiness Report" in result.output
        assert "Status" in result.output


class TestDropzoneContract:
    """Test DropzoneContract class."""
    
    def test_load_and_save_contract(self, temp_contract_path, sample_contract_data):
        """Test loading and saving contract."""
        # Create contract file
        with open(temp_contract_path, 'w') as f:
            json.dump(sample_contract_data, f)
        
        # Load contract
        contract_manager = DropzoneContract(temp_contract_path)
        contract = contract_manager.load()
        
        assert contract.contract_version == "1.0.0"
        assert contract.blueprint_stage_id == "test_blueprint"
        assert len(contract.required_reference_slots) == 1
        assert contract.required_reference_slots[0].slot_role == SlotRole.IDENTITY_REFERENCE
        
        # Save contract
        contract.blueprint_stage_id = "updated_blueprint"
        contract_manager.save(contract)
        
        # Verify saved data
        with open(temp_contract_path) as f:
            data = json.load(f)
        assert data["blueprint_stage_id"] == "updated_blueprint"
    
    def test_get_dropzone_path(self, temp_contract_path, sample_contract_data):
        """Test getting dropzone path."""
        with open(temp_contract_path, 'w') as f:
            json.dump(sample_contract_data, f)
        
        contract_manager = DropzoneContract(temp_contract_path)
        contract = contract_manager.load()
        dropzone_path = contract_manager.get_dropzone_path()
        
        assert isinstance(dropzone_path, Path)
        assert dropzone_path.name == "dropzone"
