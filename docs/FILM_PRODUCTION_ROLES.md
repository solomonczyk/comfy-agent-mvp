# Film Production Roles for ComfyUI Agent System

## Overview

This document defines the film-production role architecture for the ComfyUI agent system. Each role has clear responsibilities, decision authority, and blocking power to ensure quality control at each stage of production.

## Role Definitions

### 1. Executive Producer / Product Owner

**Purpose:**
Owns the overall episode vision, budget, timeline, and final release decision. Responsible for ensuring the production meets creative and technical standards.

**Responsibilities:**
- Define episode objectives and success criteria
- Approve or reject overall episode plan
- Allocate resources (checkpoint selection, budget constraints)
- Make final release decision
- Escalate critical production blockers
- Ensure compliance with production standards

**Inputs:**
- Episode brief from external stakeholders
- Budget and timeline constraints
- Resource availability (checkpoints, compute)
- Final QA report
- Release candidate

**Outputs:**
- Approved episode plan
- Resource allocation decisions
- Final release approval or rejection
- Production status reports

**Allowed to Decide:**
- Episode approval or rejection
- Resource allocation priorities
- Timeline adjustments
- Final release decision

**NOT Allowed to Decide:**
- Specific shot composition
- Character design details
- Workflow technical implementation
- Individual frame acceptance
- Audio/music selection

**Acceptance Criteria:**
- Episode plan meets creative objectives
- All gates passed
- Budget within constraints
- Timeline achievable
- Final QA passed

**Failure Conditions:**
- Episode plan does not meet objectives
- Critical gates failed without resolution
- Budget/timeline constraints violated
- Stakeholder rejection of final product

---

### 2. Director / Orchestrator

**Purpose:**
Orchestrates the overall production pipeline, coordinates between roles, and ensures creative vision is executed consistently across all shots.

**Responsibilities:**
- Translate episode brief into creative direction
- Coordinate between all production roles
- Ensure shot-to-shot consistency
- Resolve creative conflicts between roles
- Monitor pipeline progress and blockers
- Make creative escalation decisions

**Inputs:**
- Episode brief from Executive Producer
- Script from Screenwriter
- Shot plans from Shot Designer
- Character canon from Character Director
- Workflow fit report from Workflow TD
- QA reports from Image QA and Character QA

**Outputs:**
- Creative direction document
- Shot sequence and pacing decisions
- Coordination decisions between roles
- Escalation requests to Executive Producer
- Production status updates

**Allowed to Decide:**
- Creative direction interpretation
- Shot sequencing and pacing
- Which creative conflicts to escalate
- When to pause production for creative review
- Handoff timing between roles

**NOT Allowed to Decide:**
- Technical workflow implementation
- Specific checkpoint selection
- Individual frame technical quality
- Audio/music technical details
- Final release decision

**Acceptance Criteria:**
- Creative direction aligns with episode brief
- All roles coordinated effectively
- Shot-to-shot consistency maintained
- No unresolved creative conflicts
- Pipeline progressing without creative blockers

**Failure Conditions:**
- Creative direction misaligned with brief
- Roles uncoordinated causing production delays
- Shot-to-shot inconsistency detected
- Creative conflicts unresolved blocking production

---

### 3. Screenwriter / Script Agent

**Purpose:**
Generates narrative content, dialogue, and scene descriptions that guide visual production. Ensures story structure and character development are coherent.

**Responsibilities:**
- Generate episode script from high-level concept
- Write dialogue and character actions
- Define scene locations and atmosphere
- Ensure story structure (act breaks, pacing)
- Maintain character voice consistency
- Revise script based on feedback

**Inputs:**
- Episode brief from Executive Producer
- Creative direction from Director
- Character canon from Character Director
- Feedback from Director and Executive Producer

**Outputs:**
- Episode script (scene-by-scene breakdown)
- Character dialogue and actions
- Scene descriptions and atmosphere notes
- Story structure documentation

**Allowed to Decide:**
- Narrative structure and pacing
- Character dialogue and actions
- Scene descriptions and atmosphere
- Script revisions based on feedback

**NOT Allowed to Decide:**
- Visual composition of shots
- Character visual design
- Technical workflow implementation
- Audio/music selection
- Frame-by-frame visual execution

**Acceptance Criteria:**
- Script meets episode brief objectives
- Story structure coherent
- Character voice consistent
- Scene descriptions actionable for visual production
- Feedback incorporated appropriately

**Failure Conditions:**
- Script misaligned with episode brief
- Story structure incoherent
- Character voice inconsistent
- Scene descriptions too vague for visual execution

---

### 4. Shot Designer / Storyboard Agent

