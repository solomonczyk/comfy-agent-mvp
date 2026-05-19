"""
File validator for reference images.

Validates file existence, readability, SHA256 checksum, size, and dimensions.
Does NOT perform visual acceptance or generation.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image

from .models import (
    ValidationPolicy,
    FileValidationResult,
    ValidationCheck,
    ValidationStatus,
    ReferenceSlot
)


class FileValidator:
    """Validates reference files against policy and slot requirements."""
    
    def __init__(self, validation_policy: ValidationPolicy):
        self.validation_policy = validation_policy
    
    def validate_file(
        self,
        file_path: str,
        slot: Optional[ReferenceSlot] = None
    ) -> FileValidationResult:
        """Validate a single reference file."""
        checks: Dict[str, ValidationCheck] = {}
        errors: List[str] = []
        
        # Existence check
        if self.validation_policy.validate_existence:
            existence_check = self._check_existence(file_path)
            checks["existence"] = existence_check
            if not existence_check.passed:
                errors.append(existence_check.message)
                return FileValidationResult(
                    file_path=file_path,
                    checks=checks,
                    overall_valid=False,
                    errors=errors
                )
        
        # Readability check
        if self.validation_policy.validate_readability:
            readability_check = self._check_readability(file_path)
            checks["readability"] = readability_check
            if not readability_check.passed:
                errors.append(readability_check.message)
                return FileValidationResult(
                    file_path=file_path,
                    checks=checks,
                    overall_valid=False,
                    errors=errors
                )
        
        # SHA256 checksum
        if self.validation_policy.validate_sha256:
            sha256_check = self._check_sha256(file_path)
            checks["sha256"] = sha256_check
            if not sha256_check.passed:
                errors.append(sha256_check.message)
        
        # File size
        if self.validation_policy.validate_size:
            size_check = self._check_size(file_path, slot)
            checks["size"] = size_check
            if not size_check.passed:
                errors.append(size_check.message)
        
        # Dimensions
        if self.validation_policy.validate_dimensions:
            dimensions_check = self._check_dimensions(file_path, slot)
            checks["dimensions"] = dimensions_check
            if not dimensions_check.passed:
                errors.append(dimensions_check.message)
        
        overall_valid = all(check.passed for check in checks.values())
        
        return FileValidationResult(
            file_path=file_path,
            checks=checks,
            overall_valid=overall_valid,
            errors=errors
        )
    
    def _check_existence(self, file_path: str) -> ValidationCheck:
        """Check if file exists."""
        path = Path(file_path)
        exists = path.exists() and path.is_file()
        return ValidationCheck(
            passed=exists,
            message="File exists" if exists else "File does not exist"
        )
    
    def _check_readability(self, file_path: str) -> ValidationCheck:
        """Check if file is readable."""
        try:
            path = Path(file_path)
            with open(path, 'rb') as f:
                # Try to read first byte
                f.read(1)
            return ValidationCheck(
                passed=True,
                message="File is readable"
            )
        except Exception as e:
            return ValidationCheck(
                passed=False,
                message=f"File is not readable: {str(e)}"
            )
    
    def _check_sha256(self, file_path: str) -> ValidationCheck:
        """Compute SHA256 checksum."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            checksum = sha256_hash.hexdigest()
            return ValidationCheck(
                passed=True,
                message="SHA256 checksum computed",
                value=checksum
            )
        except Exception as e:
            return ValidationCheck(
                passed=False,
                message=f"Failed to compute SHA256: {str(e)}"
            )
    
    def _check_size(self, file_path: str, slot: Optional[ReferenceSlot] = None) -> ValidationCheck:
        """Check file size against slot requirements."""
        try:
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            
            if slot and slot.max_file_size_mb:
                if size_mb > slot.max_file_size_mb:
                    return ValidationCheck(
                        passed=False,
                        message=f"File size {size_mb:.2f}MB exceeds maximum {slot.max_file_size_mb}MB",
                        value=size_bytes
                    )
            
            return ValidationCheck(
                passed=True,
                message=f"File size {size_mb:.2f}MB",
                value=size_bytes
            )
        except Exception as e:
            return ValidationCheck(
                passed=False,
                message=f"Failed to check file size: {str(e)}"
            )
    
    def _check_dimensions(self, file_path: str, slot: Optional[ReferenceSlot] = None) -> ValidationCheck:
        """Check image dimensions against slot requirements."""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                
                if slot and slot.min_dimensions:
                    min_width = slot.min_dimensions.get("width", 0)
                    min_height = slot.min_dimensions.get("height", 0)
                    
                    if width < min_width or height < min_height:
                        return ValidationCheck(
                            passed=False,
                            message=f"Dimensions {width}x{height} below minimum {min_width}x{min_height}",
                            value={"width": width, "height": height}
                        )
                
                return ValidationCheck(
                    passed=True,
                    message=f"Dimensions {width}x{height}",
                    value={"width": width, "height": height}
                )
        except Exception as e:
            return ValidationCheck(
                passed=False,
                message=f"Failed to check dimensions: {str(e)}"
            )
    
    def determine_validation_status(self, validation_result: FileValidationResult) -> ValidationStatus:
        """Determine overall validation status from check results."""
        checks = validation_result.checks
        
        # Check existence
        if "existence" in checks and not checks["existence"].passed:
            return ValidationStatus.MISSING
        
        # Check readability
        if "readability" in checks and not checks["readability"].passed:
            return ValidationStatus.UNREADABLE
        
        # Check size
        if "size" in checks and not checks["size"].passed:
            return ValidationStatus.SIZE_EXCEEDED
        
        # Check dimensions
        if "dimensions" in checks and not checks["dimensions"].passed:
            return ValidationStatus.DIMENSIONS_INSUFFICIENT
        
        # If all checks passed
        if validation_result.overall_valid:
            return ValidationStatus.VALID
        
        # Default to unreadable if something else failed
        return ValidationStatus.UNREADABLE
