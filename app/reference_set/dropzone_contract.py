"""
Dropzone contract manager for reference set.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .models import (
    DropzoneContract,
    ReferenceSlot,
    ValidationPolicy,
    SlotRole
)


class DropzoneContract:
    """Manages dropzone contract for reference set."""
    
    def __init__(self, contract_path: str):
        self.contract_path = Path(contract_path)
        self.contract: Optional[DropzoneContract] = None
    
    def load(self) -> DropzoneContract:
        """Load contract from file."""
        with open(self.contract_path, 'r') as f:
            data = json.load(f)
        
        self.contract = self._deserialize(data)
        return self.contract
    
    def save(self, contract: DropzoneContract) -> None:
        """Save contract to file."""
        self.contract = contract
        data = self._serialize(contract)
        
        self.contract_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.contract_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _deserialize(self, data: Dict[str, Any]) -> DropzoneContract:
        """Deserialize contract data."""
        slots = [
            ReferenceSlot(
                slot_id=s["slot_id"],
                slot_role=SlotRole(s["slot_role"]),
                required=s["required"],
                allowed_formats=s.get("allowed_formats", ["jpg", "jpeg", "png", "webp"]),
                min_dimensions=s.get("min_dimensions"),
                max_file_size_mb=s.get("max_file_size_mb")
            )
            for s in data["required_reference_slots"]
        ]
        
        validation_policy = ValidationPolicy(**data["validation_policy"])
        
        return DropzoneContract(
            contract_version=data["contract_version"],
            blueprint_stage_id=data["blueprint_stage_id"],
            dropzone_root_path=data["dropzone_root_path"],
            required_reference_slots=slots,
            validation_policy=validation_policy,
            intake_manifest_path=data["intake_manifest_path"],
            created_at=datetime.fromisoformat(data["created_at"]),
            operator_instructions=data.get("operator_instructions")
        )
    
    def _serialize(self, contract: DropzoneContract) -> Dict[str, Any]:
        """Serialize contract to dict."""
        return {
            "contract_version": contract.contract_version,
            "blueprint_stage_id": contract.blueprint_stage_id,
            "dropzone_root_path": contract.dropzone_root_path,
            "required_reference_slots": [
                {
                    "slot_id": s.slot_id,
                    "slot_role": s.slot_role.value,
                    "required": s.required,
                    "allowed_formats": s.allowed_formats,
                    "min_dimensions": s.min_dimensions,
                    "max_file_size_mb": s.max_file_size_mb
                }
                for s in contract.required_reference_slots
            ],
            "validation_policy": {
                "validate_existence": contract.validation_policy.validate_existence,
                "validate_readability": contract.validation_policy.validate_readability,
                "validate_sha256": contract.validation_policy.validate_sha256,
                "validate_size": contract.validation_policy.validate_size,
                "validate_dimensions": contract.validation_policy.validate_dimensions,
                "fail_on_missing_required": contract.validation_policy.fail_on_missing_required
            },
            "intake_manifest_path": contract.intake_manifest_path,
            "created_at": contract.created_at.isoformat(),
            "operator_instructions": contract.operator_instructions
        }
    
    def get_dropzone_path(self) -> Path:
        """Get the dropzone root path as Path object."""
        if not self.contract:
            self.load()
        return Path(self.contract.dropzone_root_path)
