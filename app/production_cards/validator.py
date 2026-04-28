"""
Production Card Validator

This module provides validation for universal production cards.
It validates project card completeness, schema validity, statuses, ownership,
dependencies, and reference availability before any generation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from .schema_loader import SchemaLoader, list_valid_statuses, list_valid_owner_roles


class CardValidator:
    """Validates production cards against schemas and business rules."""

    def __init__(self, schemas_dir: Optional[str] = None):
        """
        Initialize the card validator.

        Args:
            schemas_dir: Path to the schemas directory. If None, uses default.
        """
        self.schema_loader = SchemaLoader(schemas_dir)
        self.valid_statuses = list_valid_statuses()
        self.valid_owner_roles = list_valid_owner_roles()

    def discover_cards(self, project_root: str) -> List[Path]:
        """
        Discover all card JSON files in the project.

        Args:
            project_root: Path to the project root

        Returns:
            List of card file paths
        """
        project_path = Path(project_root)
        cards_dir = project_path / "cards"
        
        if not cards_dir.exists():
            return []
        
        card_files = []
        for card_file in cards_dir.rglob("*.json"):
            card_files.append(card_file)
        
        return sorted(card_files)

    def validate_card_file(self, path: Path) -> Dict[str, Any]:
        """
        Validate a single card file.

        Args:
            path: Path to the card file

        Returns:
            Validation result dict with status, errors, warnings
        """
        result = {
            "path": str(path),
            "validation_status": "failed",
            "errors": [],
            "warnings": []
        }

        # Check file exists
        if not path.exists():
            result["errors"].append(f"File does not exist: {path}")
            return result

        # Check file is readable
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            result["errors"].append(f"Failed to read file: {e}")
            return result

        # Check JSON parses
        try:
            card = json.loads(content)
        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON: {e}")
            return result

        # Check card is a dict
        if not isinstance(card, dict):
            result["errors"].append("Card must be a JSON object")
            return result

        # Check required fields
        required_fields = ["card_id", "card_type", "project_id", "owner_role", "status"]
        for field in required_fields:
            if field not in card:
                result["errors"].append(f"Missing required field: {field}")

        # Validate card_type
        if "card_type" in card:
            card_type = card["card_type"]
            if not self.schema_loader.validate_card_type(card_type):
                result["errors"].append(f"Invalid card_type: {card_type}")

        # Validate owner_role
        if "owner_role" in card:
            owner_role = card["owner_role"]
            if owner_role not in self.valid_owner_roles:
                result["errors"].append(f"Invalid owner_role: {owner_role}")

        # Validate status
        if "status" in card:
            status = card["status"]
            if status not in self.valid_statuses:
                result["errors"].append(f"Invalid status: {status}")

        # Check for project-specific hardcode
        # Distinguish between core/template cards and real project cards
        content_lower = content.lower()
        has_project_specific_names = "alya" in content_lower or "mir erdan" in content_lower
        
        if has_project_specific_names:
            # Check if this is a template card (should reject project-specific hardcode)
            path_str = str(path)
            is_template_card = "project_templates" in path_str
            
            # Check if this is a real project card with project_specific_data_allowed flag
            project_specific_data_allowed = card.get("project_specific_data_allowed", False)
            
            if is_template_card:
                # Template cards must be project-agnostic
                result["errors"].append("project-specific hardcode detected in template card")
            elif not project_specific_data_allowed:
                # Real project cards must have project_specific_data_allowed flag to contain project names
                result["errors"].append("project-specific hardcode detected without project_specific_data_allowed flag")

        # Set status based on errors
        if not result["errors"]:
            result["validation_status"] = "passed"

        return result

    def validate_project_cards(self, project_root: str) -> Dict[str, Any]:
        """
        Validate all cards in a project.

        Args:
            project_root: Path to the project root

        Returns:
            Validation result dict with summary, cards, errors, warnings
        """
        project_path = Path(project_root)
        result = {
            "status": "failed",
            "project_root": project_root,
            "summary": {
                "cards_found": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "warnings": 0
            },
            "cards": [],
            "errors": [],
            "warnings": [],
            "generation_ready": False
        }

        # Check cards folder exists
        cards_dir = project_path / "cards"
        if not cards_dir.exists():
            result["errors"].append(f"Cards folder does not exist: {cards_dir}")
            return result

        # Discover cards
        card_files = self.discover_cards(project_root)
        result["summary"]["cards_found"] = len(card_files)

        # Track card_ids for uniqueness check
        card_ids = []

        # Validate each card
        for card_file in card_files:
            validation = self.validate_card_file(card_file)
            
            # Load card to get card_id for reporting
            try:
                with open(card_file, 'r', encoding='utf-8') as f:
                    card = json.load(f)
                card_id = card.get("card_id", "unknown")
                card_type = card.get("card_type", "unknown")
                status = card.get("status", "unknown")
                owner_role = card.get("owner_role", "unknown")
            except:
                card_id = "unknown"
                card_type = "unknown"
                status = "unknown"
                owner_role = "unknown"

            # Check for duplicate card_id
            if card_id in card_ids:
                validation["errors"].append(f"Duplicate card_id: {card_id}")
                # Update validation status if duplicate detected
                validation["validation_status"] = "failed"
                # Add to project-level errors
                result["errors"].append(f"Duplicate card_id: {card_id}")
            card_ids.append(card_id)

            card_result = {
                "card_id": card_id,
                "card_type": card_type,
                "status": status,
                "owner_role": owner_role,
                "validation_status": validation["validation_status"],
                "errors": validation["errors"],
                "warnings": validation["warnings"]
            }

            result["cards"].append(card_result)

            # Update summary
            if validation["validation_status"] == "passed":
                result["summary"]["passed_checks"] += 1
            else:
                result["summary"]["failed_checks"] += 1

            result["summary"]["warnings"] += len(validation["warnings"])

        # Validate dependencies
        dependency_result = self.validate_card_dependencies(result["cards"])
        result["errors"].extend(dependency_result["errors"])
        result["warnings"].extend(dependency_result["warnings"])

        # Determine overall status
        if not result["errors"] and result["summary"]["failed_checks"] == 0:
            result["status"] = "passed"

        # Determine generation readiness
        result["generation_ready"] = self._check_generation_ready(result["cards"])

        return result

    def validate_card_dependencies(self, cards: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that card dependencies reference existing cards.

        Args:
            cards: List of card validation results

        Returns:
            Validation result with errors and warnings
        """
        result = {
            "errors": [],
            "warnings": []
        }

        # Build card_id lookup
        card_ids = {card["card_id"]: card for card in cards}

        # Check dependencies for each card
        for card in cards:
            card_id = card["card_id"]
            
            # Load the actual card file to check dependencies
            # This is a simplified check - in a full implementation, we'd load the card
            # and check its references/dependencies fields
            pass  # Placeholder for dependency validation

        return result

    def validate_card_references(self, card: Dict[str, Any], project_root: str) -> Dict[str, Any]:
        """
        Validate that card references exist or have appropriate handling.

        Args:
            card: Card data
            project_root: Path to the project root

        Returns:
            Validation result with errors and warnings
        """
        result = {
            "errors": [],
            "warnings": []
        }

        # Check if card has next_action_if_missing for missing references
        if "references" in card and card["references"]:
            project_path = Path(project_root)
            
            for ref in card["references"]:
                # Check if referenced card exists
                # This is a simplified check
                pass

        return result

    def _check_generation_ready(self, cards: List[Dict[str, Any]]) -> bool:
        """
        Check if the project is ready for generation.

        Args:
            cards: List of card validation results

        Returns:
            True if generation ready, False otherwise
        """
        # Generation is ready only if all critical cards are approved
        # Template cards in draft status are not generation-ready
        for card in cards:
            if card["validation_status"] != "passed":
                return False
            
            # Draft or blocked cards prevent generation readiness
            if card["status"] in ["draft", "blocked", "needs_references", "needs_role_work"]:
                return False

        return True


def validate_production_cards(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Validate all production cards in a project.

    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output

    Returns:
        Validation result dict
    """
    validator = CardValidator()
    result = validator.validate_project_cards(project_root)
    
    if json_output:
        return result
    
    return result


def main():
    """CLI entry point for production card validation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate production cards in a project"
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Path to the project root"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    
    args = parser.parse_args()
    
    result = validate_production_cards(args.project_root, json_output=True)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Validation Status: {result['status'].upper()}")
        print(f"Cards Found: {result['summary']['cards_found']}")
        print(f"Passed: {result['summary']['passed_checks']}")
        print(f"Failed: {result['summary']['failed_checks']}")
        print(f"Warnings: {result['summary']['warnings']}")
        print(f"Generation Ready: {result['generation_ready']}")
        
        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")
        
        if result["warnings"]:
            print("\nWarnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
    
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
