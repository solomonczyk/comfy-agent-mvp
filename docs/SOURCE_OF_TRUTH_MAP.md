# Source of Truth Map

## Best Portable Demo Zip

**Primary Demo Zip:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01.zip`
- **Purpose:** Voice demo pack with Alya character voiceover
- **Contents:** Ep01 final video with voiceover, audio assets, briefs
- **Status:** Protected, immutable
- **Size:** 320,818 bytes
- **Acceptance:** RC2-VOICE1 acceptance report

**Secondary Demo Zip:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01.zip`
- **Purpose:** Demo pack without voiceover
- **Contents:** Ep01 frames, briefs, control artifacts
- **Status:** Protected, immutable
- **Size:** 97,158 bytes
- **Acceptance:** RC2-DEMO acceptance report

## Best Media Artifact

**Best Video Artifact:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\final\ep01_final_with_voiceover.mp4`
- **Purpose:** Final video with Alya voiceover
- **Status:** Protected, immutable
- **Source:** Generated from rc2_voice1_ep01
- **Acceptance:** RC2-VOICE1 acceptance report

## Current Active Multi-Shot Root

**Active Root:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01`
- **Purpose:** Current active multi-shot episode for RC2 work
- **Status:** Active, DO NOT DELETE
- **Current State:**
  - shot01: Generated (3 frames), identity QA failed, production not accepted
  - shot02: Not generated
  - shot03: Not generated
  - Downstream: Blocked (identity_qa_blocks_downstream check passed)
  - Recommended action: route_to_character_director_and_workflow_td
- **Acceptance:** RC2-MULTISHOT1A, RC2-MULTISHOT1B, RC2-MULTISHOT1C, RC2-MULTISHOT1C-QA1 acceptance reports

## Current Accepted Role Architecture Docs

**Role Architecture:** `F:\ComfyUI\comfy-agent-mvp\docs\FILM_PRODUCTION_ROLES.md`
- **Purpose:** Defines 12 film production roles with responsibilities and blocking authority
- **Status:** Accepted, immutable
- **Acceptance:** RC2-FILMROLES1 acceptance report

**Role Responsibility Matrix:** `F:\ComfyUI\comfy-agent-mvp\docs\ROLE_RESPONSIBILITY_MATRIX.md`
- **Purpose:** Table of roles, ownership, inputs, outputs, blocking authority
- **Status:** Accepted, immutable
- **Acceptance:** RC2-FILMROLES1 acceptance report

**Pipeline Gates:** `F:\ComfyUI\comfy-agent-mvp\docs\PIPELINE_GATES.md`
- **Purpose:** Defines 11 mandatory pipeline gates with pass/fail criteria
- **Status:** Accepted, immutable
- **Acceptance:** RC2-FILMROLES1 acceptance report

## Current Validators

**CLI Validators:** `F:\ComfyUI\comfy-agent-mvp\app\cli.py`
- **validate_multishot_plan:** Validates multi-shot episode plan
- **validate_multishot_preflight:** Validates preflight artifacts
- **validate_multishot_generation:** Validates post-generation artifacts and identity QA

**Validation Rules (in validate_multishot_generation):**
- identity_qa_report_required_after_generation: Requires identity QA report after generation
- frames_manifest_qa_compliant: Validates frames manifest QA compliance
- artifact_index_qa_compliant: Validates artifact index QA compliance
- identity_qa_blocks_downstream: Blocks downstream actions after identity QA failure
- gorynych_identity_required_for_character_shots: Enforces gorynych_identity mode for multi-frame character shots
- character_director_and_workflow_td_approval_required: Requires Character Director and Workflow TD approval for identity workflow

## Current Blocked State

**Current State:** Identity QA Failed, Downstream Blocked
- **Episode:** ep01 (rc2_multishot1_ep01)
- **Shot:** shot01
- **Identity QA:** Failed (identity_consistency_passed=false)
- **Production Accepted:** False (production_accepted=false)
- **Recommended Action:** route_to_character_director_and_workflow_td
- **Downstream Actions:** Blocked (assemble_scene, qa_review, attach_audio, render_episode all blocked)
- **Blocking Authority:** Character Director and Workflow TD must approve identity workflow before downstream can proceed

**Artifact Index Fragment:**
```json
{
  "shot_id": "shot01",
  "frame_qc_passed": true,
  "identity_consistency_passed": false,
  "production_accepted": false,
  "recommended_action": "route_to_character_director_and_workflow_td"
}
```

## Deprecated/Legacy Workflows

### Legacy Reference Locked Workflow
- **Status:** Deprecated for multi-frame character shots
- **Replacement:** gorynych_identity workflow
- **Technical Fallback Only:** Allowed only if marked as technical_fallback_only
- **Acceptance:** RC2-GORYNYCH1 acceptance report

### Legacy Single-Frame Workflows
- **Status:** Deprecated for multi-shot episodes
- **Replacement:** Multi-shot workflow with gorynych_identity
- **Acceptance:** RC2-MULTISHOT1A/B/C acceptance reports

## Protected Immutable Artifacts

