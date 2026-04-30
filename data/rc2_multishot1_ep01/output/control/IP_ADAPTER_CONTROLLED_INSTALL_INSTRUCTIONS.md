# IP-Adapter FaceID Plus Controlled Install Instructions

**Task Code:** RC2-PRODCARDS3X  
**Episode:** ep01  
**Shot:** shot01  
**Target Asset:** ip-adapter-faceid-plus_sd15.bin  
**Created:** 2026-04-30T09:31:00Z

## Overview

This document provides controlled installation instructions for the IP-Adapter FaceID Plus model required for dual-lock identity preservation in shot01 retry.

## Target Asset Information

- **Filename:** ip-adapter-faceid-plus_sd15.bin
- **Asset Type:** ip_adapter_faceid_plus_sd15
- **Required For:** dual-lock identity preservation for shot01 retry
- **Expected Install Path:** models/ipadapter/ip-adapter-faceid-plus_sd15.bin
- **Current Status:** missing
- **Install Status:** pending

## Pre-Installation Requirements

### Source Resolution

Before any download:

1. **Trusted Source Must Be Explicitly Recorded**
   - Document the source URL/reference
   - Verify source is trusted (e.g., official HuggingFace, GitHub release)
   - No mirror or random sources allowed
   - No silent model substitution allowed

2. **License/Status Must Be Recorded**
   - Record license information if available
   - Record model status (e.g., stable, experimental)
   - Document any usage restrictions

3. **Filename Match Verification**
   - Source filename must match expected filename: ip-adapter-faceid-plus_sd15.bin
   - No filename substitutions allowed

## Controlled Acquisition Flow

### Phase 1: Source Review (Dry Run)

- Review and record trusted source before any download
- Document source URL/reference
- Record license/status if available
- Verify filename match
- **Execution Mode:** dry_run
- **Explicit Flag Required:** true

### Phase 2: Temp Download (Dry Run)

- Download to temporary location only
- Record file size
- Calculate hash/checksum if possible
- **Execution Mode:** dry_run
- **Explicit Flag Required:** true

### Phase 3: Validation (Dry Run)

- Validate downloaded file before final placement
- Extension validation (.bin)
- Size validation
- Hash/checksum validation if available
- Filename match verification
- **Execution Mode:** dry_run
- **Explicit Flag Required:** true

### Phase 4: Atomic Placement (Dry Run)

- Atomic move/copy to final location only after validation passes
- Target path: models/ipadapter/ip-adapter-faceid-plus_sd15.bin
- **Execution Mode:** dry_run
- **Explicit Flag Required:** true

### Phase 5: Post-Install Verification (Dry Run)

- Run post-install verification contract
- Verify file exists at expected path
- Verify extension is .bin
- Record file size
- Record hash/checksum
- Record source reference
- **Execution Mode:** dry_run
- **Explicit Flag Required:** true

## Post-Install Verification Contract

After installation, the following must be verified:

1. **File Existence Check**
   - File exists at: models/ipadapter/ip-adapter-faceid-plus_sd15.bin

2. **Extension Validation**
   - File extension is .bin

3. **Size Validation**
   - File size recorded and validated

4. **Checksum Validation**
   - Hash/checksum recorded if available

5. **Source Reference**
   - Source reference recorded

6. **Checkpoint Integrity**
   - Active checkpoint remains: juggernautXL_version2.safetensors

7. **Shot Integrity**
   - Target shot remains: shot01

8. **Retry Gate Integrity**
   - retry_gate_open remains: false

## State Integrity Requirements

After installation and verification, the following state must be maintained:

- **active_checkpoint:** juggernautXL_version2.safetensors
- **target_shot:** shot01
- **retry_gate_open:** false
- **production_accepted:** false
- **assemble_scene_allowed:** false
- **downstream_blocked:** true

## Next Allowed Action

Only after all post-install verification checks pass:

- **next_allowed_action:** controlled_retry_authorization_required
- **retry_gate_open:** false (remains closed until verification layer passes)

## Boundary Conditions

The following actions are NOT permitted as part of this contract:

- Download without source review
- Install without validation
- Move/copy model files without atomic operation
- Open retry gate before verification
- Mark production_accepted=true
- Unblock downstream before verification
- Run ComfyUI generation
- Execute retry_generate_frames
- Rerun QA
- Assemble scene
- Attach audio
- Render episode

## Safety Notes

- All phases default to dry-run mode
- Explicit execution flag required for each phase
- Source allowlist required
- Retry gate remains closed after install until verification layer passes
- No silent model substitution allowed
- No mirror or random sources allowed

## Verification Status

- **Contract Created:** true
- **Download Performed:** false
- **Install Performed:** false
- **Model Move/Copy Performed:** false
- **Verification Performed:** false
- **All Checks Passed:** false
- **Next Allowed Action:** controlled_ip_adapter_asset_acquisition_required
