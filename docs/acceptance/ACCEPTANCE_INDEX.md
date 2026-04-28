# Acceptance Index

## Overview
This index documents all accepted RC (Release Candidate) layers for the comfy-agent-mvp project.

## Accepted Stack

### RC2 - Release Candidate 2
**Status:** Accepted

**Commit References:**
- Initial commit: `94c9a7a` - chore: initial commit of comfy-agent-mvp project
- Post-git audit: `2e3c2a0` - docs: add post-git audit and artifact storage strategy

## Accepted Reports

### Flow Acceptance Reports
- `RC_FLOW1H_ACCEPTANCE_REPORT.md` - Flow 1H acceptance (single-shot visual pipeline)
- `RC_FLOW1I_ACCEPTANCE_REPORT.md` - Flow 1I acceptance (voice pipeline)

### RC2 Layer Acceptance Reports
- `RC2_TESTBASE1_ACCEPTANCE_REPORT.md` - Test base layer acceptance
- `RC2_GORYNYCH1_ACCEPTANCE_REPORT.md` - Gorynych identity workflow acceptance
- `RC2_FILMROLES1_ACCEPTANCE_REPORT.md` - Film roles layer acceptance
- `RC2_FILMROLES1B_ACCEPTANCE_REPORT.md` - Film roles layer acceptance (revision)
- `RC2_MULTISHOT1A_ACCEPTANCE_REPORT.md` - Multi-shot layer acceptance (initial)
- `RC2_MULTISHOT1B_ACCEPTANCE_REPORT.md` - Multi-shot layer acceptance (revision)
- `RC2_MULTISHOT1C_ACCEPTANCE_REPORT.md` - Multi-shot layer acceptance (revision)
- `RC2_MULTISHOT1C_QA1_ACCEPTANCE_REPORT.md` - Multi-shot QA acceptance

## Local-Only Artifact References

### Demo Artifacts (Not in Git)
**Visual Demo:**
- Path: `data/rc2_demo_pack_ep01.zip` (~95 KB)
- Intended storage: GitHub Releases
- Local extraction: `data/rc2_demo_pack_ep01/`

**Voice Demo:**
- Path: `data/rc2_voice_demo_pack_ep01.zip` (~313 KB)
- Intended storage: GitHub Releases
- Local extraction: `data/rc2_voice_demo_pack_ep01/`

### Episode Data (Not in Git)
- `data/rc_mir_erdan_ep01/` - Full episode data for Mir/Erdan
- `data/rc2_multishot1_ep01/` - Multi-shot test data for EP01

### Generated Outputs (Not in Git)
- `data/outputs/` - All generated frames, images, control artifacts
- `data/audio/` - Generated audio files
- `data/videos/` - Generated video files
- `data/traces/` - Runtime traces and debug logs
- `data/manifests/` - Run manifests

## Current Best Demo Artifact Path

**Primary Visual Demo:**
```
data/rc2_demo_pack_ep01.zip
```
This is the canonical visual demo for RC2, demonstrating single-shot character generation with consistent identity.

**Primary Voice Demo:**
```
data/rc2_voice_demo_pack_ep01.zip
```
This is the canonical voice demo for RC2, demonstrating real voiceover integration.

## Current Blocked Multi-Shot State

**Status:** Blocked
**Reason:** Multi-shot identity workflow requires approval from:
- Character Director
- Workflow TD

**Current State:**
- Single-shot identity workflow: **ACCEPTED** (RC2_GORYNYCH1)
- Multi-shot identity workflow: **BLOCKED** pending approval
- Multi-shot planning and QA reports: **ACCEPTED** (RC2_MULTISHOT1C, RC2_MULTISHOT1C_QA1)

**Blocker Details:**
- Multi-shot identity consistency across shots requires director sign-off
- Workflow technical debt needs TD review
- See `RC2_MULTISHOT1C_QA1_ACCEPTANCE_REPORT.md` for detailed QA findings

## Demo Zip Storage Strategy

**Important:** Demo zips are intentionally stored outside Git.

**Rationale:**
- Demo zips contain generated media artifacts
- Large binary files should not be in version control
- Versioned releases should use GitHub Releases
- Local copies remain for testing and verification

**Reproduction:**
1. Clone repository
2. Download demo zip from GitHub Releases (when available)
3. Extract to `data/` directory
4. Run verification scripts
5. Compare outputs against acceptance reports

## Known Limitations

### Single-Shot Demo
- Current demo demonstrates single-shot character generation
- Identity consistency verified for single shots
- Multi-shot identity workflow is blocked (see above)

### Real Voiceover Demo
- Real voiceover integration exists locally
- Voice demo pack demonstrates TTS-to-audio pipeline
- Voice artifacts are stored locally, not in Git

### Multi-Shot Identity Workflow
- **BLOCKED** - Requires Character Director and Workflow TD approval
- Technical debt identified in QA report
- See `RC2_MULTISHOT1C_QA1_ACCEPTANCE_REPORT.md` for details

### Generated Artifacts Excluded from Git
- All generated frames, images, audio, video are excluded
- Only acceptance reports and source code are tracked
- Demo zips intended for GitHub Releases, not Git

## Verification

To verify acceptance status:
1. Review individual acceptance reports in this directory
2. Check commit history for corresponding implementation
3. Verify local demo artifacts match acceptance criteria
4. Run test suite: `pytest tests/`
5. Run hygiene validation: `python scripts/validate_project_hygiene.py`

## Next Steps

1. Upload demo zips to GitHub Releases as versioned assets
2. Obtain Character Director and Workflow TD approval for multi-shot workflow
3. Resolve multi-shot technical debt identified in QA
4. Update this index with new acceptance reports as RC progresses
