"""MK-REF1R-2 — Reference resolver for character identity references."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class ReferenceResolver:
    """Resolves character references from project reference root.

    MK-REF1R-2 — Uses existing approved project references as identity source.
    Never generates new references.
    """

    def __init__(
        self,
        project_root: Path | str,
        reference_root: Path | str | None = None,
    ):
        """Initialize reference resolver.

        Args:
            project_root: Project source root
            reference_root: Optional reference root (defaults to project_root/references)
        """
        self.project_root = Path(project_root).resolve()
        if reference_root is None:
            self.reference_root = self.project_root / "референсы"
        else:
            self.reference_root = Path(reference_root).resolve()

        # RC-CORE1 — No hardcoded character aliases
        # Character resolution is now done via project_profile.json

    def resolve_character_reference(self, character_name: str) -> dict | None:
        """Resolve character reference from reference root.

        Args:
            character_name: Character name to resolve (e.g., "Alya", "Аля")

        Returns:
            Reference dict with character_name, aliases, reference_image_path,
            source, reference_role, lock_strength, or None if not found.

        MK-REF1R-2 — Returns existing file only, never generates new reference.
        """
        # Normalize character name for lookup
        normalized_name = character_name.strip()
        aliases = self._get_aliases(normalized_name)

        # Scan reference root for matching files
        if not self.reference_root.exists():
            return None

        valid_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        candidate_files = []

        for file_path in self.reference_root.iterdir():
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in valid_extensions:
                continue

            # Check filename against aliases
            filename_lower = file_path.stem.lower()
            for alias in aliases:
                alias_lower = alias.lower()
                if alias_lower in filename_lower or filename_lower == alias_lower:
                    candidate_files.append(file_path)
                    break

        # Prioritize exact matches
        exact_matches = []
        for file_path in candidate_files:
            filename_lower = file_path.stem.lower()
            for alias in aliases:
                alias_lower = alias.lower()
                if filename_lower == alias_lower:
                    exact_matches.append(file_path)
                    break

        # Use exact match if available, otherwise first partial match
        if exact_matches:
            selected_file = exact_matches[0]
        elif candidate_files:
            selected_file = candidate_files[0]
        else:
            return None

        # Verify file exists and is readable
        if not selected_file.exists():
            return None

        # Return reference dict
        return {
            "character_name": character_name,
            "aliases": aliases,
            "reference_image_path": str(selected_file),
            "source": "reference_root",
            "reference_role": "character_identity",
            "lock_strength": 0.65,
        }

    def _get_aliases(self, character_name: str) -> list[str]:
        """Get aliases for character name.

        RC-CORE1 — Returns the character name itself as the only alias.
        Character aliases are now managed via project_profile.json.

        Args:
            character_name: Character name

        Returns:
            List of alias strings
        """
        # RC-CORE1 — No hardcoded character aliases
        # Return the name itself as only alias
        return [character_name]

    def scan_reference_root(self) -> list[dict]:
        """Scan reference root for all image files.

        Returns:
            List of file info dicts with path, size, modification_time

        MK-REF1R-2 — Returns discovered files for verification.
        """
        if not self.reference_root.exists():
            return []

        valid_extensions = {".png", ".jpg", ".jpeg", ".webp"}
        files = []

        for file_path in self.reference_root.iterdir():
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in valid_extensions:
                continue

            files.append({
                "path": str(file_path),
                "name": file_path.name,
                "extension": file_path.suffix.lower(),
                "size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime,
            })

        return sorted(files, key=lambda x: x["name"])
