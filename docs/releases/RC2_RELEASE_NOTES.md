# RC2 Demo Pack v1 - Release Notes

## Release Information
- **Version:** rc2-demo-v1
- **Release Date:** 2026-04-28
- **Commit:** ad33d58
- **Branch:** main

## Overview
This release contains demo artifacts for Release Candidate 2 (RC2) of the comfy-agent-mvp project. The artifacts demonstrate single-shot character generation with consistent identity and real voiceover integration.

## What This Release Demonstrates

### Visual Demo Pack
- **File:** `rc2_demo_pack_ep01.zip` (~95 KB)
- **Demonstrates:** Single-shot character generation with consistent identity
- **Features:**
  - Character consistency across generated frames
  - ComfyUI workflow execution
  - Control artifact generation
  - Shot-level planning and execution

### Voice Demo Pack
- **File:** `rc2_voice_demo_pack_ep01.zip` (~313 KB)
- **Demonstrates:** Real voiceover integration with text-to-speech
- **Features:**
  - TTS-to-audio pipeline
  - Voice synchronization with visual content
  - Audio artifact generation

## Accepted RC2 Stack

### Single-Shot Identity Workflow
- **Status:** ACCEPTED
- **Acceptance Report:** RC2_GORYNYCH1_ACCEPTANCE_REPORT.md
- **Description:** Character identity consistency verified for single shots

### Real Voiceover Integration
- **Status:** ACCEPTED
- **Acceptance Report:** RC_FLOW1I_ACCEPTANCE_REPORT.md
- **Description:** TTS integration and voiceover pipeline

### Multi-Shot Identity Workflow
- **Status:** BLOCKED
- **Reason:** Requires Character Director and Workflow TD approval
- **Acceptance Report:** RC2_MULTISHOT1C_QA1_ACCEPTANCE_REPORT.md
- **Description:** Multi-shot identity consistency pending approval

## Artifacts Attached

### rc2_demo_pack_ep01.zip
- **Size:** 97,158 bytes (95 KB)
- **SHA256:** 4037b308fa6844332d53b9d27db858bee0b3ccdefd678838aa83fea6d601c2a9
- **Local Path:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01.zip`
- **Extracted:** `data/rc2_demo_pack_ep01/`
- **Artifact Kind:** Visual demo pack

### rc2_voice_demo_pack_ep01.zip
- **Size:** 320,818 bytes (313 KB)
- **SHA256:** c328eff4d4da107f7fa5706f09340cce6a0d0c6ba29716934b87ef3f08499099
- **Local Path:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01.zip`
- **Extracted:** `data/rc2_voice_demo_pack_ep01/`
- **Artifact Kind:** Voice demo pack

## Known Limitations

### Single-Shot Demo Only
- Current demo demonstrates single-shot character generation only
- Identity consistency verified for single shots
- Multi-shot identity workflow is blocked (see below)

### Multi-Shot Identity Workflow Blocked
- Multi-shot identity consistency across shots requires Character Director approval
- Workflow technical debt identified in QA
- See acceptance reports in `docs/acceptance/` for details

### Generated Artifacts Excluded from Git
- All generated frames, images, audio, video are excluded from Git
- Only acceptance reports and source code are versioned
- Demo zips are distributed via GitHub Releases, not Git

## Installation & Usage

### Prerequisites
- Clone the repository: `git clone git@github.com:solomonczyk/comfy-agent-mvp.git`
- Install dependencies: `pip install -r requirements.txt`
- Configure environment: Copy `.env.example` to `.env` and configure

### Download Demo Packs
1. Download both zip files from this release
2. Extract to `data/` directory in the repository
3. Verify SHA256 checksums against the values listed above

### Verification
```bash
# Verify checksums (Linux/Mac)
sha256sum -c <<EOF
4037b308fa6844332d53b9d27db858bee0b3ccdefd678838aa83fea6d601c2a9  data/rc2_demo_pack_ep01.zip
c328eff4d4da107f7fa5706f09340cce6a0d0c6ba29716934b87ef3f08499099  data/rc2_voice_demo_pack_ep01.zip
EOF

# Verify checksums (PowerShell)
Get-FileHash data\rc2_demo_pack_ep01.zip -Algorithm SHA256
Get-FileHash data\rc2_voice_demo_pack_ep01.zip -Algorithm SHA256
```

### Run Tests
```bash
# Run test suite
pytest tests/ -q

# Run hygiene validation
python scripts/validate_project_hygiene.py --project-root . --json
```

## Documentation

- [Acceptance Index](../acceptance/ACCEPTANCE_INDEX.md) - RC acceptance reports and status
- [Artifact Storage Strategy](../ARTIFACT_STORAGE_STRATEGY.md) - Storage strategy for artifacts
- [Post-Git Audit](../POST_GIT_AUDIT.md) - Repository audit report
- [README.md](../../README.md) - Project overview and getting started

## Important Notes

### Artifacts Not Committed to Git
**WARNING:** These demo artifacts are intentionally NOT committed to Git history. They are distributed via GitHub Releases to keep the repository clean and avoid large binary files in version control.

### Local Artifact Paths
The artifacts referenced in this release are stored locally at:
- `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01.zip`
- `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01.zip`

These paths are for reference only. Download the artifacts from this release rather than copying from local paths.

### Checksum Verification
Always verify the SHA256 checksums after downloading to ensure artifact integrity.

## Support

For issues or questions:
- Review acceptance reports in `docs/acceptance/`
- Check the [README.md](../../README.md) for getting started guide
- Run hygiene validation to verify project state

## License

[Add your license here]
