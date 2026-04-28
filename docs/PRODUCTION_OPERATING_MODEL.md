# Production Operating Model

## Overview

The comfy-agent-mvp system is an automated film production pipeline that orchestrates ComfyUI workflows for consistent character generation and video production. This document defines the operating model that prevents repeated generation loops through clear separation of concerns, role ownership, and gated workflows.

## What the System is Building

The system builds **animated film content** from creative intent to release-ready artifacts. This includes:
- Character-consistent visual shots
- Voiceover-integrated audio
- Compiled video sequences
- Release packages for distribution

## Core Concepts

### Project
A complete creative work (e.g., "Mir Erdan Chronicles"). Contains one or more episodes.
- **Owner:** Executive Producer / Product Owner
- **Scope:** Entire production lifecycle
- **Deliverable:** Release package(s)

### Episode
A narrative unit within a project (e.g., "Episode 1: The Awakening"). Contains one or more scenarios.
- **Owner:** Director / Orchestrator
- **Scope:** Complete narrative arc
- **Deliverable:** Episode-level release package

### Scenario
A narrative segment within an episode (e.g., "Mir discovers the artifact"). Contains one or more shots.
- **Owner:** Screenwriter / Script Agent
- **Scope:** Narrative beat or scene
- **Deliverable:** Scenario storyboard and shot list

### Shot
A single continuous camera take (e.g., "Medium shot of Mir examining artifact"). The atomic unit of generation.
- **Owner:** Shot Designer / Storyboard Agent
- **Scope:** Single camera angle and action
- **Deliverable:** Generated frames, audio, video

### Asset
A reusable creative element that exists across shots (e.g., "Mir character design", "Forest environment").
- **Owner:** Various (Character Director, Environment Director, etc.)
- **Scope:** Reusable across multiple shots
- **Deliverable:** Asset card with references

### Artifact
A generated output file (frame, audio, video, control data).
- **Owner:** Generation agents
- **Scope:** Specific to a shot
- **Deliverable:** Binary output files

## Film Production Flow

### Phase 1: Pre-Production
1. **Project Card** created by Executive Producer
2. **Episode Cards** created by Director
3. **Scenario Cards** created by Screenwriter
4. **Shot Cards** created by Shot Designer
5. **Asset Cards** created by respective directors (Character, Environment, etc.)

### Phase 2: Asset Preparation
1. **CharacterCard** populated with references (Character Director)
2. **EnvironmentCard** populated with references (Environment Director)
3. **LightingCard** defined (Cinematographer)
4. **CameraCard** defined (Cinematographer)
5. **StyleCard** defined (Director)
6. **WardrobeCard** populated (Wardrobe/Character Director)
7. **PropCard** populated (Prop Master/Environment Director)

### Phase 3: Workflow Approval
1. **WorkflowRecipeCard** created and approved (Workflow TD)
2. **QARequirementCard** defined (QA Supervisor)
3. All cards validated against requirements

### Phase 4: Generation
1. **VoiceCard** executed (Audio/Voice Agent)
2. **Image Generation Agent** executes workflow
3. Frames generated and QC'd
4. Identity QA performed

### Phase 5: Post-Production
1. **Video/Motion Agent** compiles video
2. **Editor** performs final QA
3. **ReleasePackageCard** assembled
4. Release published

## Role of Orchestrator

### What the Orchestrator Is
The orchestrator is a **routing and gatekeeping system**, not a creative decision-maker. It:
- Reads all production cards
- Determines which cards are complete vs. missing
- Identifies blocked states
- Routes work to the appropriate role
- Prevents downstream execution when prerequisites are not met
- Provides route preview showing what work is pending

### What the Orchestrator Is Allowed to Decide
- **Routing decisions:** Which role should receive next work item
- **Blocking decisions:** Whether downstream work can proceed
- **Validation checks:** Whether cards meet schema and reference requirements
- **State transitions:** When a card moves from pending to complete

### What the Orchestrator Is NOT Allowed to Decide
- **Creative decisions:** Character design, environment style, camera angles, etc.
- **Technical workflow choices:** Which ComfyUI nodes to use, parameter values
- **Quality judgments:** Whether a frame is "good enough" artistically
- **Narrative decisions:** Story structure, dialogue, pacing
- **Approval decisions:** Whether a card meets production standards (role owners approve)

## Why Production Cards Exist

Production cards exist to:
1. **Separate concerns:** Each card type has a clear owner and purpose
2. **Enable parallel work:** Different roles can work on their cards simultaneously
3. **Provide audit trail:** All decisions and references are documented
4. **Enable validation:** Cards can be checked for completeness before generation
5. **Prevent repeated loops:** Missing or incomplete cards block generation until fixed
6. **Support reusability:** Asset cards can be referenced across multiple shots

## How This Prevents Repeated Generation Loops

### Problem Without Cards
- Generation starts with incomplete information
- Generated output fails QA
- System retries generation with same incomplete information
- Loop continues until manual intervention

### Solution With Cards
- Orchestrator checks card completeness before routing to generation
- Missing cards block generation entirely
- Incomplete cards route back to owning role for completion
- Generation only proceeds when all prerequisites are satisfied
- Each generation attempt uses validated, complete information

### Example Loop Prevention
**Without cards:**
1. Generate shot with missing character reference
2. Identity QA fails
3. Retry generation (same missing reference)
4. Loop continues

**With cards:**
1. Orchestrator detects missing CharacterCard
2. Routes work to Character Director
3. Character Director creates/populates CharacterCard
4. Orchestrator validates completeness
5. Only then routes to Image Generation Agent
6. Generation succeeds with complete information

## State Machine

### Card States
- **Pending:** Card created but not yet populated
- **Draft:** Card partially populated
- **Complete:** All required fields populated and references satisfied
- **Approved:** Role owner has approved card for production use
- **Blocked:** Card has validation errors or missing dependencies

### Pipeline States
- **Pre-Production:** All cards being created and populated
- **Asset-Ready:** All asset cards complete and approved
- **Workflow-Ready:** Workflow recipe approved
- **Generation-Ready:** All prerequisites met, generation can proceed
- **Generation-In-Progress:** Generation agents executing
- **QA-In-Progress:** Quality checks running
- **Post-Production:** Video compilation and final QA
- **Release-Ready:** Release package assembled and approved

## Key Principles

### 1. No Generation Without Complete Cards
The orchestrator must never route to generation agents unless all prerequisite cards are complete and approved.

### 2. Clear Role Ownership
Every card type has exactly one owning role responsible for its creation and approval.

### 3. Gated Transitions
State transitions require approval from the owning role or designated gatekeeper.

### 4. Immutable Once Approved
Approved cards cannot be modified without formal change process and re-approval.

### 5. Forward-Only Routing
Orchestrator routes work forward to the next responsible role, never backward to retry failed generation without fixing root cause.

### 6. Explicit Dependencies
Card dependencies are explicitly declared and validated before generation.

## Success Metrics

The operating model is successful when:
- Zero generation loops due to missing information
- Clear audit trail for all creative and technical decisions
- Parallel work enabled across roles
- Generation success rate > 95% on first attempt
- QA failures route to specific responsible roles, not generic retry
