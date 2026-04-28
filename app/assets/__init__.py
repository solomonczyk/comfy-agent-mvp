"""KT-5 Minimal Asset Pipeline v1.

Central definitions for the stable local asset structure used by
single runs, batches, traces, manifests, inputs, references, and outputs.
"""
from app.assets.paths import AssetPaths, ensure_asset_dirs
from app.assets.organizer import organize_run_artifacts

__all__ = ["AssetPaths", "ensure_asset_dirs", "organize_run_artifacts"]
