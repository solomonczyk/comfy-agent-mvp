# IP-Adapter Acquisition Execution Instructions

**Task Code:** RC2-PRODCARDS3Z  
**Precheck Status:** Complete  
**Created:** 2026-04-30T09:53:00Z  
**Shot ID:** shot01  
**Episode ID:** ep01

## Overview

This document provides controlled execution instructions for acquiring the IP-Adapter FaceID Plus SD15 asset. The precheck phase has been completed successfully. This package defines the exact conditions required before a future controlled download/install can be authorized.

## Target Asset

- **Filename:** ip-adapter-faceid-plus_sd15.bin
- **Extension:** .bin
- **Asset Type:** ip_adapter_faceid_plus_sd15
- **Trusted Source:** h94/IP-Adapter-FaceID
- **Source URL:** https://huggingface.co/h94/IP-Adapter-FaceID
- **No Substitution Allowed:** true

## Source Allowlist Verification

- **Source Name:** h94/IP-Adapter-FaceID
- **Source Type:** hugging_face_repository
- **Approval Scope:** source_resolution_only
- **Allowlist Status:** confirmed
- **Allowlist Decision Path:** output/control/ip_adapter_source_allowlist_decision.json

## Target Install Path Plan

- **Final Install Path:** models/ipadapter/ip-adapter-faceid-plus_sd15.bin
- **Temp Acquisition Path:** temp/ip_adapter_acquisition/ip-adapter-faceid-plus_sd15.bin
- **Backup Collision Policy:** backup_existing_if_present
- **Atomic Placement Policy:** atomic_move_from_temp_to_final
- **Overwrite Policy:** no_overwrite_unless_validated

## Validation Policy

### Pre-Acquisition Validation (COMPLETED)
- Source allowlist verification: PASSED
- Target asset verification: PASSED
- Active checkpoint verification: juggernautXL_version2.safetensors - PASSED
- Target shot verification: shot01 - PASSED

### Post-Acquisition Validation (PENDING EXECUTION)
- Existence check: file must exist at temp acquisition path
- File size recording: record file size in bytes
- Hash SHA256 recording: compute and record SHA256 hash
- Extension check: verify .bin extension
- Expected filename exact match: must be ip-adapter-faceid-plus_sd15.bin
- Source reference recording: record h94/IP-Adapter-FaceID
- Allowlist source match: verify source matches allowlist

### Post-Install Validation (PENDING EXECUTION)
- Final location existence check: file must exist at models/ipadapter/
- File size match: must match post-acquisition recording
- Hash verification: SHA256 must match post-acquisition recording
- ComfyUI loadability check: must be loadable by IP-Adapter node

## Execution Authorization Policy

### Current Authorization State
- **Download Authorized:** false
- **Install Authorized:** false
- **Retry Authorized:** false
- **Retry Gate Open:** false
- **Production Accepted:** false
- **Assemble Scene Allowed:** false
- **Downstream Blocked:** true

### Future Execution Requirements
- **Dry-run by default:** true
- **Explicit operator/agent execution flag required:** true
- **Download must be authorized separately:** true
- **Install must be authorized separately:** true
- **Post-install verifier must run after acquisition:** true
- **Retry gate must remain closed after acquisition:** true
- **Generation remains forbidden until separate controlled retry authorization:** true

## Acquisition Phases

### Phase 1: Download from Trusted Source
- **Authorization Required:** true
- **Authorization Granted:** false
- **Source:** h94/IP-Adapter-FaceID
- **Target Filename:** ip-adapter-faceid-plus_sd15.bin
- **Destination:** temp/ip_adapter_acquisition/ip-adapter-faceid-plus_sd15.bin
- **Execution Blocked:** true

### Phase 2: Post-Download Validation
- **Authorization Required:** false
- **Depends On:** Phase 1 Download
- **Validation Steps:** existence, file size, hash, extension, filename, source reference, allowlist match
- **Execution Blocked:** true

### Phase 3: Atomic Install to Final Location
- **Authorization Required:** true
- **Authorization Granted:** false
- **Source:** temp/ip_adapter_acquisition/ip-adapter-faceid-plus_sd15.bin
- **Destination:** models/ipadapter/ip-adapter-faceid-plus_sd15.bin
- **Atomic Placement:** true
- **Backup Policy:** backup_existing_if_present
- **Overwrite Policy:** no_overwrite_unless_validated
- **Execution Blocked:** true

### Phase 4: Post-Install Verification
- **Authorization Required:** false
- **Depends On:** Phase 3 Install
- **Verification Steps:** final location existence, file size match, hash verification, ComfyUI loadability
- **Execution Blocked:** true

## Boundary Compliance

### Actions NOT Performed in This Precheck
- **Download Performed:** false
- **Install Performed:** false
- **Model Move or Copy Performed:** false
- **ComfyUI Generation:** false
- **Generation Performed:** false
- **Retry Generate Frames Executed:** false
- **QA Rerun:** false
- **Downstream Actions Executed:** false

## Next Allowed Action

**controlled_ip_adapter_asset_acquisition_execution_required**

## Execution Blocked Until

- Download authorization granted: false
- Install authorization granted: false
- Explicit operator flag set: false

## Required Files

- Precheck: output/control/ip_adapter_acquisition_precheck.json
- Execution Contract: output/control/ip_adapter_acquisition_execution_contract.json
- Validation Policy: output/control/ip_adapter_validation_policy.json
- Allowlist Decision: output/control/ip_adapter_source_allowlist_decision.json

## Important Notes

1. This precheck package does NOT download the model
2. This precheck package does NOT install the model
3. This precheck package does NOT move/copy model files
4. This precheck package does NOT run retry
5. This precheck package does NOT run ComfyUI
6. This precheck package does NOT generate frames
7. This precheck package does NOT execute retry_generate_frames
8. This precheck package does NOT rerun QA
9. This precheck package does NOT assemble scene
10. This precheck package does NOT attach audio
11. This precheck package does NOT render episode
12. This precheck package does NOT open retry gate
13. This precheck package does NOT mark production_accepted=true
14. This precheck package does NOT unblock downstream
15. Download/install/retry/generation/QA/downstream remain unauthorized and unexecuted

## Failure Handling

- **Validation Failure Action:** block_install_and_report
- **Hash Mismatch Action:** reject_file_and_report
- **Filename Mismatch Action:** reject_file_and_report
- **Source Mismatch Action:** reject_file_and_report
- **Loadability Failure Action:** reject_file_and_report
