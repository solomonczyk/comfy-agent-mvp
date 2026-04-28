# Pipeline Gates

## Overview

This document defines the mandatory gates in the ComfyUI agent film production pipeline. Each gate validates that required artifacts exist, meet quality criteria, and have appropriate approvals before allowing downstream progression.

## Gate Definitions

### 1. Brief Gate

**Purpose:** Validate that the episode brief is complete, actionable, and approved by Executive Producer before any production begins.

**Required Artifacts:**
- Episode brief document
- Executive Producer approval

**Pass Criteria:**
- Episode brief contains: objectives, success criteria, budget constraints, timeline constraints, resource requirements
- Executive Producer has approved the brief
- Brief is specific enough to guide script generation

**Fail Criteria:**
- Episode brief missing or incomplete
- Executive Producer has not approved the brief
- Brief too vague to guide production

**Retry Action:**
- Revise episode brief with missing information
- Obtain Executive Producer approval
- Clarify vague sections

**Downstream Blocked Actions:**
- Script generation
- Creative direction
- Shot design
- Character canon creation
- All subsequent production activities

**Gate Owner:** Executive Producer

---

### 2. Script Gate

**Purpose:** Validate that the script is complete, coherent, and aligns with episode brief before shot design begins.

**Required Artifacts:**
- Episode script (scene-by-scene breakdown)
- Director review and approval
- Alignment with episode brief

**Pass Criteria:**
- Script contains all scenes from episode brief
- Story structure coherent (act breaks, pacing)
- Character dialogue consistent
- Scene descriptions actionable for visual production
- Director has approved the script

**Fail Criteria:**
- Script missing or incomplete
- Story structure incoherent
- Character voice inconsistent
- Scene descriptions too vague for visual execution
- Director has not approved the script

**Retry Action:**
- Revise script to address failures
- Obtain Director approval
- Clarify vague scene descriptions

**Downstream Blocked Actions:**
- Shot design
- Storyboard creation
- Character canon creation (if depends on script)
- All subsequent visual production activities

**Gate Owner:** Director

---

### 3. Shot Plan Gate

**Purpose:** Validate that shot designs are complete, technically feasible, and align with script and creative direction before workflow design begins.

**Required Artifacts:**
- Shot design specifications for all shots
- Storyboard descriptions
- Director review and approval
- Alignment with script and creative direction

**Pass Criteria:**
- Shot designs exist for all scenes in script
- Camera angles and movements specified
- Shot types appropriate for scenes
- Shot sequence supports narrative flow
- Character framing respects character canon
- Technical constraints acknowledged
- Director has approved shot plans

**Fail Criteria:**
- Shot designs missing for some scenes
- Camera angles inappropriate
- Shot sequence incoherent
- Character framing violates character canon
- Technical constraints ignored
- Director has not approved shot plans

**Retry Action:**
- Revise shot designs to address failures
- Obtain Director approval
- Consult Workflow TD for technical feasibility

**Downstream Blocked Actions:**
- Workflow TD workflow design
- Character anchor generation
- Frame generation
- All subsequent generation activities

**Gate Owner:** Director

---

### 4. Character Identity Gate

**Purpose:** Validate that character canon is defined, identity workflow is selected, and character anchors are approved before frame generation begins.

**Required Artifacts:**
- Character canon document (visual traits, personality, voice)
- Character anchor specifications (portrait, action poses, expression sheets)
- Identity workflow selection decision (Gorynych, IPAdapter, FaceID, etc.)
- Character Director approval of identity workflow
- Character Director approval of character anchors
- Character anchor reference images (approved)

**Pass Criteria:**
- Character canon defined and actionable
- Identity workflow selected and documented
- Character Director has approved identity workflow
- Character anchors specified and approved
- Character anchor reference images approved
- ReferenceLockContract has downstream_generation_allowed=true

**Fail Criteria:**
- Character canon undefined or vague
- Identity workflow not selected
- Character Director has not approved identity workflow
- Character anchors not approved
- Character anchor reference images missing or not approved
- ReferenceLockContract blocks generation

**Retry Action:**
- Define character canon with actionable specifications
- Character Director selects identity workflow
- Character Director approves identity workflow
- Generate and approve character anchor references
- Update ReferenceLockContract to allow generation

**Downstream Blocked Actions:**
- Workflow TD workflow design (cannot integrate unapproved identity workflow)
- Frame generation
- All subsequent generation activities

**Gate Owner:** Character Director

**Blocking Authority:** Character Director CAN BLOCK pipeline until identity workflow approved and anchors approved

---

### 5. Workflow Fit Gate

