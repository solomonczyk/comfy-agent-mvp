"""
Slot mapper for matching reference files to blueprint slots.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from .models import (
    ReferenceSlot,
    SlotMapping,
    SlotRole,
    FillStatus,
    MappingConfidence,
    ReferenceFileEntry,
    SlotMappingSummary,
    ReadinessStatus
)


class SlotMapper:
    """Maps discovered reference files to blueprint slots."""
    
    # Role name patterns for filename matching
    ROLE_PATTERNS = {
        SlotRole.IDENTITY_REFERENCE: ["identity", "id", "subject", "character"],
        SlotRole.STYLE_REFERENCE: ["style", "aesthetic", "look", "mood"],
        SlotRole.CAMERA_REFERENCE: ["camera", "angle", "view", "perspective"],
        SlotRole.LIGHTING_REFERENCE: ["lighting", "light", "illumination"],
        SlotRole.ANATOMY_REFERENCE: ["anatomy", "body", "pose", "structure"],
        SlotRole.QUALITY_REFERENCE: ["quality", "reference", "standard"],
        SlotRole.NEGATIVE_REFERENCE: ["negative", "avoid", "not"]
    }
    
    def __init__(self, slots: List[ReferenceSlot]):
        self.slots = slots
        self.slot_by_id = {slot.slot_id: slot for slot in slots}
    
    def map_files_to_slots(
        self,
        file_entries: List[ReferenceFileEntry]
    ) -> Tuple[List[SlotMapping], List[str], List[str]]:
        """
        Map files to slots based on filename patterns.
        
        Returns:
            (slot_mappings, unmapped_files, unfilled_slots)
        """
        slot_mappings: List[SlotMapping] = []
        unmapped_files: List[str] = []
        used_files = set()
        
        # First pass: exact matches by filename
        for slot in self.slots:
            matched_files = self._find_exact_matches(slot, file_entries)
            if matched_files:
                for file_path in matched_files:
                    if file_path not in used_files:
                        used_files.add(file_path)
            
            if matched_files:
                slot_mappings.append(SlotMapping(
                    slot_id=slot.slot_id,
                    slot_role=slot.slot_role,
                    required=slot.required,
                    assigned_files=matched_files,
                    fill_status=FillStatus.FILLED,
                    mapping_confidence=MappingConfidence.EXACT_MATCH
                ))
            else:
                slot_mappings.append(SlotMapping(
                    slot_id=slot.slot_id,
                    slot_role=slot.slot_role,
                    required=slot.required,
                    assigned_files=[],
                    fill_status=FillStatus.EMPTY,
                    mapping_confidence=MappingConfidence.NONE
                ))
        
        # Second pass: pattern matching for empty slots
        for mapping in slot_mappings:
            if mapping.fill_status == FillStatus.EMPTY:
                slot = self.slot_by_id[mapping.slot_id]
                pattern_matches = self._find_pattern_matches(slot, file_entries, used_files)
                
                if pattern_matches:
                    for file_path in pattern_matches:
                        used_files.add(file_path)
                    
                    mapping.assigned_files = pattern_matches
                    mapping.fill_status = FillStatus.FILLED
                    mapping.mapping_confidence = MappingConfidence.ROLE_INFERENCE
        
        # Find unmapped files
        for entry in file_entries:
            if entry.file_path not in used_files:
                unmapped_files.append(entry.file_path)
        
        # Find unfilled required slots
        unfilled_slots = [
            mapping.slot_id
            for mapping in slot_mappings
            if mapping.required and mapping.fill_status == FillStatus.EMPTY
        ]
        
        return slot_mappings, unmapped_files, unfilled_slots
    
    def _find_exact_matches(
        self,
        slot: ReferenceSlot,
        file_entries: List[ReferenceFileEntry]
    ) -> List[str]:
        """Find files that exactly match the slot role in filename."""
        role_name = slot.slot_role.value.replace("_", " ")
        role_snake = slot.slot_role.value
        
        matches = []
        for entry in file_entries:
            filename_lower = entry.file_name.lower()
            
            # Check for exact role name match
            if role_snake in filename_lower or role_name in filename_lower:
                matches.append(entry.file_path)
        
        return matches
    
    def _find_pattern_matches(
        self,
        slot: ReferenceSlot,
        file_entries: List[ReferenceFileEntry],
        used_files: set
    ) -> List[str]:
        """Find files matching role patterns."""
        patterns = self.ROLE_PATTERNS.get(slot.slot_role, [])
        matches = []
        
        for entry in file_entries:
            if entry.file_path in used_files:
                continue
            
            filename_lower = entry.file_name.lower()
            
            for pattern in patterns:
                if pattern in filename_lower:
                    matches.append(entry.file_path)
                    break
        
        return matches
    
    def compute_mapping_summary(
        self,
        slot_mappings: List[SlotMapping],
        unfilled_slots: List[str]
    ) -> SlotMappingSummary:
        """Compute summary of slot mapping."""
        total_slots = len(slot_mappings)
        filled_slots = sum(
            1 for m in slot_mappings
            if m.fill_status != FillStatus.EMPTY
        )
        
        # Determine readiness status
        if unfilled_slots:
            readiness_status = ReadinessStatus.BLOCKED_MISSING_REQUIRED_REFERENCE
        elif filled_slots < total_slots:
            readiness_status = ReadinessStatus.PENDING_OPERATOR_SUPPLY
        else:
            readiness_status = ReadinessStatus.READY
        
        return SlotMappingSummary(
            total_slots=total_slots,
            filled_slots=filled_slots,
            missing_required_slots=unfilled_slots,
            readiness_status=readiness_status
        )
