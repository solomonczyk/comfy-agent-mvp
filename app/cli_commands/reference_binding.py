"""CLI commands for reference binding validation, inspection, and readiness reporting."""

import json
from pathlib import Path

import click

from app.reference_binding.binding_engine import ReferenceBindingEngine
from app.reference_binding.models import (
    ReferenceBinding,
    ReferenceReadiness,
    ReferenceRole,
    SlotRequirement,
)


@click.group()
def reference_binding():
    """Reference binding CLI commands."""
    pass


@reference_binding.command()
@click.argument("binding_file", type=click.Path(exists=True))
def validate(binding_file: str):
    """Validate a reference binding file."""
    binding_path = Path(binding_file)
    with binding_path.open() as f:
        binding_data = json.load(f)

    binding = ReferenceBinding.from_dict(binding_data)
    errors = ReferenceBindingEngine.validate_binding(binding)

    if errors:
        click.echo("Validation FAILED:")
        for error in errors:
            click.echo(f"  - {error}")
        raise click.ClickException("Validation failed")
    else:
        click.echo("Validation PASSED: Reference binding is valid.")


@reference_binding.command()
@click.argument("binding_file", type=click.Path(exists=True))
def inspect(binding_file: str):
    """Inspect a reference binding and display detailed information."""
    binding_path = Path(binding_file)
    with binding_path.open() as f:
        binding_data = json.load(f)

    binding = ReferenceBinding.from_dict(binding_data)
    inspection = ReferenceBindingEngine.inspect_binding(binding)

    click.echo(json.dumps(inspection, indent=2))


@reference_binding.command()
@click.argument("binding_file", type=click.Path(exists=True))
@click.argument("available_slots_file", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), help="Output file for readiness report")
def readiness_report(binding_file: str, available_slots_file: str, output: str | None = None):
    """Generate a readiness report for a reference binding."""
    binding_path = Path(binding_file)
    with binding_path.open() as f:
        binding_data = json.load(f)

    slots_path = Path(available_slots_file)
    with slots_path.open() as f:
        available_slots = json.load(f)

    binding = ReferenceBinding.from_dict(binding_data)
    readiness = ReferenceBindingEngine.calculate_readiness(binding, available_slots)

    readiness_dict = readiness.to_dict()

    if output:
        output_path = Path(output)
        with output_path.open("w") as f:
            json.dump(readiness_dict, f, indent=2)
        click.echo(f"Readiness report written to {output}")
    else:
        click.echo(json.dumps(readiness_dict, indent=2))


@reference_binding.command()
@click.argument("binding_file", type=click.Path(exists=True))
@click.argument("stage_id")
def get_required_slots(binding_file: str, stage_id: str):
    """Get required reference slots for a specific stage."""
    binding_path = Path(binding_file)
    with binding_path.open() as f:
        binding_data = json.load(f)

    binding = ReferenceBinding.from_dict(binding_data)
    required_slots = ReferenceBindingEngine.get_required_slots_for_stage(binding, stage_id)

    click.echo(f"Required slots for stage {stage_id}:")
    for slot in required_slots:
        click.echo(f"  - {slot.slot_id} ({slot.slot_role.value})")


@reference_binding.command()
@click.argument("binding_file", type=click.Path(exists=True))
@click.argument("stage_id")
def get_optional_slots(binding_file: str, stage_id: str):
    """Get optional reference slots for a specific stage."""
    binding_path = Path(binding_file)
    with binding_path.open() as f:
        binding_data = json.load(f)

    binding = ReferenceBinding.from_dict(binding_data)
    optional_slots = ReferenceBindingEngine.get_optional_slots_for_stage(binding, stage_id)

    click.echo(f"Optional slots for stage {stage_id}:")
    for slot in optional_slots:
        click.echo(f"  - {slot.slot_id} ({slot.slot_role.value})")


if __name__ == "__main__":
    reference_binding()
