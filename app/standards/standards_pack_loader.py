"""Standards Pack Loader — loads all JSON artifacts from the standards pack."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class StandardsPackLoader:
    """Loads the standards pack directory structure into memory."""

    def __init__(self, standards_pack_dir: str | Path) -> None:
        self.standards_pack_dir = Path(standards_pack_dir)
        self.manifest: Dict[str, Any] = {}
        self.artifacts: Dict[str, Any] = {}
        self.schemas: Dict[str, Any] = {}

    def load_all(self) -> Dict[str, Any]:
        """Load manifest, schemas, and all artifacts."""
        self.load_manifest()
        self.load_schemas()
        self.load_artifacts()
        return {
            "manifest": self.manifest,
            "schemas": self.schemas,
            "artifacts": self.artifacts,
        }

    def load_manifest(self) -> Dict[str, Any]:
        """Load standards_pack_manifest.json."""
        path = self.standards_pack_dir / "standards_pack_manifest.json"
        self.manifest = self._read_json(path)
        return self.manifest

    def load_schemas(self) -> Dict[str, Any]:
        """Load all JSON schemas from the schemas directory."""
        schemas_dir = self.standards_pack_dir / "schemas"
        self.schemas = {}
        if schemas_dir.exists():
            for f in sorted(schemas_dir.glob("*.json")):
                self.schemas[f.stem] = self._read_json(f)
        return self.schemas

    def load_artifacts(self) -> Dict[str, Any]:
        """Load all standard artifacts referenced in the manifest."""
        self.artifacts = {}
        if not self.manifest:
            self.load_manifest()
        artifacts = self.manifest.get("artifacts", {})
        for key, rel_path in artifacts.items():
            path = self.standards_pack_dir / rel_path
            if path.exists():
                self.artifacts[key] = self._read_json(path)
            else:
                self.artifacts[key] = {"_missing": True, "_expected_path": str(rel_path)}
        return self.artifacts

    def list_standards(self) -> List[Dict[str, Any]]:
        """Return a list of all loaded standard artifacts with metadata."""
        if not self.artifacts:
            self.load_artifacts()
        result = []
        for key, data in sorted(self.artifacts.items()):
            entry = {"standard_id": key}
            if isinstance(data, dict):
                entry["version"] = data.get("version", "unknown")
                entry["missing"] = data.get("_missing", False)
            result.append(entry)
        return result

    def inspect_standard(self, standard_id: str) -> Dict[str, Any]:
        """Return the content of a specific standard artifact."""
        if not self.artifacts:
            self.load_artifacts()
        data = self.artifacts.get(standard_id)
        if data is None:
            return {"error": f"Standard '{standard_id}' not found"}
        return data

    @staticmethod
    def _read_json(path: Path) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