### Voice Demo Pack
- **Path:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01`
- **Path:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01.zip`
- **Status:** Protected, immutable
- **Acceptance:** RC2-VOICE1 acceptance report

### Voice Demo Final Video
- **Path:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\final\ep01_final_with_voiceover.mp4`
- **Status:** Protected, immutable
- **Acceptance:** RC2-VOICE1 acceptance report

### Demo Pack
- **Path:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01`
- **Path:** `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01.zip`
- **Status:** Protected, immutable
- **Acceptance:** RC2-DEMO acceptance report

### Mir Erdan Episode
- **Path:** `F:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01`
- **Status:** Protected, immutable
- **Acceptance:** Legacy demo

### External Smoke Copy
- **Path:** `F:\ComfyUI\comfy-agent-mvp\data\external_smoke\rc2_voice_demo_pack_ep01`
- **Status:** Protected, immutable
- **Purpose:** External smoke test copy

## Current Test Suite

**Test Files:**
- `tests/test_multishot_plan.py` - Multi-shot plan tests (lifecycle-aware, supports dry and post-generation states)
- `tests/test_character_consistency_qa.py` - Character consistency QA tests
- `tests/test_gorynych_identity.py` - Gorynych identity workflow tests
- `tests/test_project_hygiene.py` - Project hygiene tests (to be added in RC2-CLEANUP1)

**Test Status:** 39 passed, 0 failed (after RC2-TESTBASE1 lifecycle-aware fixes)

## Current Configuration Files

**Configuration:**
- `data/config.json` - Global configuration
- `data/workflow_template.json` - ComfyUI workflow template
- `data/voice_map.json` - Voice mapping configuration
- `data/generation_recipes.json` - Generation recipes
- `data/hardware_profiles.json` - Hardware profiles

## Current Knowledge Base

**Knowledge Files:**
- `docs/knowledge/head_1.md` - Character canon knowledge part 1
- `docs/knowledge/head_2.md` - Character canon knowledge part 2
- `docs/knowledge/head_3.md` - Character canon knowledge part 3

## Current Acceptance Reports

**RC2 Acceptance Reports:**
- `RC2_FILMROLES1B_ACCEPTANCE_REPORT.md` - Film roles regression triage
- `RC2_FILMROLES1_ACCEPTANCE_REPORT.md` - Film production roles architecture
- `RC2_GORYNYCH1_ACCEPTANCE_REPORT.md` - Gorynych identity workflow
- `RC2_MULTISHOT1A_ACCEPTANCE_REPORT.md` - Multi-shot plan creation
- `RC2_MULTISHOT1B_ACCEPTANCE_REPORT.md` - Multi-shot preflight
- `RC2_MULTISHOT1C_ACCEPTANCE_REPORT.md` - Multi-shot generation
- `RC2_MULTISHOT1C_QA1_ACCEPTANCE_REPORT.md` - Multi-shot identity QA
- `RC2_TESTBASE1_ACCEPTANCE_REPORT.md` - Test fixture lifecycle split

**RC Flow Acceptance Reports:**
- `RC_FLOW1H_ACCEPTANCE_REPORT.md` - Flow 1H acceptance
- `RC_FLOW1I_ACCEPTANCE_REPORT.md` - Flow 1I acceptance

## Legacy Roots (Do Not Use for Production)

### Real Episode Pilots (Legacy)
- `data/real_ep01_pilot` through `data/real_ep01_pilot_r7r` - Legacy pilot runs

### Real Recipe Smokes (Legacy)
- `data/real_recipe_smoke_r1` through `data/real_recipe_smoke_r3_fresh` - Legacy recipe smoke tests

### Real Reference Locked (Legacy)
- `data/real_reference_locked_alya_r1` through `data/real_reference_locked_alya_r6` - Legacy reference locked runs

### Smoke Clean Contract (Legacy)
- `data/smoke_clean_contract` through `data/smoke_clean_contract_r3` - Legacy smoke clean contract tests

### RC2 Roots (Legacy)
- `data/rc_core1_profile_proof` - RC core1 profile proof
- `data/rc2_audio1_ep01` - RC2 audio1 ep01
- `data/rc2_render1_ep01` - RC2 render1 ep01
- `data/gorynych_ep01` - Gorynych ep01

## Summary

**Source of Truth Hierarchy:**
1. Protected Demo Zips (rc2_voice_demo_pack_ep01.zip, rc2_demo_pack_ep01.zip)
2. Best Media Artifact (ep01_final_with_voiceover.mp4)
3. Active Multi-Shot Root (rc2_multishot1_ep01)
4. Role Architecture Docs (FILM_PRODUCTION_ROLES.md, ROLE_RESPONSIBILITY_MATRIX.md, PIPELINE_GATES.md)
5. Validators (CLI validation rules in app/cli.py)
6. Current Blocked State (identity QA failed, downstream blocked)
7. Deprecated Workflows (reference_locked, single-frame)

**Protected Artifacts:** 7 (frozen demos and active working roots)
**Legacy Roots:** 23 (real pilots, recipe smokes, reference locked, smoke clean contracts, RC2 roots)
**Acceptance Reports:** 8 (RC2 and RC flow acceptance reports)
