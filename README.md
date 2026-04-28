# comfy-agent-mvp

An agent-based system for automated ComfyUI workflow execution, enabling consistent character generation and video production pipelines.

## What is comfy-agent-mvp

comfy-agent-mvp is a Python-based agent system that:
- Orchestrates ComfyUI workflows for automated image and video generation
- Manages character identity consistency across shots
- Integrates text-to-speech (TTS) for voiceover generation
- Provides action planning and execution capabilities
- Supports batch processing of multiple shots

## Current RC2 Status

**Release Candidate 2 (RC2)** - Accepted

RC2 includes:
- Single-shot character identity workflow (ACCEPTED)
- Real voiceover integration (ACCEPTED)
- Multi-shot identity workflow (BLOCKED - pending Character Director and Workflow TD approval)

See [docs/acceptance/ACCEPTANCE_INDEX.md](docs/acceptance/ACCEPTANCE_INDEX.md) for detailed acceptance reports.

## What is in Git

**Source Code & Tests:**
- `app/` - Main application code (agent system, handlers, adapters)
- `tests/` - Test suite for all components
- `scripts/` - Utility and validation scripts

**Documentation:**
- `docs/` - Project documentation
  - `acceptance/` - RC acceptance reports
  - `ARTIFACT_STORAGE_STRATEGY.md` - Storage strategy for artifacts
  - `POST_GIT_AUDIT.md` - Post-git repository audit

**Configuration:**
- `requirements.txt` - Python dependencies
- `.env.example` - Environment configuration template
- `.gitignore` - Git ignore patterns

**Data Schemas & Examples:**
- `data/batch_specs/` - Batch specification examples
- `data/kb_samples/` - Knowledge base samples
- `data/rules/` - Rules documentation

## What is Intentionally Not in Git

**Secrets:**
- `.env` - Environment configuration with API keys and local paths (use `.env.example` as template)

**Generated Artifacts:**
- `data/outputs/` - Generated frames, images, control artifacts
- `data/audio/` - Generated audio files
- `data/videos/` - Generated video files
- `data/traces/` - Runtime traces and debug logs
- `data/manifests/` - Run manifests

**Demo Packs:**
- `data/rc2_demo_pack_ep01.zip` - Visual demo pack (~95 KB)
- `data/rc2_voice_demo_pack_ep01.zip` - Voice demo pack (~313 KB)
- These are intended for GitHub Releases, not Git

**Episode Data:**
- `data/rc_mir_erdan_ep01/` - Full episode data
- `data/rc2_multishot1_ep01/` - Multi-shot test data

**Local Config:**
- `.windsurf/` - IDE configuration
- `data/config/` - Local configuration overrides
- `data/presets/` - User-specific presets

**Temporary Scripts:**
- Root-level `mk*_proof.py` scripts - one-off validation scripts

See [docs/ARTIFACT_STORAGE_STRATEGY.md](docs/ARTIFACT_STORAGE_STRATEGY.md) for detailed storage strategy.

## How to Run Hygiene Validation

**Prerequisites:**
- Python 3.12+
- Install dependencies: `pip install -r requirements.txt`
- Configure environment: Copy `.env.example` to `.env` and configure

**Run validation:**
```bash
# Compile check
python -m py_compile app/cli.py scripts/validate_project_hygiene.py

# Test suite
python -m pytest tests/test_project_hygiene.py tests/test_character_consistency_qa.py tests/test_gorynych_identity.py tests/test_multishot_plan.py -q -s --tb=short

# Full hygiene validation
python scripts/validate_project_hygiene.py --project-root "F:\ComfyUI\comfy-agent-mvp" --json
```

## Where Local Demo Artifacts Live

**Visual Demo:**
- Path: `data/rc2_demo_pack_ep01.zip`
- Extracted: `data/rc2_demo_pack_ep01/`
- Demonstrates: Single-shot character generation with consistent identity

**Voice Demo:**
- Path: `data/rc2_voice_demo_pack_ep01.zip`
- Extracted: `data/rc2_voice_demo_pack_ep01/`
- Demonstrates: Real voiceover integration with TTS

**Episode Data:**
- Path: `data/rc_mir_erdan_ep01/`
- Contains: Full episode data for Mir/Erdan characters

## Known Limitations

### Single-Shot Demo
- Current demo demonstrates single-shot character generation only
- Identity consistency verified for single shots
- Multi-shot identity workflow is blocked (see below)

### Real Voiceover Demo
- Real voiceover integration exists locally
- Voice demo pack demonstrates TTS-to-audio pipeline
- Voice artifacts are stored locally, not in Git

### Multi-Shot Identity Workflow
**Status:** BLOCKED
**Reason:** Requires approval from Character Director and Workflow TD
**Details:**
- Multi-shot identity consistency across shots needs director sign-off
- Workflow technical debt identified in QA
- See [docs/acceptance/RC2_MULTISHOT1C_QA1_ACCEPTANCE_REPORT.md](docs/acceptance/RC2_MULTISHOT1C_QA1_ACCEPTANCE_REPORT.md)

### Generated Artifacts Excluded from Git
- All generated frames, images, audio, video are excluded from Git
- Only acceptance reports and source code are versioned
- Demo zips intended for GitHub Releases, not Git

## Getting Started

1. **Clone the repository:**
   ```bash
   git clone git@github.com:solomonczyk/comfy-agent-mvp.git
   cd comfy-agent-mvp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run validation:**
   ```bash
   python scripts/validate_project_hygiene.py --project-root . --json
   ```

5. **Run tests:**
   ```bash
   pytest tests/ -q
   ```

## Documentation

- [Acceptance Index](docs/acceptance/ACCEPTANCE_INDEX.md) - RC acceptance reports and status
- [Artifact Storage Strategy](docs/ARTIFACT_STORAGE_STRATEGY.md) - Storage strategy for artifacts
- [Post-Git Audit](docs/POST_GIT_AUDIT.md) - Repository audit report

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
