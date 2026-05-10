"""Standards Pack Validator — validates JSON artifacts against schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


try:
    import jsonschema
    _HAS_JSONSCHEMA = True
except Exception:  # pragma: no cover
    _HAS_JSONSCHEMA = False


class StandardsPackValidator:
    """Validates the standards pack artifacts and structure."""

    def __init__(self, standards_pack_dir: str | Path) -> None:
        self.standards_pack_dir = Path(standards_pack_dir)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> Dict[str, Any]:
        """Run full validation and return a report."""
        self.errors = []
        self.warnings = []

        manifest_valid = self._validate_manifest()
        schemas_valid = self._validate_schemas_readable()
        artifacts_valid = self._validate_artifacts_present()
        policy_valid = self._validate_policy_consistency()

        return {
            "valid": not self.errors,
            "errors": self.errors,
            "warnings": self.warnings,
            "checks": {
                "manifest_valid": manifest_valid,
                "schemas_readable": schemas_valid,
                "artifacts_present": artifacts_valid,
                "policy_consistency": policy_valid,
            },
        }

    def _validate_manifest(self) -> bool:
        path = self.standards_pack_dir / "standards_pack_manifest.json"
        if not path.exists():
            self.errors.append("standards_pack_manifest.json is missing")
            return False
        try:
            data = self._read_json(path)
            required = ["manifest_id", "version", "task_id", "directories", "artifacts"]
            for key in required:
                if key not in data:
                    self.errors.append(f"manifest missing required field: {key}")
            return True
        except Exception as exc:
            self.errors.append(f"manifest is invalid JSON: {exc}")
            return False

    def _validate_schemas_readable(self) -> bool:
        schemas_dir = self.standards_pack_dir / "schemas"
        if not schemas_dir.exists():
            self.errors.append("schemas directory is missing")
            return False
        ok = True
        for f in sorted(schemas_dir.glob("*.json")):
            try:
                self._read_json(f)
            except Exception as exc:
                self.errors.append(f"schema {f.name} is invalid JSON: {exc}")
                ok = False
        return ok

    def _validate_artifacts_present(self) -> bool:
        manifest_path = self.standards_pack_dir / "standards_pack_manifest.json"
        if not manifest_path.exists():
            return False
        manifest = self._read_json(manifest_path)
        artifacts = manifest.get("artifacts", {})
        ok = True
        for key, rel_path in artifacts.items():
            path = self.standards_pack_dir / rel_path
            if not path.exists():
                self.errors.append(f"artifact '{key}' missing at {rel_path}")
                ok = False
            else:
                try:
                    self._read_json(path)
                except Exception as exc:
                    self.errors.append(f"artifact '{key}' is invalid JSON: {exc}")
                    ok = False
        return ok

    def _validate_policy_consistency(self) -> bool:
        """Check that decision policies do not contain contradictions."""
        policies_dir = self.standards_pack_dir / "policies"
        if not policies_dir.exists():
            self.warnings.append("policies directory missing — skipping policy consistency check")
            return True
        ok = True
        for f in sorted(policies_dir.glob("*.json")):
            try:
                data = self._read_json(f)
                rules = data.get("rules", [])
                for rule in rules:
                    if rule.get("production_accepted") is True:
                        # Verify there is an explicit operator gate condition
                        condition = rule.get("condition", {})
                        if not condition.get("operator_final_approval") and not condition.get("decision_source") == "human_operator":
                            self.warnings.append(
                                f"policy {f.name} rule {rule.get('rule_id')} sets production_accepted=true without explicit operator gate"
                            )
            except Exception:
                pass
        return ok

    def validate_schema(self, artifact_path: Path, schema_path: Path) -> Dict[str, Any]:
        """Validate a single artifact against a schema using jsonschema if available."""
        if not _HAS_JSONSCHEMA:
            return {
                "valid": True,
                "note": "jsonschema not installed; skipping strict schema validation",
            }
        try:
            schema = self._read_json(schema_path)
            artifact = self._read_json(artifact_path)
            jsonschema.validate(instance=artifact, schema=schema)
            return {"valid": True, "errors": []}
        except jsonschema.ValidationError as exc:
            return {"valid": False, "errors": [str(exc)]}
        except Exception as exc:
            return {"valid": False, "errors": [str(exc)]}

    @staticmethod
    def _read_json(path: Path) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
