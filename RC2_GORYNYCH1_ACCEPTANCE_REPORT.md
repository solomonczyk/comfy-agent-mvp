# RC2-GORYNYCH1 Acceptance Report

## Objective
Break the repeated failed loop where the system uses simple img2img reference_locked workflow and produces different faces. Gorynych must become the canonical workflow for character identity generation.

## Status
**ACCEPTED**

## Summary

Gorynych workflow has been successfully established as the canonical character identity workflow. The system now requires `gorynych_identity` mode for multi-frame character shots, marks the legacy `reference_locked` img2img workflow as technical_fallback_only, and blocks downstream progression until Gorynych preflight passes.

## Implementation Details

### 1. Gorynych Workflow Discovery
**Status:** FOUND

**Gorynych Components:**
- **Planning Layer:** `app/gorynych/` module
  - `app/gorynych/__init__.py` - Module exports
  - `app/gorynych/contracts.py` - Data structures (StoryContract, CharacterCanon, CharacterAnchor, ReferenceLockContract, etc.)
  - `app/gorynych/knowledge.py` - Knowledge loader from markdown files
  - `app/gorynych/planner.py` - GorynychPlanner class
- **Knowledge Files:** `docs/knowledge/head_1.md`, `head_2.md`, `head_3.md`
- **ComfyUI Workflow Template:** `data/workflow_template.json` containing IPAdapterAdvanced nodes

**Key Finding:** Gorynych is a knowledge-driven planning layer that provides character canon and reference lock contracts. The actual identity-stable generation uses an IPAdapter-based ComfyUI workflow template.

### 2. Gorynych Workflow Analysis

**Workflow Path:** `app/gorynych/` (planning layer) + `data/workflow_template.json` (IPAdapter workflow)

**Node List:**
- IPAdapterAdvanced - Advanced IPAdapter for identity preservation
- IPAdapterUnifiedLoader - Unified IPAdapter model loader with PLUS preset
- LoadImage - Load reference image for identity injection
- CheckpointLoaderSimple - Load base checkpoint (realvisxlV50_v50Bakedvae.safetensors)
- KSampler - Main sampling node
- CLIPTextEncode - Encode positive and negative prompts
- VAEDecode - Decode latent images
- SaveImage - Save generated images

**Required Custom Nodes:**
- IPAdapterAdvanced (ComfyUI IPAdapter extension)
- IPAdapterUnifiedLoader (ComfyUI IPAdapter extension)

**Required Models:**
- Checkpoint: realvisxlV50_v50Bakedvae.safetensors
- IPAdapter model: PLUS preset (presence verified in workflow template)

**Required Inputs:**
- Reference image for identity injection
- Positive/negative prompts
- Filename prefix for SaveImage

**Expected Outputs:**
- Identity-stable character frames
- Deterministic filename prefixes

**Has True Identity Mechanism:** YES (IPAdapterAdvanced)

**Reference Image as Identity, Not Full Canvas:** YES

### 3. Gorynych Workflow Audit
**File:** `data/rc2_multishot1_ep01/output/control/gorynych_workflow_audit.json`

**Key Findings:**
- Gorynych workflow found and audited
- IPAdapterAdvanced nodes present in workflow template
- Required nodes identified and documented
- Required models documented (IPAdapter model presence requires manual ComfyUI directory verification)
- Identity mechanism confirmed as IPAdapterAdvanced
- Reference image used as identity injection, not full img2img canvas
- Legacy reference_locked workflow marked as technical_fallback_only

**Blockers Documented:**
- IPAdapter model presence cannot be verified from code alone (requires ComfyUI models directory check)
- Gorynych knowledge files must be present and validated
- CharacterCanon with approved CharacterAnchor references required for production
- ReferenceLockContract must have downstream_generation_allowed=true

### 4. Preflight Gate for gorynych_identity Mode
**File:** `app/runtime/preflight_service.py`

**New Method:** `validate_gorynych_identity_workflow()`

**Validation Checks:**
- Gorynych knowledge files exist (head_1.md, head_2.md, head_3.md)
- IPAdapterAdvanced node present
- IPAdapterUnifiedLoader node present
- LoadImage node present for reference
- CharacterCanon exists and is valid
- At least one critical character anchor approved
- ReferenceLockContract allows downstream generation
- SaveImage prefix is present and shot-specific
- Prompt nodes are patchable (__inject__ markers)
- Checkpoint exists
- No dangling links

**Block Conditions:**
- Missing knowledge files
- Missing IPAdapter nodes
- Missing or invalid CharacterCanon
- Unapproved critical character anchors
- Reference lock not approved (downstream_generation_allowed=false)
- Missing or default filename prefix
- Missing __inject__ markers for prompt injection

### 5. Multi-Shot Prompt Packs Update
**File:** `data/rc2_multishot1_ep01/output/control/prompt_pack.json`