**Purpose:** Validate that ComfyUI workflow is structurally valid, integrates selected identity workflow, and is approved by Workflow TD before frame generation begins.

**Required Artifacts:**
- ComfyUI workflow JSON
- Workflow validation report (no dangling links, all nodes connected)
- Workflow fit report (identity workflow integrated correctly)
- Checkpoint compatibility validation
- Workflow TD approval of workflow fit

**Pass Criteria:**
- Workflow structurally valid (no dangling links, all nodes connected)
- Workflow integrates selected identity workflow correctly
- Workflow compatible with available checkpoints
- Workflow optimized for performance
- Workflow TD has approved workflow fit

**Fail Criteria:**
- Workflow structurally invalid (dangling links, disconnected nodes)
- Workflow does not integrate identity workflow
- Workflow incompatible with checkpoints
- Workflow performance unacceptable
- Workflow TD has not approved workflow fit

**Retry Action:**
- Fix workflow structure issues
- Integrate identity workflow correctly
- Select compatible checkpoint
- Optimize workflow for performance
- Obtain Workflow TD approval

**Downstream Blocked Actions:**
- Frame generation
- All subsequent generation activities

**Gate Owner:** Workflow TD

**Blocking Authority:** Workflow TD CAN BLOCK pipeline until workflow fit approved

---

### 6. Frame QC Gate

**Purpose:** Validate that generated frames meet technical quality standards before character identity QA and video assembly.

**Required Artifacts:**
- Generated frames
- Image QA report (frame_qc_passed)
- Frame metadata (seed, parameters, timing)
- Alignment with shot design specifications

**Pass Criteria:**
- All frames generated successfully
- Frame technical quality acceptable (resolution, aspect ratio, no blur/artifacts)
- Frame composition matches shot design
- Image QA passed (frame_qc_passed=true)
- Metadata recorded

**Fail Criteria:**
- Generation failures exceeding retry limit
- Frame technical quality unacceptable (blur, artifacts, distortion)
- Frame composition mismatched with shot design
- Image QA failed (frame_qc_passed=false)
- Metadata not recorded

**Retry Action:**
- Retry failed generations
- Adjust workflow parameters within approved ranges
- Consult Workflow TD for technical issues
- Regenerate failed frames

**Downstream Blocked Actions:**
- Character identity QA
- Video assembly
- All subsequent assembly activities

**Gate Owner:** Image QA

---

### 7. Character Consistency QA Gate

**Purpose:** Validate that character identity is consistent across all frames in multi-frame shots before video assembly.

**Required Artifacts:**
- Generated frames (passed Frame QC Gate)
- Character canon from Character Director
- Character anchor references (approved)
- Character QA report (character_identity_consistency_passed)
- Character Director review if identity issues detected

**Pass Criteria:**
- Character identity consistent across frames
- Generated faces match character anchors
- No character drift or identity changes
- Character QA passed (character_identity_consistency_passed=true)
- Character Director has approved character identity

**Fail Criteria:**
- Character identity inconsistent across frames
- Generated faces do not match character anchors
- Character drift or identity changes detected
- Character QA failed (character_identity_consistency_passed=false)
- Character Director has not approved character identity

**Retry Action:**
- Regenerate frames with identity workflow adjustments
- Consult Character Director for identity workflow re-selection
- Character Director may select different identity workflow
- Update character anchors if needed

**Downstream Blocked Actions:**
- Video assembly
- Audio generation
- Scene assembly
- All subsequent assembly activities

**Gate Owner:** Character QA

**Blocking Authority:** Character QA CAN BLOCK pipeline if character identity consistency failed

---

### 8. Video Motion Gate

**Purpose:** Validate that video assembly, motion effects, and temporal coherence meet quality standards before audio integration.

**Required Artifacts:**
- Assembled video sequence
- Motion quality report
- Temporal coherence validation
- Alignment with shot design specifications

**Pass Criteria:**
- Video sequence assembled correctly
- Motion quality acceptable
- Temporal coherence maintained
- Frame rate and timing meet specifications
- Motion effects appropriate

**Fail Criteria:**
- Video assembly failed
- Motion quality unacceptable
- Temporal coherence broken
- Frame rate or timing mismatched
- Motion effects inappropriate

**Retry Action:**
- Reassemble video sequence
- Adjust motion smoothing parameters
- Fix temporal coherence issues
- Consult Director for creative guidance

**Downstream Blocked Actions:**
- Audio integration
- Scene assembly
- All subsequent assembly activities

**Gate Owner:** Video Agent

---

### 9. Audio Fit Gate

**Purpose:** Validate that voice, music, and sound effects fit the scene, character canon, and are synchronized with video before scene assembly.

