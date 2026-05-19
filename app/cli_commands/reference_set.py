"""
CLI commands for reference set dropzone/intake bridge.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from app.reference_set import (
    DropzoneContract,
    IntakeManifestBuilder,
    SlotMapper,
    FileValidator,
    ArtifactWriter
)
from app.reference_set.models import (
    ReferenceSlot,
    ValidationPolicy,
    SlotRole
)


@click.group()
def reference_set():
    """Reference set dropzone/intake bridge commands."""
    pass


@reference_set.command()
@click.argument('contract_path', type=click.Path())
@click.argument('blueprint_stage_id')
@click.option('--output-dir', type=click.Path(), default='output', help='Output directory for artifacts')
def validate(contract_path: str, blueprint_stage_id: str, output_dir: str):
    """Validate reference set against contract."""
    click.echo(f"Validating reference set for {blueprint_stage_id}")
    
    # Load contract
    contract_manager = DropzoneContract(contract_path)
    contract = contract_manager.load()
    
    # Initialize components
    validator = FileValidator(contract.validation_policy)
    slot_mapper = SlotMapper(contract.required_reference_slots)
    dropzone_path = contract_manager.get_dropzone_path()
    
    # Build manifest
    manifest_builder = IntakeManifestBuilder(dropzone_path, validator, slot_mapper)
    manifest = manifest_builder.build_manifest(blueprint_stage_id)
    
    # Write artifacts
    artifact_writer = ArtifactWriter(Path(output_dir))
    artifact_writer.write_dropzone_contract(contract)
    artifact_writer.write_intake_manifest(manifest)
    
    # Get validation results
    file_validations = []
    for entry in manifest.reference_files:
        validation_result = validator.validate_file(entry.file_path)
        file_validations.append(validation_result)
    
    # Determine overall status
    if not file_validations:
        overall_status = "no_files"
    elif all(v.overall_valid for v in file_validations):
        overall_status = "all_valid"
    elif any(v.overall_valid for v in file_validations):
        overall_status = "some_invalid"
    else:
        overall_status = "all_invalid"
    
    # Write validation report
    artifact_writer.write_validation_report(
        blueprint_stage_id,
        contract.validation_policy,
        file_validations,
        overall_status
    )
    
    # Write slot mapping report
    slot_mappings, unmapped_files, unfilled_slots = slot_mapper.map_files_to_slots(manifest.reference_files)
    artifact_writer.write_slot_mapping_report(
        blueprint_stage_id,
        slot_mappings,
        unmapped_files,
        unfilled_slots
    )
    
    # Print summary
    click.echo(f"\nValidation Summary:")
    click.echo(f"  Total files: {len(manifest.reference_files)}")
    click.echo(f"  Valid files: {sum(1 for v in file_validations if v.overall_valid)}")
    click.echo(f"  Invalid files: {sum(1 for v in file_validations if not v.overall_valid)}")
    click.echo(f"  Overall status: {overall_status}")
    click.echo(f"  Readiness: {manifest.slot_mapping_summary.readiness_status.value}")
    click.echo(f"  Filled slots: {manifest.slot_mapping_summary.filled_slots}/{manifest.slot_mapping_summary.total_slots}")
    
    if manifest.slot_mapping_summary.missing_required_slots:
        click.echo(f"  Missing required slots: {', '.join(manifest.slot_mapping_summary.missing_required_slots)}")


@reference_set.command()
@click.argument('contract_path', type=click.Path())
def inspect(contract_path: str):
    """Inspect dropzone contract."""
    contract_manager = DropzoneContract(contract_path)
    contract = contract_manager.load()
    
    click.echo(f"\nDropzone Contract:")
    click.echo(f"  Version: {contract.contract_version}")
    click.echo(f"  Blueprint Stage ID: {contract.blueprint_stage_id}")
    click.echo(f"  Dropzone Path: {contract.dropzone_root_path}")
    click.echo(f"  Created: {contract.created_at}")
    click.echo(f"\nRequired Reference Slots ({len(contract.required_reference_slots)}):")
    
    for slot in contract.required_reference_slots:
        required = "[REQUIRED]" if slot.required else "[OPTIONAL]"
        click.echo(f"  - {slot.slot_id}: {slot.slot_role.value} {required}")
        if slot.min_dimensions:
            click.echo(f"    Min dimensions: {slot.min_dimensions}")
        if slot.max_file_size_mb:
            click.echo(f"    Max file size: {slot.max_file_size_mb}MB")
    
    click.echo(f"\nValidation Policy:")
    click.echo(f"  Existence: {contract.validation_policy.validate_existence}")
    click.echo(f"  Readability: {contract.validation_policy.validate_readability}")
    click.echo(f"  SHA256: {contract.validation_policy.validate_sha256}")
    click.echo(f"  Size: {contract.validation_policy.validate_size}")
    click.echo(f"  Dimensions: {contract.validation_policy.validate_dimensions}")
    click.echo(f"  Fail on missing required: {contract.validation_policy.fail_on_missing_required}")
    
    if contract.operator_instructions:
        click.echo(f"\nOperator Instructions:")
        click.echo(f"  {contract.operator_instructions}")


@reference_set.command()
@click.argument('contract_path', type=click.Path())
@click.argument('blueprint_stage_id')
@click.option('--output-dir', type=click.Path(), default='output', help='Output directory for artifacts')
def readiness_report(contract_path: str, blueprint_stage_id: str, output_dir: str):
    """Generate readiness report for reference set."""
    click.echo(f"Generating readiness report for {blueprint_stage_id}")
    
    # Load contract
    contract_manager = DropzoneContract(contract_path)
    contract = contract_manager.load()
    
    # Initialize components
    validator = FileValidator(contract.validation_policy)
    slot_mapper = SlotMapper(contract.required_reference_slots)
    dropzone_path = contract_manager.get_dropzone_path()
    
    # Build manifest
    manifest_builder = IntakeManifestBuilder(dropzone_path, validator, slot_mapper)
    manifest = manifest_builder.build_manifest(blueprint_stage_id)
    
    # Write artifacts
    artifact_writer = ArtifactWriter(Path(output_dir))
    artifact_writer.write_intake_manifest(manifest)
    
    # Print readiness report
    click.echo(f"\nReadiness Report:")
    click.echo(f"  Blueprint Stage ID: {blueprint_stage_id}")
    click.echo(f"  Status: {manifest.slot_mapping_summary.readiness_status.value}")
    click.echo(f"  Slots filled: {manifest.slot_mapping_summary.filled_slots}/{manifest.slot_mapping_summary.total_slots}")
    
    if manifest.slot_mapping_summary.missing_required_slots:
        click.echo(f"  Missing required slots:")
        for slot_id in manifest.slot_mapping_summary.missing_required_slots:
            click.echo(f"    - {slot_id}")
    
    if manifest.reference_files:
        click.echo(f"\nReference Files:")
        for entry in manifest.reference_files:
            status_icon = "✓" if entry.validation_status.value == "valid" else "✗"
            click.echo(f"  {status_icon} {entry.file_name}")
            click.echo(f"    Status: {entry.validation_status.value}")
            click.echo(f"    Slot: {entry.assigned_slot_id or 'unmapped'}")
            if entry.image_dimensions:
                click.echo(f"    Dimensions: {entry.image_dimensions['width']}x{entry.image_dimensions['height']}")
            click.echo(f"    Size: {entry.file_size_bytes / 1024:.2f}KB")
    else:
        click.echo(f"\nNo reference files found in dropzone")


@reference_set.command()
@click.argument('contract_path', type=click.Path())
def create_contract_template(contract_path: str):
    """Create a new dropzone contract from template."""
    from datetime import datetime
    
    template = {
        "contract_version": "1.0.0",
        "blueprint_stage_id": "",
        "dropzone_root_path": "data/reference_set/{blueprint_stage_id}",
        "required_reference_slots": [],
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
        "operator_instructions": "Place reference images in the dropzone directory. Files should be named according to their slot role (e.g., identity_reference.jpg, style_reference.png)."
    }
    
    Path(contract_path).parent.mkdir(parents=True, exist_ok=True)
    with open(contract_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    click.echo(f"Created contract template at {contract_path}")
    click.echo(f"Edit the file to fill in blueprint_stage_id and required_reference_slots")


if __name__ == '__main__':
    reference_set()
