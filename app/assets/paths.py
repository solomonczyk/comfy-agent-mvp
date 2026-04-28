"""KT-5 Asset Pipeline: canonical path constants.

Single source of truth for where every artifact class lives on disk.
Naming rules are documented in data/README.md.
"""
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


@dataclass(frozen=True)
class AssetPaths:
    """Canonical asset directories.

    All paths are absolute. Downstream code should import these instead of
    constructing paths ad hoc.
    """

    root: Path = DATA_DIR
    inputs: Path = DATA_DIR / "inputs"
    references: Path = DATA_DIR / "references"
    outputs: Path = DATA_DIR / "outputs"
    outputs_runs: Path = DATA_DIR / "outputs" / "runs"
    batches: Path = DATA_DIR / "batches"
    manifests: Path = DATA_DIR / "manifests"
    traces: Path = DATA_DIR / "traces"
    videos: Path = DATA_DIR / "videos"
    batch_specs: Path = DATA_DIR / "batch_specs"

    def run_dir(self, run_id: str) -> Path:
        """Return the canonical folder for a single run: data/outputs/runs/{run_id}."""
        return self.outputs_runs / run_id

    def batch_dir(self, batch_id: str) -> Path:
        """Return the canonical folder for a batch: data/batches/{batch_id}."""
        return self.batches / batch_id

    def job_dir(self, batch_id: str, job_id: str) -> Path:
        """Return the canonical folder for a batch job: data/batches/{batch_id}/{job_id}."""
        return self.batches / batch_id / job_id

    def manifest_path(self, batch_id: str) -> Path:
        """Return the manifest path for a batch: data/manifests/{batch_id}.json."""
        return self.manifests / f"{batch_id}.json"

    def trace_path(self, run_id: str) -> Path:
        """Return the trace file path for a run: data/traces/{run_id}.jsonl."""
        return self.traces / f"{run_id}.jsonl"

    def video_dir(self, video_id: str) -> Path:
        """Return the canonical folder for a video: data/videos/{video_id}."""
        return self.videos / video_id

    def video_manifest_path(self, video_id: str) -> Path:
        """Return the manifest path for a video: data/manifests/video_{video_id}.json."""
        return self.manifests / f"video_{video_id}.json"


ASSET_PATHS = AssetPaths()


def ensure_asset_dirs(paths: AssetPaths = ASSET_PATHS) -> None:
    """Create all required asset directories if they do not exist."""
    for attr in (
        "inputs",
        "references",
        "outputs",
        "outputs_runs",
        "batches",
        "manifests",
        "traces",
        "videos",
        "batch_specs",
    ):
        getattr(paths, attr).mkdir(parents=True, exist_ok=True)
