# RC2 Release Asset Verification

## Verification Information
- **Verification Date:** 2026-04-28
- **Release URL:** https://github.com/solomonczyk/comfy-agent-mvp/releases/tag/rc2-demo-v1
- **Release Tag:** rc2-demo-v1
- **Target Commit:** 16c3f9a

## Downloaded Assets

### Download Folder
`data/release_verify/rc2-demo-v1` (untracked)

### Downloaded Files
1. rc2_demo_pack_ep01.zip
2. rc2_voice_demo_pack_ep01.zip

## SHA256 Checksum Comparison

### Asset 1: rc2_demo_pack_ep01.zip
- **File Size:** 97,158 bytes (95 KB)
- **Expected SHA256:** 4037b308fa6844332d53b9d27db858bee0b3ccdefd678838aa83fea6d601c2a9
- **Actual SHA256:** 4037b308fa6844332d53b9d27db858bee0b3ccdefd678838aa83fea6d601c2a9
- **Match:** true

### Asset 2: rc2_voice_demo_pack_ep01.zip
- **File Size:** 320,818 bytes (313 KB)
- **Expected SHA256:** c328eff4d4da107f7fa5706f09340cce6a0d0c6ba29716934b87ef3f08499099
- **Actual SHA256:** c328eff4d4da107f7fa5706f09340cce6a0d0c6ba29716934b87ef3f08499099
- **Match:** true

## Verification Summary Table

| Asset | Size (bytes) | Expected SHA256 | Actual SHA256 | Match |
|-------|-------------|----------------|---------------|-------|
| rc2_demo_pack_ep01.zip | 97,158 | 4037b308fa6844332d53b9d27db858bee0b3ccdefd678838aa83fea6d601c2a9 | 4037b308fa6844332d53b9d27db858bee0b3ccdefd678838aa83fea6d601c2a9 | true |
| rc2_voice_demo_pack_ep01.zip | 320,818 | c328eff4d4da107f7fa5706f09340cce6a0d0c6ba29716934b87ef3f08499099 | c328eff4d4da107f7fa5706f09340cce6a0d0c6ba29716934b87ef3f08499099 | true |

## Final Verdict
**PASSED** - All release assets were successfully downloaded from GitHub and their SHA256 checksums match the expected values in the release manifest.

## Verification Commands

### Download Commands
```powershell
mkdir -p data/release_verify/rc2-demo-v1
Invoke-WebRequest -Uri "https://github.com/solomonczyk/comfy-agent-mvp/releases/download/rc2-demo-v1/rc2_demo_pack_ep01.zip" -OutFile "data/release_verify/rc2-demo-v1/rc2_demo_pack_ep01.zip"
Invoke-WebRequest -Uri "https://github.com/solomonczyk/comfy-agent-mvp/releases/download/rc2-demo-v1/rc2_voice_demo_pack_ep01.zip" -OutFile "data/release_verify/rc2-demo-v1/rc2_voice_demo_pack_ep01.zip"
```

### Checksum Verification Commands
```powershell
Get-FileHash data/release_verify/rc2-demo-v1/rc2_demo_pack_ep01.zip -Algorithm SHA256
Get-FileHash data/release_verify/rc2-demo-v1/rc2_voice_demo_pack_ep01.zip -Algorithm SHA256
```

## Notes
- Downloaded zip files remain untracked in Git
- Verification folder `data/release_verify/` is excluded from version control
- This verification confirms that the GitHub Release artifacts are correctly uploaded and match the expected release manifest
