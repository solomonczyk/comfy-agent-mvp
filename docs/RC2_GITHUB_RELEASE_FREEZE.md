# RC2 GitHub Release Freeze

## Freeze Information
- **Freeze Date:** 2026-04-28
- **Freeze Commit:** 90f2c3a

## Repository Information
- **GitHub Repository:** https://github.com/solomonczyk/comfy-agent-mvp
- **Remote URL:** git@github.com:solomonczyk/comfy-agent-mvp.git
- **Branch:** main
- **Latest Commit:** 90f2c3a

## GitHub Release Information
- **Release URL:** https://github.com/solomonczyk/comfy-agent-mvp/releases/tag/rc2-demo-v1
- **Release Tag:** rc2-demo-v1
- **Release Title:** RC2 Demo Pack v1
- **Release Type:** Pre-release (draft)
- **Target Commit:** 16c3f9a

## Release Assets

### Attached Assets
1. **rc2_demo_pack_ep01.zip**
   - **Size:** 97,158 bytes (95 KB)
   - **SHA256:** 4037b308fa6844332d53b9d27db858bee0b3ccdefd678838aa83fea6d601c2a9
   - **Description:** Single-shot character generation demo with consistent identity

2. **rc2_voice_demo_pack_ep01.zip**
   - **Size:** 320,818 bytes (313 KB)
   - **SHA256:** c328eff4d4da107f7fa5706f09340cce6a0d0c6ba29716934b87ef3f08499099
   - **Description:** Real voiceover integration demo with TTS

## Verification Status
- **Verification Date:** 2026-04-28
- **Verification Result:** PASSED
- **Verification Report:** docs/releases/RC2_RELEASE_ASSET_VERIFICATION.md
- **Details:** All release assets were successfully downloaded from GitHub and their SHA256 checksums match the expected values in the release manifest.

## Known Limitations

### Single-Shot Demo Only
- Current demo demonstrates single-shot character generation only
- Identity consistency verified for single shots
- Multi-shot identity workflow is blocked

### Multi-Shot Identity Workflow Blocked
- Multi-shot identity consistency across shots requires Character Director approval
- Workflow technical debt identified in QA
- See acceptance reports in `docs/acceptance/` for details

### Generated Artifacts Excluded from Git
- All generated frames, images, audio, video are excluded from Git
- Only acceptance reports and source code are versioned
- Demo zips are distributed via GitHub Releases, not Git

## DO NOT MUTATE WARNING

**CRITICAL:** This release state is frozen. Do NOT mutate the following:

- Release assets (zip files on GitHub Release)
- Release metadata (tag, title, description)
- Attached files
- SHA256 checksums
- Target commit reference

Any changes to the release state must go through a new release process with proper versioning and verification.

## Release Documentation

- [Release Notes](docs/releases/RC2_RELEASE_NOTES.md)
- [Release Asset Verification](docs/releases/RC2_RELEASE_ASSET_VERIFICATION.md)
- [Release Assets Manifest](data/cleanup/RC2_RELEASE_ASSETS.json)
- [Manual Release Upload Instructions](docs/releases/RC2_MANUAL_RELEASE_UPLOAD.md)
- [Handoff Documentation](docs/HANDOFF_AFTER_RC2_RELEASE.md)

## Acceptance Status

### Accepted RC2 Stack
- **Single-Shot Identity Workflow:** ACCEPTED (RC2_GORYNYCH1_ACCEPTANCE_REPORT.md)
- **Real Voiceover Integration:** ACCEPTED (RC_FLOW1I_ACCEPTANCE_REPORT.md)
- **Multi-Shot Identity Workflow:** BLOCKED (RC2_MULTISHOT1C_QA1_ACCEPTANCE_REPORT.md)

## Next Steps

See [HANDOFF_AFTER_RC2_RELEASE.md](docs/HANDOFF_AFTER_RC2_RELEASE.md) for:
- Recommended next tasks
- What is safely on GitHub
- What remains local-only
- Character Director and Workflow TD approval requirements