**Required Artifacts:**
- Voice audio tracks
- Background music tracks
- Sound effect tracks
- Audio quality report
- Synchronization validation
- Character canon alignment (voice characteristics)

**Pass Criteria:**
- Voice matches character canon
- Music fits scene atmosphere
- Sound effects appropriate
- Audio synchronized with video
- Audio quality meets specifications

**Fail Criteria:**
- Voice does not match character canon
- Music inappropriate for scene
- Sound effects inappropriate
- Audio not synchronized
- Audio quality below specifications

**Retry Action:**
- Regenerate voice with adjusted parameters
- Select different background music
- Select different sound effects
- Adjust synchronization timing

**Downstream Blocked Actions:**
- Scene assembly
- Final QA
- Release

**Gate Owner:** Audio Agent

---

### 10. Assembly Gate

**Purpose:** Validate that final scene assembly (video + audio) meets creative direction and script requirements before final QA.

**Required Artifacts:**
- Assembled scene (video + audio)
- Scene quality report
- Timing and pacing validation
- Alignment with script and creative direction
- Director review and approval

**Pass Criteria:**
- Scene assembled correctly
- Transitions appropriate
- Timing matches script
- Scene flows according to creative direction
- Director has approved assembled scene

**Fail Criteria:**
- Scene assembly failed
- Transitions inappropriate
- Timing mismatched with script
- Scene does not flow according to creative direction
- Director has not approved assembled scene

**Retry Action:**
- Reassemble scene
- Adjust transitions
- Fix timing issues
- Consult Director for creative guidance

**Downstream Blocked Actions:**
- Final QA
- Release

**Gate Owner:** Editor

---

### 11. Final Release Gate

**Purpose:** Validate that all gates have passed, all roles have completed responsibilities, and the episode meets release criteria before final release.

**Required Artifacts:**
- Assembled episode
- All gate reports (Brief, Script, Shot Plan, Character Identity, Workflow Fit, Frame QC, Character Consistency QA, Video Motion, Audio Fit, Assembly)
- All role completion reports
- Final QA report
- Release criteria validation
- Executive Producer final approval

**Pass Criteria:**
- All 10 gates passed
- All roles completed responsibilities
- Episode meets release criteria
- Final technical quality acceptable
- Final creative quality acceptable
- Executive Producer has approved release

**Fail Criteria:**
- Gates failed without resolution
- Roles not completed responsibilities
- Episode does not meet release criteria
- Final technical quality unacceptable
- Final creative quality unacceptable
- Executive Producer has not approved release

**Retry Action:**
- Address failed gates
- Ensure roles complete responsibilities
- Revise episode to meet release criteria
- Improve technical or creative quality
- Obtain Executive Producer approval

**Downstream Blocked Actions:**
- Release to distribution
- All post-release activities

**Gate Owner:** Final QA

**Blocking Authority:** Final QA CAN BLOCK release until all criteria met

---

## Gate Sequence

1. **Brief Gate** → Script Gate → Shot Plan Gate → Character Identity Gate → Workflow Fit Gate
2. **Workflow Fit Gate** → Frame Generation (not a gate, but production step)
3. **Frame Generation** → Frame QC Gate → Character Consistency QA Gate
4. **Character Consistency QA Gate** → Video Motion Gate → Audio Fit Gate
5. **Audio Fit Gate** → Assembly Gate → Final Release Gate

## Critical Blocking Gates

**Gates that can block the entire pipeline:**
- Character Identity Gate (Character Director)
- Workflow Fit Gate (Workflow TD)
- Character Consistency QA Gate (Character QA)
- Final Release Gate (Final QA)

These gates have explicit blocking authority and can prevent downstream progression until their criteria are met.

## Gate Failures and Escalation

**Gate Failure Handling:**
1. Gate fails → Retry action executed
2. Retry fails → Escalate to gate owner
3. Escalation fails → Escalate to Executive Producer
4. Unresolved critical gate failure → Pipeline blocked, episode halted

**Escalation Paths:**
- Script Gate → Director → Executive Producer
- Shot Plan Gate → Director → Executive Producer
- Character Identity Gate → Character Director → Executive Producer
- Workflow Fit Gate → Workflow TD → Director → Executive Producer
- Frame QC Gate → Image QA → Workflow TD → Director
- Character Consistency QA Gate → Character QA → Character Director → Executive Producer
- Video Motion Gate → Video Agent → Director
- Audio Fit Gate → Audio Agent → Director
- Assembly Gate → Editor → Director
- Final Release Gate → Final QA → Executive Producer
