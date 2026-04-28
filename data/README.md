# KT-5 Minimal Asset Pipeline v1

Canonical layout of the `data/` folder. All agent artifacts MUST live under
this tree so downstream tooling can find them deterministically.

## Folder structure

```
data/
├── inputs/         # user-provided raw inputs for edit/img2img runs
├── references/     # reference images (style/identity/keyframes)
├── outputs/
│   └── runs/
│       └── {run_id}/          # one folder per single agent run
│           ├── metadata.json  # copy of sdxl_agent_run_*.json
│           ├── summary.txt    # copy of run_summary_*.txt
│           ├── trace.jsonl    # copy of the KT-2 tool trace
│           ├── result.json    # full agent result contract
│           └── images/        # downloaded output images
├── batches/
│   └── {batch_id}/            # one folder per batch
│       └── {job_id}/          # one folder per job in the batch
│           ├── metadata.json
│           ├── summary.txt
│           ├── trace.jsonl
│           ├── result.json
│           └── images/
├── manifests/
│   └── {batch_id}.json        # batch manifest (per-job status, timestamps, paths)
├── traces/
│   └── {run_id}.jsonl         # raw KT-2 tool trace for every run
├── videos/
│   └── {video_id}/            # KT-6 video pipeline output per input video
│       ├── frames/            # all extracted frames (frame_NNNNNN.png)
│       ├── processed/         # processed subset (renumbered contiguously)
│       └── export.mp4         # assembled video from processed frames
├── batch_specs/
│   └── {batch_name}.json      # batch spec definitions
├── presets/
├── workflows/
└── README.md                  # this file
```

## Naming rules

- **run_id**: 8-char lowercase hex (first 8 of a `uuid.uuid4().hex`). Example: `39a6414c`.
- **batch_id**: lowercase alphanumeric + underscores, author-defined. Example: `portrait_light_001`.
- **job_id**: lowercase alphanumeric + underscores, author-defined, unique within a batch. Example: `job_001`.
- **image filenames**: preserved from ComfyUI (e.g. `sdxl_agent_00008_.png`); stored under `.../images/`.
- **per-run files** inside `runs/{run_id}/` and `batches/{batch_id}/{job_id}/` use fixed names:
  `metadata.json`, `summary.txt`, `trace.jsonl`, `result.json`.
- **manifests**: always `data/manifests/{batch_id}.json`; video manifests at `data/manifests/video_{video_id}.json`.
- **traces**: always `data/traces/{run_id}.jsonl` (source of truth); copied into the run/job folder.
- **video_id**: lowercase alphanumeric + underscores. Either author-provided (`--video-id`) or derived as `{sanitized_input_stem}_{YYYYMMDD_HHMMSS}`.
- **video frames**: 6-digit zero-padded `frame_NNNNNN.png`, contiguous from `frame_000001.png` in both `frames/` and `processed/`.

## Source of truth

`app/assets/paths.py` is the only place that encodes these paths. Downstream
code must import `AssetPaths` / `ASSET_PATHS` instead of hard-coding.

`app/assets/organizer.py::organize_run_artifacts(target_dir, result)` is the
only function that writes into a `{run_id}` or `{job_id}` folder; it copies
metadata / summary / trace and downloads images via ComfyUI `/view`.