**Purpose:**
Translates script and creative direction into specific shot compositions, camera angles, and visual specifications for each scene.

**Responsibilities:**
- Design shot compositions from script
- Define camera angles and movements
- Specify shot types (wide, medium, close-up, etc.)
- Create storyboard descriptions for each shot
- Ensure shot sequence supports narrative flow
- Coordinate with Character Director for character framing

**Inputs:**
- Script from Screenwriter
- Creative direction from Director
- Character canon from Character Director
- Technical constraints from Workflow TD

**Outputs:**
- Shot design specifications
- Camera angle and movement descriptions
- Storyboard descriptions
- Shot sequence recommendations

**Allowed to Decide:**
- Shot composition and framing
- Camera angles and movements
- Shot type selection
- Visual storytelling approach

**NOT Allowed to Decide:**
- Character visual identity design
- Technical workflow implementation
- Checkpoint selection
- Individual frame generation parameters
- Audio/music selection

**Acceptance Criteria:**
- Shot designs support narrative flow
- Camera angles appropriate for scene
- Shot sequence coherent
- Character framing respects character canon
- Technical constraints acknowledged

**Failure Conditions:**
- Shot designs conflict with script
- Camera angles inappropriate
- Shot sequence incoherent
- Character framing violates character canon
- Technical constraints ignored

---

### 5. Character Director

**Purpose:**
Owns character identity consistency across all frames and shots. Selects and approves character identity workflow (Gorynych, IPAdapter, FaceID, etc.) and ensures character anchors are established and maintained.

**Responsibilities:**
- Define character canon (visual traits, personality, voice)
- Create character anchor specifications (portrait, action poses, expression sheets)
- Select approved character identity workflow for production
- Approve character anchor references before generation
- Monitor character consistency across generated frames
- Request character consistency QA for all multi-frame shots
- Approve or reject character identity in generated frames

**Inputs:**
- Episode brief from Executive Producer
- Creative direction from Director
- Script from Screenwriter
- Character design concepts
- Available identity workflows (Gorynych, IPAdapter, FaceID, etc.)
- Generated frames for character consistency QA

**Outputs:**
- Character canon document
- Character anchor specifications
- Identity workflow selection decision
- Character anchor approval/rejection
- Character consistency QA requests
- Character identity approval/rejection for frames

**Allowed to Decide:**
- Character visual identity specifications
- Which identity workflow to use (Gorynych, IPAdapter, FaceID, etc.)
- Character anchor approval
- Character consistency QA criteria
- Character identity approval/rejection for frames
- **CAN BLOCK pipeline** until identity workflow approved and anchors approved

**NOT Allowed to Decide:**
- Technical workflow implementation details
- Checkpoint selection
- Individual frame technical quality
- Audio/music selection
- Final release decision

**Acceptance Criteria:**
- Character canon defined and actionable
- Identity workflow selected and documented
- Character anchors approved before generation
- Character consistency maintained across frames
- Character identity QA criteria met

**Failure Conditions:**
- Character canon undefined or vague
- Identity workflow not selected
- Character anchors not approved before generation
- Character identity inconsistent across frames
- Character identity QA failed without remediation

---

### 6. Workflow TD / ComfyUI Technical Director

**Purpose:**
Owns the technical ComfyUI workflow implementation, node graph design, and workflow fit for the selected identity workflow. Ensures workflows are valid, efficient, and compatible with available resources.

**Responsibilities:**
- Design ComfyUI workflow node graphs
- Integrate selected identity workflow (Gorynych, IPAdapter, FaceID, etc.) into ComfyUI
- Validate workflow structure and connectivity
- Optimize workflow for performance and quality
- Ensure checkpoint compatibility
- Approve workflow fit before generation
- Monitor workflow execution and troubleshoot issues

**Inputs:**
- Identity workflow selection from Character Director
- Shot design specifications from Shot Designer
- Available checkpoints and models
- Technical constraints (compute, memory)
- Character anchor paths from Character Director

**Outputs:**
- ComfyUI workflow JSON
- Workflow validation report
- Workflow fit approval/rejection
- Workflow optimization recommendations
- Troubleshooting reports

**Allowed to Decide:**
- ComfyUI workflow node graph design
- Node parameter values and ranges
- Workflow optimization strategies
- Checkpoint selection for workflow fit
- Workflow fit approval/rejection
- **CAN BLOCK pipeline** until workflow fit approved

**NOT Allowed to Decide:**
- Character visual identity
- Shot composition and framing
- Character identity workflow selection (owned by Character Director)
- Audio/music selection
- Final release decision

**Acceptance Criteria:**
- Workflow structurally valid (no dangling links, all nodes connected)
- Workflow integrates selected identity workflow correctly
- Workflow compatible with available checkpoints
- Workflow optimized for performance
- Workflow fit approved before generation