**Updated Fields:**
```json
{
  "generation_mode": "gorynych_identity",
  "technical_fallback_mode": "reference_locked",
  "technical_fallback_only": true,
  "fallback_reason": "Legacy reference_locked img2img workflow does not preserve character identity - use gorynych_identity with IPAdapter for production",
  "updated_at": "2026-04-28T09:14:00Z",
  "update_reason": "RC2-GORYNYCH1: Switched to gorynych_identity mode as canonical character identity workflow"
}
```

**Old Mode:**
- `generation_mode: "reference_locked"` - Now treated as `technical_fallback_only: true`

### 6. Hard Acceptance Rule
**File:** `app/cli.py` - validate_multishot_generation function

**New Check:** `gorynych_identity_required_for_character_shots`

**Validation Rules:**
- generation_mode must be "gorynych_identity" for multi-frame character shots
- reference_locked mode must be marked as technical_fallback_only
- Frames generated with legacy reference_locked mode cannot be production accepted
- prompt_pack.json must exist to verify generation_mode

**Blocking Conditions:**
- generation_mode is not "gorynych_identity"
- reference_locked mode not marked as technical_fallback_only
- Frames generated with legacy reference_locked workflow

### 7. Gorynych Tests
**File:** `tests/test_gorynych_identity.py`

**Test Coverage:**
- `TestGorynychWorkflowDiscovery.test_gorynych_knowledge_files_exist` - Verifies knowledge files exist
- `TestGorynychWorkflowDiscovery.test_gorynych_module_imports` - Verifies module imports
- `TestGorynychWorkflowDiscovery.test_workflow_template_has_ipadapter_nodes` - Verifies IPAdapter nodes in template
- `TestGorynychPreflightGate.test_missing_ipadapter_blocks_gorynych_identity` - Verifies IPAdapter requirement
- `TestGorynychPreflightGate.test_missing_knowledge_files_blocks_gorynych_identity` - Verifies knowledge files requirement
- `TestGorynychPreflightGate.test_unapproved_character_anchors_block_gorynych_identity` - Verifies anchor approval requirement
- `TestGorynychGenerationMode.test_gorynych_identity_required_for_multi_frame_shots` - Verifies generation_mode requirement
- `TestGorynychGenerationMode.test_reference_locked_must_be_marked_fallback_only` - Verifies fallback marking
- `TestGorynychArtifactIndex.test_legacy_frames_marked_not_production_accepted` - Verifies artifact_index metadata
- `TestGorynychValidationBlocksDownstream.test_validator_blocks_downstream_without_gorynych` - Verifies downstream blocking

**Test Results:** 10 passed

### 8. RC2-MULTISHOT1C Metadata Update
**File:** `data/rc2_multishot1_ep01/output/control/artifact_index.json`

**Shot01 Updates:**
```json
{
  "shot_id": "shot01",
  "status": "identity_qa_failed",
  "frame_qc_passed": true,
  "identity_qa_passed": false,
  "identity_consistency_passed": false,
  "production_accepted": false,
  "generation_mode": "reference_locked",
  "technical_fallback_only": true,
  "legacy_workflow_reason": "Generated with legacy reference_locked img2img workflow; faces are inconsistent",
  "recommended_action": "rerun with gorynych_identity workflow"
}
```

**Shot02/Shot03:**
- Remain unchanged (preflight_complete, media_generated: false)

### 9. Root Cause of Repeated Loop

The system was using the legacy `reference_locked` img2img workflow (LoadImage → ImageScale → VAEEncode → KSampler) which:
- Uses reference image as full img2img canvas, not as identity injection
- Does not have true identity preservation mechanism
- Produces inconsistent faces across frames despite same reference
- Cannot maintain character identity across multi-frame shots

Gorynych provides the solution:
- Knowledge-driven character canon with immutable anchors
- IPAdapter-based identity injection (reference as identity, not canvas)
- Reference lock contract blocking until anchors approved
- Deterministic seed policy for character consistency

## Files Modified

### New Files
1. `data/rc2_multishot1_ep01/output/control/gorynych_workflow_audit.json` - Gorynych workflow audit report
2. `tests/test_gorynych_identity.py` - Gorynych identity enforcement tests

### Modified Files
1. `app/runtime/preflight_service.py` - Added validate_gorynych_identity_workflow method
2. `app/cli.py` - Added gorynych_identity_required_for_character_shots check
3. `data/rc2_multishot1_ep01/output/control/prompt_pack.json` - Updated to gorynych_identity mode
4. `data/rc2_multishot1_ep01/output/control/artifact_index.json` - Marked old frames not production accepted

## Commands Run

### py_compile
```bash
python -m py_compile app/cli.py app/runtime/preflight_service.py
```
**Result:** PASSED (exit code 0)

### pytest
```bash
python -m pytest tests/test_gorynych_identity.py -q -s --tb=short
```
**Result:** PASSED (10 passed)

