# Role Responsibility Matrix

## Overview

This matrix defines what each role owns, their inputs, outputs, pipeline blocking authority, and handoff targets in the ComfyUI agent film production system.

## Responsibility Matrix

| Role | Owns | Inputs | Outputs | Can Block Pipeline? | Handoff Target |
|------|-------|--------|---------|---------------------|----------------|
| Executive Producer / Product Owner | Episode vision, budget, timeline, final release decision | Episode brief from stakeholders, budget/timeline constraints, resource availability, Final QA report, Release candidate | Approved episode plan, Resource allocation decisions, Final release approval/rejection, Production status reports | YES - Episode approval, Final release | Director, Final QA |
| Director / Orchestrator | Creative direction, role coordination, shot-to-shot consistency | Episode brief, Script, Shot plans, Character canon, Workflow fit report, QA reports | Creative direction document, Shot sequence decisions, Coordination decisions, Escalation requests, Production status updates | YES - Can pause production for creative review | Screenwriter, Shot Designer, Character Director, Workflow TD, Executive Producer |
| Screenwriter / Script Agent | Narrative content, dialogue, scene descriptions | Episode brief, Creative direction, Character canon, Feedback | Episode script, Character dialogue, Scene descriptions, Story structure documentation | NO - Can escalate to Director | Shot Designer, Director |
| Shot Designer / Storyboard Agent | Shot composition, camera angles, visual specifications | Script, Creative direction, Character canon, Technical constraints | Shot design specifications, Camera angle descriptions, Storyboard descriptions, Shot sequence recommendations | NO - Can escalate to Director | Workflow TD, Director |
| Character Director | Character identity consistency, identity workflow selection, character anchors | Episode brief, Creative direction, Script, Character design concepts, Available identity workflows, Generated frames for QA | Character canon, Character anchor specifications, Identity workflow selection, Anchor approval/rejection, Character consistency QA requests, Character identity approval/rejection | YES - Can block generation until identity workflow approved and anchors approved | Workflow TD, Image QA, Executive Producer |
| Workflow TD / ComfyUI Technical Director | ComfyUI workflow implementation, node graph design, workflow fit | Identity workflow selection, Shot design specifications, Available checkpoints/models, Technical constraints, Character anchor paths | ComfyUI workflow JSON, Workflow validation report, Workflow fit approval/rejection, Optimization recommendations, Troubleshooting reports | YES - Can block generation until workflow fit approved | Image Generation Agent, Character Director |
| Image Generation Agent | ComfyUI workflow execution, frame generation, generation metadata | Approved workflow, Shot design specifications, Character anchor paths, Prompt pack, Technical constraints | Generated frames, Generation metadata, Error reports, Frame collection for QA | NO - Can retry failed generations | Image QA |
| Image QA / Character QA | Frame technical quality, character identity consistency | Generated frames, Shot design specifications, Character canon, Character anchors, Technical quality criteria | Image QA report (frame_qc_passed), Character QA report (character_identity_consistency_passed), Frame approval/rejection, Identity approval/rejection, Escalation requests | YES - Can block downstream if character identity QA fails | Video Agent, Character Director |
| Video / Motion Agent | Video assembly, motion effects, temporal coherence | Approved frames, Shot design specifications, Motion requirements, Frame rate/timing specifications | Assembled video sequence, Motion quality report, Temporal coherence validation | NO - Can escalate to Director | Editor |
| Audio / Voice Agent | Voice generation, music selection, sound effects, audio synchronization | Character canon (voice), Script (dialogue), Scene atmosphere, Video sequence, Audio quality specifications | Voice audio tracks, Background music, Sound effects, Mixed audio synchronized with video, Audio quality report | NO - Can escalate to Director | Editor |
| Editor / Assembly Agent | Scene assembly, transitions, timing and pacing | Video sequences, Audio tracks, Script, Creative direction, Assembly specifications | Assembled scene (video + audio), Scene quality report, Timing/pacing validation | NO - Can escalate to Director | Final QA |
| Final QA / Release Gate | Final quality assurance, release validation | Assembled episode, All gate reports, All role completion reports, Release criteria, Final QA criteria | Final QA report, Release recommendation (approve/reject), Revision requests, Final episode artifact | YES - Can block release until all criteria met | Executive Producer |

## Blocking Authority Summary

**Roles with pipeline blocking authority:**
- Executive Producer - Episode approval, Final release
- Director - Can pause production for creative review
- Character Director - Generation until identity workflow approved and anchors approved
- Workflow TD - Generation until workflow fit approved
- Character QA - Downstream if character identity consistency failed
- Final QA - Release until all criteria met

**Roles without pipeline blocking authority (escalation only):**
- Screenwriter - Escalates to Director
- Shot Designer - Escalates to Director
- Image Generation Agent - Escalates to Workflow TD
- Video Agent - Escalates to Director
- Audio Agent - Escalates to Director
- Editor - Escalates to Director

## Handoff Flow

1. Executive Producer → Director (episode approval)
2. Director → Screenwriter (creative direction)
3. Screenwriter → Shot Designer (script)
4. Shot Designer → Workflow TD (shot design specifications)
5. Character Director → Workflow TD (identity workflow selection, character anchors)
6. Workflow TD → Image Generation Agent (approved workflow)
7. Image Generation Agent → Image QA (generated frames)
8. Image QA → Video Agent (approved frames)
9. Character QA → Video Agent (character identity approval) - BLOCKS if failed
10. Video Agent → Editor (video sequence)
11. Audio Agent → Editor (audio tracks)
12. Editor → Final QA (assembled scene)
13. Final QA → Executive Producer (release recommendation) - BLOCKS if failed

## Decision Boundaries

**Character Director decisions:**
- Character visual identity specifications
- Identity workflow selection (Gorynych, IPAdapter, FaceID, etc.)
- Character anchor approval
- Character identity approval/rejection for frames

**Workflow TD decisions:**
- ComfyUI workflow node graph design
- Node parameter values and ranges
- Workflow optimization strategies
- Checkpoint selection for workflow fit
- Workflow fit approval/rejection

**Separation of concerns:**
- Character Director owns identity workflow selection (NOT technical implementation)
- Workflow TD owns technical implementation (NOT identity workflow selection)
- This separation prevents the repeated loop where technical fixes are applied without character identity consideration