**Failure Conditions:**
- Workflow structurally invalid
- Workflow does not integrate identity workflow
- Workflow incompatible with checkpoints
- Workflow performance unacceptable
- Workflow fit not approved before generation

---

### 7. Image Generation Agent

**Purpose:**
Executes ComfyUI workflow to generate individual frames based on approved shot designs, character anchors, and workflow configuration. Operates within technical constraints defined by Workflow TD.

**Responsibilities:**
- Submit ComfyUI workflows for execution
- Inject shot-specific prompts and parameters
- Use approved character anchors as inputs
- Monitor generation progress
- Handle generation errors and retries
- Collect generated frames for QA

**Inputs:**
- Approved ComfyUI workflow from Workflow TD
- Shot design specifications from Shot Designer
- Character anchor paths from Character Director
- Prompt pack with shot-specific prompts
- Technical constraints from Workflow TD

**Outputs:**
- Generated frame images
- Generation metadata (seed, parameters, timing)
- Generation error reports
- Frame collection for QA

**Allowed to Decide:**
- When to retry failed generations
- Generation parameter adjustments within approved ranges
- Error handling strategies

**NOT Allowed to Decide:**
- Workflow node graph design
- Character identity workflow selection
- Checkpoint selection
- Shot composition or framing
- Frame approval or rejection

**Acceptance Criteria:**
- All frames generated successfully
- Generation metadata recorded
- Errors handled with appropriate retries
- Frames delivered to QA

**Failure Conditions:**
- Generation failures exceeding retry limit
- Metadata not recorded
- Errors not handled appropriately
- Frames not delivered to QA

---

### 8. Image QA / Character QA

**Purpose:**
Performs quality assurance on generated frames. Image QA checks technical quality (resolution, artifacts, visual defects). Character QA checks character identity consistency across frames.

**Responsibilities:**

**Image QA:**
- Validate frame technical quality (resolution, aspect ratio)
- Detect visual defects (blur, artifacts, noise, distortion)
- Check for composition issues
- Approve or reject frames based on technical criteria

**Character QA:**
- Validate character identity consistency across frames
- Compare generated faces to character anchors
- Detect character drift or identity changes
- Approve or reject character identity in frames
- Request Character Director review if identity issues detected

**Inputs:**
- Generated frames from Image Generation Agent
- Shot design specifications from Shot Designer
- Character canon from Character Director
- Character anchors from Character Director
- Technical quality criteria

**Outputs:**
- Image QA report (frame_qc_passed)
- Character QA report (character_identity_consistency_passed)
- Frame approval/rejection
- Character identity approval/rejection
- Escalation requests to Character Director

**Allowed to Decide:**
- Frame technical quality approval/rejection
- Character identity consistency approval/rejection
- When to escalate to Character Director
- **CAN BLOCK pipeline** if character identity QA fails

**NOT Allowed to Decide:**
- Workflow node graph design
- Character identity workflow selection
- Checkpoint selection
- Shot composition or framing
- Audio/music selection

**Acceptance Criteria:**
- Image QA criteria met for all frames
- Character identity consistent across frames
- QA reports documented
- Escalations handled appropriately

**Failure Conditions:**
- Image QA failed (technical defects)
- Character identity inconsistent
- QA reports not documented
- Character identity issues not escalated

---

### 9. Video / Motion Agent

**Purpose:**
Assembles generated frames into video sequences, applies motion effects, and ensures temporal coherence across the shot.

**Responsibilities:**
- Assemble frames into video sequence
- Apply motion smoothing or interpolation if needed
- Ensure temporal coherence (no jarring jumps)
- Validate video playback quality
- Handle frame rate and timing

**Inputs:**
- Approved frames from Image QA
- Shot design specifications from Shot Designer
- Motion requirements from Director
- Frame rate and timing specifications

**Outputs:**
- Assembled video sequence
- Motion quality report
- Temporal coherence validation

**Allowed to Decide:**
- Motion smoothing parameters
- Interpolation strategies
- Temporal coherence adjustments

**NOT Allowed to Decide:**
- Frame generation parameters
- Character identity workflow
- Audio/music selection
- Final release decision

**Acceptance Criteria:**
- Video sequence assembled correctly
- Motion quality acceptable
- Temporal coherence maintained
- Playback quality meets specifications

**Failure Conditions:**
- Video assembly failed
- Motion quality unacceptable
- Temporal coherence broken
- Playback quality below specifications

---

### 10. Audio / Voice Agent

**Purpose:**
Generates or selects audio content (voice, music, sound effects) that fits the scene and character voice. Ensures audio quality and synchronization with video.

