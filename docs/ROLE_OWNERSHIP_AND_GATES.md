# Role Ownership and Gates

## Overview
This document defines the 12 production roles in the comfy-agent-mvp system, their ownership of cards, inputs/outputs, blocking capabilities, handoff targets, failure conditions, and decision boundaries.

## Production Roles

### 1. Executive Producer / Product Owner

**Owns Which Cards:**
- ProjectCard
- ReleasePackageCard

**Inputs:**
- Creative brief from stakeholders
- Budget and timeline constraints
- Market requirements

**Outputs:**
- Approved ProjectCard
- Approved ReleasePackageCard
- Project-level sign-off

**Can Block Pipeline:** YES
- Can block entire project if not approved
- Can block release if quality standards not met

**Handoff Target:**
- Director / Orchestrator (for EpisodeCard creation)

**Failure Conditions:**
- Project scope undefined
- Deliverables unclear
- Budget/timeline unrealistic
- Release package fails final QA

**What the Role Must NOT Decide:**
- Creative direction (Director's responsibility)
- Technical workflow choices (Workflow TD's responsibility)
- Shot-by-shot execution decisions (Shot Designer's responsibility)
- Quality judgments on specific artifacts (QA roles' responsibility)

---

### 2. Director / Orchestrator

**Owns Which Cards:**
- EpisodeCard
- StyleCard

**Inputs:**
- Approved ProjectCard
- Creative vision
- Character roster from Character Director

**Outputs:**
- Approved EpisodeCard
- Approved StyleCard
- Route preview for pipeline state
- Handoff decisions to next role

**Can Block Pipeline:** YES
- Can block episode if narrative structure incomplete
- Can block generation if style not defined

**Handoff Target:**
- Screenwriter / Script Agent (for ScenarioCard creation)
- Shot Designer / Storyboard Agent (for ShotCard creation)

**Failure Conditions:**
- Episode narrative unclear
- Style definition insufficient
- Character roster incomplete
- Unable to resolve routing conflicts

**What the Role Must NOT Decide:**
- Character design details (Character Director's responsibility)
- Environment design (Environment Director's responsibility)
- Technical workflow parameters (Workflow TD's responsibility)
- Quality judgments on generated frames (QA roles' responsibility)

---

### 3. Screenwriter / Script Agent

**Owns Which Cards:**
- ScenarioCard

**Inputs:**
- Approved EpisodeCard
- Narrative requirements
- Character roster

**Outputs:**
- Approved ScenarioCard
- Dialogue and action descriptions
- Scene breakdown

**Can Block Pipeline:** YES
- Can block scenario if narrative beat unclear
- Can block shot design if scenario incomplete

**Handoff Target:**
- Shot Designer / Storyboard Agent (for ShotCard creation)

**Failure Conditions:**
- Narrative beat undefined
- Location description insufficient
- Character actions unclear
- Dialogue missing (if required)

**What the Role Must NOT Decide:**
- Visual composition (Shot Designer's responsibility)
- Camera angles (Cinematographer's responsibility)
- Technical generation parameters (Workflow TD's responsibility)
- Character visual design (Character Director's responsibility)

---

### 4. Shot Designer / Storyboard Agent

**Owns Which Cards:**
- ShotCard

**Inputs:**
- Approved ScenarioCard
- CharacterCard references
- EnvironmentCard references
- StyleCard references

**Outputs:**
- Approved ShotCard
- Shot composition and framing
- Action timing and blocking

**Can Block Pipeline:** YES
- Can block generation if shot undefined
- Can block workflow if references incomplete

**Handoff Target:**
- Image Generation Agent (for frame generation)

**Failure Conditions:**
- Shot type undefined
- Action description too vague
- Camera reference missing
- Duration not specified
- Required asset references missing

**What the Role Must NOT Decide:**
- Character visual design (Character Director's responsibility)
- Environment visual design (Environment Director's responsibility)
- Technical ComfyUI workflow (Workflow TD's responsibility)
- Lighting parameters (Cinematographer's responsibility)

---

### 5. Character Director

**Owns Which Cards:**
- CharacterCard
- WardrobeCard

**Inputs:**
- Character concept from Director
- Visual reference materials
- Narrative requirements

**Outputs:**
- Approved CharacterCard
- Approved WardrobeCard
- Identity consistency requirements
- Multi-shot identity approval

**Can Block Pipeline:** YES
- Can block generation if character undefined
- Can block multi-shot if identity not approved

**Handoff Target:**
- Shot Designer (for character reference in shots)
- Workflow TD (for identity workflow integration)

**Failure Conditions:**
- Visual references insufficient
- Physical description too vague
- Identity mode not specified
- Multi-shot consistency requirements unclear
- Wardrobe incomplete

**What the Role Must NOT Decide:**
- Shot composition (Shot Designer's responsibility)
- Camera angles (Cinematographer's responsibility)
- Technical workflow implementation (Workflow TD's responsibility)
- Environment design (Environment Director's responsibility)

---

### 6. Environment / Art Director

**Owns Which Cards:**
- EnvironmentCard
- PropCard

**Inputs:**
- Location requirements from Screenwriter
- Visual reference materials
- Style guidelines from Director

**Outputs:**
- Approved EnvironmentCard
- Approved PropCard
- Set dressing specifications

**Can Block Pipeline:** YES
- Can block scenario if environment undefined
- Can block shot if props missing

**Handoff Target:**
- Shot Designer (for environment reference in shots)

**Failure Conditions:**
- Visual references insufficient
- Environment description too vague
- Time of day undefined
- Props incomplete or missing references

**What the Role Must NOT Decide:**
- Shot composition (Shot Designer's responsibility)
- Character design (Character Director's responsibility)
- Lighting parameters (Cinematographer's responsibility)
- Technical workflow (Workflow TD's responsibility)

---

### 7. Cinematographer / Camera + Lighting Director

**Owns Which Cards:**
- CameraCard
- LightingCard

**Inputs:**
- Shot requirements from Shot Designer
- Style guidelines from Director
- Technical constraints

**Outputs:**
- Approved CameraCard
- Approved LightingCard
- Technical camera and lighting specifications

**Can Block Pipeline:** YES
- Can block shot if camera undefined
- Can block shot if lighting undefined

**Handoff Target:**
- Shot Designer (for camera/lighting reference in shots)
- Workflow TD (for technical integration)

**Failure Conditions:**
- Camera position undefined
- Lens parameters missing
- Lighting scheme unspecified
- Mood undefined
- Movement parameters incomplete

**What the Role Must NOT Decide:**
- Shot composition (Shot Designer's responsibility)
- Character design (Character Director's responsibility)
- Environment design (Environment Director's responsibility)
- Creative visual style (Director's responsibility)

---

### 8. Workflow TD / ComfyUI Technical Director

**Owns Which Cards:**
- WorkflowRecipeCard

**Inputs:**
- Card requirements from all roles
- Technical constraints
- Resource limitations

**Outputs:**
- Approved WorkflowRecipeCard
- ComfyUI workflow graph
- Node parameter mappings
- Technical integration specifications

**Can Block Pipeline:** YES
- Can block generation if workflow not approved
- Can block generation if workflow incomplete

**Handoff Target:**
- Image Generation Agent (for workflow execution)
- Video / Motion Agent (for video compilation workflow)

**Failure Conditions:**
- Workflow graph incomplete
- Input mappings undefined
- Output mappings missing
- Resource requirements unrealistic
- Workflow not tested

**What the Role Must NOT Decide:**
- Creative direction (Director's responsibility)
- Character design (Character Director's responsibility)
- Shot composition (Shot Designer's responsibility)
- Quality judgments on output (QA roles' responsibility)

---

### 9. Image Generation Agent

**Owns Which Cards:**
- None (execution role only)

**Inputs:**
- Approved ShotCard
- Approved asset cards (Character, Environment, etc.)
- Approved WorkflowRecipeCard
- Approved QARequirementCard

**Outputs:**
- Generated frames
- Control artifacts
- Generation metadata
- QC results

**Can Block Pipeline:** NO
- Execution role, cannot block pipeline
- Can fail generation but routing decides next step

**Handoff Target:**
- Video / Motion Agent (for video compilation)
- Back to Shot Designer if generation fails due to shot definition issues
- Back to Workflow TD if generation fails due to workflow issues

**Failure Conditions:**
- Workflow execution error
- Resource exhaustion
- Generation timeout
- Output format mismatch

**What the Role Must NOT Decide:**
- Creative quality judgments (QA roles' responsibility)
- Workflow modifications (Workflow TD's responsibility)
- Shot definition changes (Shot Designer's responsibility)

---

### 10. Video / Motion Agent

**Owns Which Cards:**
- None (execution role only)

**Inputs:**
- Generated frames from Image Generation Agent
- Generated audio from Audio/Voice Agent
- Video compilation workflow from Workflow TD

**Outputs:**
- Compiled video
- Motion graphics
- Video metadata
- Duration verification

**Can Block Pipeline:** NO
- Execution role, cannot block pipeline
- Can fail compilation but routing decides next step

**Handoff Target:**
- Editor / Final QA Supervisor (for final QA)

**Failure Conditions:**
- Frame sequence incomplete
- Audio sync failure
- Duration mismatch
- Codec errors

**What the Role Must NOT Decide:**
- Editorial decisions (Editor's responsibility)
- Creative quality judgments (QA roles' responsibility)
- Workflow modifications (Workflow TD's responsibility)

---

### 11. Audio / Voice Agent

**Owns Which Cards:**
- VoiceCard

**Inputs:**
- Approved VoiceCard
- Dialogue text from Screenwriter
- TTS engine configuration

**Outputs:**
- Generated audio files
- Audio metadata
- Timing information

**Can Block Pipeline:** YES
- Can block video compilation if audio missing

**Handoff Target:**
- Video / Motion Agent (for audio-video sync)

**Failure Conditions:**
- TTS engine unavailable
- Voice model not found
- Audio generation timeout
- Duration mismatch with dialogue

**What the Role Must NOT Decide:**
- Creative voice direction (Director's responsibility)
- Character voice personality (Character Director's responsibility)
- Editorial timing (Editor's responsibility)

---

### 12. Editor / Final QA Supervisor

**Owns Which Cards:**
- QARequirementCard

**Inputs:**
- Compiled video from Video/Motion Agent
- QA requirements from QARequirementCard
- Quality standards from Executive Producer

**Outputs:**
- QA results
- Approval/rejection decisions
- Release recommendation
- Bug reports

**Can Block Pipeline:** YES
- Can block release if QA fails
- Can block release if quality standards not met

**Handoff Target:**
- Executive Producer (for release approval)
- Back to generation roles if QA fails with specific remediation

**Failure Conditions:**
- Quality thresholds not met
- Validation rules fail
- Critical bugs found
- Duration mismatch

**What the Role Must NOT Decide:**
- Creative direction changes (Director's responsibility)
- Workflow modifications (Workflow TD's responsibility)
- Shot redefinition (Shot Designer's responsibility)

---

## Gate Definitions

### Approval Gates
Each card type has an approval gate controlled by its owning role:
- **Pending:** Card created, awaiting population
- **Draft:** Card partially populated
- **Complete:** All required fields populated
- **Approved:** Owning role has signed off
- **Rejected:** Owning role has rejected (requires revision)

### Blocking Gates
Roles can block pipeline at specific points:
- **Project Gate:** Executive Producer can block entire project
- **Episode Gate:** Director can block episode
- **Scenario Gate:** Screenwriter can block scenario
- **Shot Gate:** Shot Designer can block shot
- **Asset Gate:** Asset directors can block if assets incomplete
- **Workflow Gate:** Workflow TD can block if workflow not approved
- **QA Gate:** Editor can block release if QA fails

### Handoff Gates
Successful handoff requires:
- Source card is in "Approved" state
- All dependencies are satisfied
- Target role has received all required inputs
- Handoff is documented in orchestrator state

---

## Decision Boundaries

### Creative vs. Technical
**Creative Decisions (Role Owners):**
- Character design, environment design, style, narrative
- Shot composition, camera angles, lighting mood
- Voice direction, editorial timing

**Technical Decisions (Technical Roles):**
- Workflow graph, node parameters, resource allocation
- Camera technical specs, lighting technical parameters
- TTS engine selection, codec choices

### Quality vs. Execution
**Quality Judgments (QA Roles):**
- Whether output meets quality standards
- Whether artifacts are acceptable for release
- What constitutes failure

**Execution (Agent Roles):**
- Running workflows, compiling video, generating audio
- Technical execution only, no quality judgments

### Strategic vs. Tactical
**Strategic (Executive Producer, Director):**
- Project scope, episode structure, overall creative vision
- Release decisions, budget/timeline

**Tactical (Specialist Roles):**
- Specific asset creation, technical implementation
- Shot-by-shot execution, quality validation

---

## Conflict Resolution

### Role Conflicts
When roles disagree:
1. **Creative conflicts:** Director resolves
2. **Technical conflicts:** Workflow TD resolves
3. **Quality conflicts:** Editor resolves with Executive Producer input
4. **Blocking conflicts:** Orchestrator escalates to Director or Executive Producer

### Dependency Conflicts
When card dependencies cannot be satisfied:
1. **Missing upstream card:** Route to owning role
2. **Circular dependency:** Orchestrator detects and flags for manual resolution
3. **Resource conflict:** Executive Producer prioritizes

### Timeline Conflicts
When timeline constraints cannot be met:
1. **Resource constraints:** Executive Producer adjusts scope or resources
2. **Technical limitations:** Workflow TD proposes alternatives
3. **Quality tradeoffs:** Director and Executive Producer negotiate