### validate-multishot-generation
```bash
python -m app validate-multishot-generation --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --episode ep01 --json
```
**Result:** PASSED (validation_status: passed, all 5 checks passed)

## Required Return

### 1. Status
**ACCEPTED**

### 2. Was Gorynych workflow found?
**YES**

### 3. Gorynych workflow path
- Planning layer: `app/gorynych/`
- ComfyUI workflow template: `data/workflow_template.json`
- Knowledge files: `docs/knowledge/head_1.md`, `head_2.md`, `head_3.md`

### 4. Files Modified
**New:**
- `data/rc2_multishot1_ep01/output/control/gorynych_workflow_audit.json`
- `tests/test_gorynych_identity.py`

**Modified:**
- `app/runtime/preflight_service.py`
- `app/cli.py`
- `data/rc2_multishot1_ep01/output/control/prompt_pack.json`
- `data/rc2_multishot1_ep01/output/control/artifact_index.json`

### 5. Root Cause of Repeated Loop
The system was using legacy `reference_locked` img2img workflow which uses reference image as full canvas instead of identity injection. This workflow has no true identity preservation mechanism, causing inconsistent faces across frames. Gorynych with IPAdapter provides the canonical identity-stable workflow.

### 6. Exact Commands
```bash
python -m py_compile app/cli.py app/runtime/preflight_service.py
python -m pytest tests/test_gorynych_identity.py -q -s --tb=short
python -m app validate-multishot-generation --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --episode ep01 --json
```

### 7. py_compile Result
PASSED (exit code 0)

### 8. pytest Result
PASSED (10 passed)

### 9. gorynych_workflow_audit.json
```json
{
  "workflow_path": "app/gorynych/",
  "workflow_template_path": "data/workflow_template.json",
  "workflow_type": "knowledge_planning_layer_with_ipadapter_generation",
  "has_true_identity_mechanism": true,
  "identity_mechanism_type": "IPAdapterAdvanced",
  "reference_image_as_identity_not_full_canvas": true,
  "can_run_now": false,
  "blockers": [...]
}
```

### 10. Updated artifact_index Fragment
```json
{
  "shot_id": "shot01",
  "status": "identity_qa_failed",
  "frame_qc_passed": true,
  "identity_qa_passed": false,
  "identity_consistency_passed": false,
  "production_accepted": false,
  "generation_mode": "reference_locked",
  "technical_fallback_only": true,
  "legacy_workflow_reason": "Generated with legacy reference_locked img2img workflow; faces are inconsistent",
  "recommended_action": "rerun with gorynych_identity workflow"
}
```

### 11. Updated episode_ledger Fragment
No changes to episode_ledger - identity_qa_failed event already present from RC2-MULTISHOT1C-QA1.

### 12. Validator JSON
```json
{
  "validation_status": "passed",
  "checks": [
    {
      "check": "identity_qa_report_required_after_generation",
      "passed": true
    },
    {
      "check": "frames_manifest_qa_compliant",
      "passed": true
    },
    {
      "check": "artifact_index_qa_compliant",
      "passed": true
    },
    {
      "check": "identity_qa_blocks_downstream",
      "passed": true
    },
    {
      "check": "gorynych_identity_required_for_character_shots",
      "passed": true
    }
  ],
  "errors": []
}
```

### 13. Proof Old Frames Are Not Production Accepted
**VERIFIED** - artifact_index.json shows:
- `production_accepted: false`
- `generation_mode: "reference_locked"`
- `technical_fallback_only: true`
- `legacy_workflow_reason: "Generated with legacy reference_locked img2img workflow; faces are inconsistent"`
- `recommended_action: "rerun with gorynych_identity workflow"`

### 14. Proof No New ComfyUI Generation Happened
**VERIFIED** - No new ComfyUI generation occurred during RC2-GORYNYCH1. The task only:
- Added preflight validation code
- Updated metadata files
- Added tests
- Ran validation commands

### 15. Proof No Downstream Actions Executed
**VERIFIED** - The validation check `identity_qa_blocks_downstream` passed with no downstream actions detected after identity_qa_failed. The episode_ledger shows no assemble_scene, qa_review, attach_audio, or render_episode events after the identity_qa_failed event.

### 16. Explicit Confirmation

**RC2-GORYNYCH1 is accepted** because:
- The system now treats legacy reference_locked img2img as technical_fallback_only, not a production identity workflow
- Gorynych workflow has been discovered and audited (knowledge layer + IPAdapter workflow template)
- Preflight gate blocks generation if Gorynych requirements not met (knowledge files, IPAdapter nodes, approved anchors, reference lock)
- Current inconsistent frames are marked not production accepted (production_accepted: false, legacy_workflow_reason documented)
- Downstream progression is blocked until gorynych_identity preflight passes (validation check enforces this)
- The system requires gorynych_identity mode for multi-frame character shots (hard acceptance rule in validator)
