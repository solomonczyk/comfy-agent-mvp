# RC2 Manual Release Upload Instructions

## Overview
This document provides step-by-step instructions for manually creating a GitHub Release for RC2 demo artifacts, since GitHub CLI (gh) is not available on this system.

## Release Information
- **GitHub Repository:** https://github.com/solomonczyk/comfy-agent-mvp
- **Release Tag:** rc2-demo-v1
- **Release Title:** RC2 Demo Pack v1
- **Target Branch:** main
- **Target Commit:** 7e93e40
- **Release Type:** Draft (do not publish)

## Assets to Upload

### Asset 1: Visual Demo Pack
- **File:** rc2_demo_pack_ep01.zip
- **Size:** 97,158 bytes (95 KB)
- **SHA256:** 4037b308fa6844332d53b9d27db858bee0b3ccdefd678838aa83fea6d601c2a9
- **Local Path:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01.zip`

### Asset 2: Voice Demo Pack
- **File:** rc2_voice_demo_pack_ep01.zip
- **Size:** 320,818 bytes (313 KB)
- **SHA256:** c328eff4d4da107f7fa5706f09340cce6a0d0c6ba29716934b87ef3f08499099
- **Local Path:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01.zip`

## Step-by-Step GitHub Web UI Upload Instructions

### Step 1: Navigate to GitHub Releases
1. Open your web browser
2. Go to: https://github.com/solomonczyk/comfy-agent-mvp/releases
3. Click "Create a new release" button

### Step 2: Configure Release Settings
1. **Choose a tag:**
   - Enter: `rc2-demo-v1`
   - Click "Create new tag: rc2-demo-v1 on publish"
   - **Target:** Select `main` branch
   - **Target Commit:** Should auto-select `7e93e40` (verify this is correct)

2. **Release title:**
   - Enter: `RC2 Demo Pack v1`

3. **Describe this release:**
   - Copy the contents from: `docs/releases/RC2_RELEASE_NOTES.md`
   - Paste into the release notes text area
   - Or upload the file as an attachment if GitHub supports it

### Step 3: Upload Assets
1. **Binary attachment section:**
   - Click "Attach binaries"
   - Navigate to: `F:\ComfyUI\comfy-agent-mvp\data\`
   - Select: `rc2_demo_pack_ep01.zip`
   - Click "Attach" or "Open"
   - Wait for upload to complete

2. **Upload second asset:**
   - Click "Attach binaries" again
   - Navigate to: `F:\ComfyUI\comfy-agent-mvp\data\`
   - Select: `rc2_voice_demo_pack_ep01.zip`
   - Click "Attach" or "Open"
   - Wait for upload to complete

### Step 4: Verify Uploads
1. Check that both files appear in the "Assets" section
2. Verify file sizes match:
   - rc2_demo_pack_ep01.zip: ~95 KB
   - rc2_voice_demo_pack_ep01.zip: ~313 KB

### Step 5: Set as Draft Release
1. **Important:** Ensure "Set as a pre-release" is UNCHECKED
2. **Important:** Ensure "Set as a draft release" is CHECKED
3. This prevents accidental publication

### Step 6: Create Release
1. Click "Publish release" button
2. Since it's a draft, it will not be publicly visible
3. You can review and publish later when ready

## Warning: Do NOT Commit Zips to Git
**CRITICAL:** Never commit the demo zip files to Git history. These artifacts are intentionally excluded from version control to:
- Keep repository size manageable
- Avoid large binary files in Git history
- Distribute artifacts via GitHub Releases instead

The `.gitignore` file should exclude:
- `*.zip` files
- `data/outputs/` directory
- `data/audio/` directory
- `data/videos/` directory
- All generated artifacts

## SHA256 Checksum Verification

### Before Upload
Verify the SHA256 checksums of the local files:

**Windows PowerShell:**
```powershell
Get-FileHash data\rc2_demo_pack_ep01.zip -Algorithm SHA256
Get-FileHash data\rc2_voice_demo_pack_ep01.zip -Algorithm SHA256
```

**Expected Output:**
```
rc2_demo_pack_ep01.zip: 4037b308fa6844332d53b9d27db858bee0b3ccdefd678838aa83fea6d601c2a9
rc2_voice_demo_pack_ep01.zip: c328eff4d4da107f7fa5706f09340cce6a0d0c6ba29716934b87ef3f08499099
```

### After Download (for users)
Users should verify checksums after downloading from the release:

**Linux/Mac:**
```bash
sha256sum -c <<EOF
4037b308fa6844332d53b9d27db858bee0b3ccdefd678838aa83fea6d601c2a9  rc2_demo_pack_ep01.zip
c328eff4d4da107f7fa5706f09340cce6a0d0c6ba29716934b87ef3f08499099  rc2_voice_demo_pack_ep01.zip
EOF
```

**Windows PowerShell:**
```powershell
Get-FileHash rc2_demo_pack_ep01.zip -Algorithm SHA256
Get-FileHash rc2_voice_demo_pack_ep01.zip -Algorithm SHA256
```

## Expected Final Verification Steps

### After Release Creation
1. **Verify release is draft:**
   - Go to: https://github.com/solomonczyk/comfy-agent-mvp/releases
   - Confirm release appears with "Draft" badge
   - Confirm it is NOT publicly visible

2. **Verify assets are attached:**
   - Click on the draft release
   - Confirm both zip files are listed
   - Verify file sizes match expected values

3. **Verify release notes:**
   - Confirm release notes display correctly
   - Confirm commit reference is `7e93e40`
   - Confirm SHA256 checksums are listed

4. **Verify no zips in Git:**
   - Run: `git status --short`
   - Confirm `.zip` files are NOT staged
   - Confirm `.zip` files are NOT in recent commits
   - Run: `git log --all --full-history -- "*.zip"`
   - Should return no results (no zips ever committed)

## Alternative: Install GitHub CLI

If you prefer to use GitHub CLI in the future, install it from:
- https://cli.github.com/

After installation, authenticate:
```bash
gh auth login
```

Then create the release:
```bash
gh release create rc2-demo-v1 \
  data/rc2_voice_demo_pack_ep01.zip \
  data/rc2_demo_pack_ep01.zip \
  --title "RC2 Demo Pack v1" \
  --notes-file docs/releases/RC2_RELEASE_NOTES.md \
  --target main \
  --draft
```

## Troubleshooting

### Upload Fails
- Check internet connection
- Verify file paths are correct
- Ensure files are not corrupted
- Try uploading one file at a time

### Release Not Visible
- Check if it's in draft mode (expected)
- Check if you have permissions to create releases
- Verify repository is not private (if you expect public visibility)

### Checksum Mismatch
- Re-download the file
- Re-calculate SHA256 locally
- Contact repository maintainer if issue persists

## Support

For issues or questions:
- Review release notes in `docs/releases/RC2_RELEASE_NOTES.md`
- Check acceptance reports in `docs/acceptance/`
- Review artifact manifest in `data/cleanup/RC2_RELEASE_ASSETS.json`
- Run hygiene validation: `python scripts/validate_project_hygiene.py --project-root . --json`

## References
- GitHub Releases Documentation: https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository
- Release Notes: `docs/releases/RC2_RELEASE_NOTES.md`
- Artifact Manifest: `data/cleanup/RC2_RELEASE_ASSETS.json`