**Responsibilities:**
- Generate voice audio matching character voice specifications
- Select background music fitting scene atmosphere
- Add sound effects for action and environment
- Ensure audio synchronization with video
- Validate audio quality

**Inputs:**
- Character canon from Character Director (voice characteristics)
- Script from Screenwriter (dialogue)
- Scene atmosphere from Shot Designer
- Video sequence from Video Agent
- Audio quality specifications

**Outputs:**
- Voice audio tracks
- Background music tracks
- Sound effect tracks
- Mixed audio synchronized with video
- Audio quality report

**Allowed to Decide:**
- Voice generation parameters within character canon
- Music selection within atmosphere constraints
- Sound effect selection
- Audio mix balance

**NOT Allowed to Decide:**
- Character voice specifications (owned by Character Director)
- Visual frame generation
- Final release decision

**Acceptance Criteria:**
- Voice matches character canon
- Music fits scene atmosphere
- Audio synchronized with video
- Audio quality meets specifications

**Failure Conditions:**
- Voice does not match character canon
- Music inappropriate for scene
- Audio not synchronized
- Audio quality below specifications

---

### 11. Editor / Assembly Agent

**Purpose:**
Assembles video and audio into final scene, applies transitions and timing adjustments, and ensures the assembled scene matches the director's creative vision.

**Responsibilities:**
- Assemble video and audio into final scene
- Apply transitions between shots
- Adjust timing and pacing
- Ensure scene flows according to script
- Validate assembled scene quality

**Inputs:**
- Video sequences from Video Agent
- Audio tracks from Audio Agent
- Script from Screenwriter
- Creative direction from Director
- Scene assembly specifications

**Outputs:**
- Assembled scene (video + audio)
- Scene quality report
- Timing and pacing validation

**Allowed to Decide:**
- Transition selection and parameters
- Timing and pacing adjustments
- Scene assembly order

**NOT Allowed to Decide:**
- Frame generation parameters
- Character identity workflow
- Audio/music selection (owned by Audio Agent)
- Final release decision

**Acceptance Criteria:**
- Scene assembled correctly
- Transitions appropriate
- Timing matches script
- Scene flows according to creative direction

**Failure Conditions:**
- Scene assembly failed
- Transitions inappropriate
- Timing mismatched with script
- Scene does not flow according to creative direction

---

### 12. Final QA / Release Gate

**Purpose:**
Performs final quality assurance on the complete assembled episode. Validates that all gates have passed, all roles have completed their responsibilities, and the episode meets release criteria.

**Responsibilities:**
- Validate all production gates passed
- Verify all role responsibilities completed
- Check episode against release criteria
- Perform final technical quality check
- Perform final creative quality check
- Recommend release or request revisions
- Document final QA report

**Inputs:**
- Assembled episode from Editor
- All gate reports
- All role completion reports
- Release criteria from Executive Producer
- Final QA criteria

**Outputs:**
- Final QA report
- Release recommendation (approve/reject)
- Revision requests if needed
- Final episode artifact

**Allowed to Decide:**
- Final QA pass/fail
- Release recommendation
- Revision requests
- **CAN BLOCK release** until all criteria met

**NOT Allowed to Decide:**
- Individual role decisions
- Workflow implementation
- Creative direction interpretation
- Budget/timeline adjustments

**Acceptance Criteria:**
- All gates passed
- All roles completed responsibilities
- Episode meets release criteria
- Final technical quality acceptable
- Final creative quality acceptable

**Failure Conditions:**
- Gates failed without resolution
- Roles not completed responsibilities
- Episode does not meet release criteria
- Final technical quality unacceptable
- Final creative quality unacceptable

---

## Role Interaction Flow

1. **Executive Producer** approves episode plan
2. **Director** coordinates creative direction
3. **Screenwriter** generates script
4. **Shot Designer** designs shots from script
5. **Character Director** defines character canon and selects identity workflow
6. **Workflow TD** designs ComfyUI workflow integrating identity workflow
7. **Image Generation Agent** generates frames
8. **Image QA** validates technical quality
9. **Character QA** validates character identity consistency
10. **Video Agent** assembles video sequences
11. **Audio Agent** generates audio tracks
12. **Editor** assembles final scene
13. **Final QA** validates complete episode for release

## Blocking Authority

Roles with pipeline blocking authority:
- **Executive Producer** - Can block episode approval, final release
- **Character Director** - Can block generation until identity workflow approved and anchors approved
- **Workflow TD** - Can block generation until workflow fit approved
- **Image QA** - Can block downstream if frame technical quality failed
- **Character QA** - Can block downstream if character identity consistency failed
- **Final QA** - Can block release until all criteria met
