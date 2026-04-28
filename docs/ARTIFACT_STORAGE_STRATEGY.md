# Artifact Storage Strategy

## Overview
This document defines the storage strategy for all artifacts in the comfy-agent-mvp repository, ensuring clean Git history, appropriate use of external storage, and reproducible demos.

## Classification

### 1. What Stays in Git

**Source Code & Configuration:**
- All Python source code (`app/`, `tests/`)
- Requirements files (`requirements.txt`)
- Project documentation (`docs/`, `README.md`)
- Configuration templates (`.env.example`)
- Workflow definitions (small JSON schemas)
- Brief and specification documents (small markdown files)

**Data Schemas & Examples:**
- Batch specification examples (`data/batch_specs/`)
- Knowledge base samples (`data/kb_samples/`)
- Brief examples (`data/brief_example.md`)
- Rules documentation (`data/rules/`)

**Acceptance Reports:**
- All `RC*_ACCEPTANCE_REPORT.md` files (small text files)
- Test reports and validation documentation

**Cleanup Candidates (consider committing):**
- `data/README.md` - data directory documentation
- `data/audio_smoke_brief.md` - smoke test documentation
- `data/smoke_brief.md` - smoke test documentation
- `to-do-plan-for-agent.md` - planning documentation

### 2. What Stays Local Only

**Secrets:**
- `.env` - environment configuration with API keys, local paths
- NEVER commit to Git, use `.env.example` as template

**IDE & Local Config:**
- `.windsurf/` - Windsurf IDE configuration
- Any other IDE-specific folders (`.vscode/`, `.idea/`, etc.)

**Generated Run Data:**
- `data/outputs/` - all generated images, frames, control artifacts
- `data/traces/` - runtime traces and debug logs
- `data/videos/` - generated video files
- `data/audio/` - generated audio files
- `data/smoke_test/` - smoke test outputs
- `data/batches/` - batch run outputs
- `data/manifests/` - run manifests

**Proof Artifacts:**
- `data/artifact_proofs/` - validation proof artifacts
- `data/mk_real3r_proof/` - specific proof artifacts

**Config & Presets (Local):**
- `data/config/` - local configuration overrides
- `data/presets/` - user-specific presets

**Temporary Scripts:**
- All `mk*_proof.py` scripts in root
- `live_runtime_recipe_proof.py`
- These are one-off validation scripts, not core code

### 3. What Should Go to GitHub Releases

**Demo Packs (Release Artifacts):**
- `data/rc2_demo_pack_ep01.zip` (~95 KB) - EP01 visual demo
- `data/rc2_voice_demo_pack_ep01.zip` (~313 KB) - EP01 voice demo
- Future demo packs for other episodes/features

**Release Process:**
1. Create a new GitHub Release (e.g., `v1.0.0`, `rc2-demo`)
2. Upload demo zip files as release assets
3. Update release notes with demo description
4. Reference in README with download link

**Best Demo Zip Path:**
- Primary: `data/rc2_demo_pack_ep01.zip` (visual demo)
- Secondary: `data/rc2_voice_demo_pack_ep01.zip` (voice demo)
- These should be the canonical demo artifacts for RC2

### 4. What Should Use Git LFS (if needed)

**Large Binary Assets (Future):**
- If checkpoint/model files need versioning, use Git LFS
- Large reference images that change frequently
- Any binary files > 100 MB that need version control

**Current State:**
- No current files require Git LFS
- Model/checkpoint files should stay local (in `.gitignore`)

### 5. What Should Go to External Storage

**Architectural Pack:**
- `ComfyUI_Combine_Architectural_Pack.zip` (~193 KB) - documentation pack
- `data/ComfyUI_Combine_Architectural_Pack/` - extracted docs
- Consider moving to external storage (Google Drive, Dropbox) or GitHub Releases
- Currently small enough for Git, but may grow

**Episode Data (Large):**
- `data/rc_mir_erdan_ep01/` - full episode data (if large)
- `data/rc2_multishot1_ep01/` - multishot test data
- If these contain large media, use external storage

**Input Assets:**
- `data/inputs/` - source images, audio, video inputs
- Store externally if large or copyrighted

### 6. How to Preserve Best Demo Zip Path

**Canonical Demo Location:**
- Keep `data/rc2_demo_pack_ep01.zip` as the primary visual demo
- Keep `data/rc2_voice_demo_pack_ep01.zip` as the primary voice demo
- Document these in README with clear download instructions

**Backup Strategy:**
- Upload to GitHub Releases as versioned assets
- Keep local copy in `data/` for easy testing
- Update README with release link

### 7. How to Reproduce/Verify Demo Locally

**Reproduction Steps:**
1. Clone repository
2. Copy `.env.example` to `.env` and configure
3. Download demo zip from GitHub Releases (or use local copy)
4. Extract demo pack to `data/rc2_demo_pack_ep01/`
5. Run demo verification script (if available)
6. Compare outputs against demo pack artifacts

**Verification:**
- Use acceptance reports in `docs/` as reference
- Run test suite: `pytest tests/`
- Check demo artifacts match expected outputs

## Git Ignore Recommendations

Add to `.gitignore`:
```
# Secrets
.env

# IDE
.windsurf/
.vscode/
.idea/

# Generated outputs
data/outputs/
data/traces/
data/videos/
data/audio/
data/smoke_test/
data/batches/
data/manifests/

# Proof artifacts
data/artifact_proofs/
data/mk_real3r_proof/

# Local config
data/config/
data/presets/

# Temporary scripts
mk*_proof.py
live_runtime_recipe_proof.py

# Large zips (use GitHub Releases)
*.zip
```

## Summary Table

| Category | Location | Storage Strategy | Notes |
|----------|----------|------------------|-------|
| Source code | `app/`, `tests/` | Git | Core repository |
| Documentation | `docs/`, `README.md` | Git | Project docs |
| Acceptance reports | `RC*_ACCEPTANCE_REPORT.md` | Git | Validation evidence |
| Demo packs | `data/rc2_*.zip` | GitHub Releases | Versioned artifacts |
| Generated outputs | `data/outputs/` | Local only | Never commit |
| Secrets | `.env` | Local only | Use `.env.example` |
| IDE config | `.windsurf/` | Local only | IDE-specific |
| Proof scripts | `mk*_proof.py` | Local only | Temporary validation |
| Episode data | `data/rc_mir_erdan_ep01/` | External/Local | Large data sets |
| Input assets | `data/inputs/` | External/Local | Source media |

## Next Actions

1. Update `.gitignore` with recommended patterns
2. Move demo zips to GitHub Releases
3. Consider committing small useful docs from root
4. Clean up temporary proof scripts
5. Document external storage locations for large datasets
