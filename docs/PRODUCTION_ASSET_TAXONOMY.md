# Production Asset Taxonomy

## Overview
This document defines the universal asset/card types used in the comfy-agent-mvp production system. Each card type has a clear purpose, required fields, owner role, dependencies, and acceptance criteria.

## Card Types

### 1. ProjectCard

**Purpose:** Top-level container for an entire creative work. Defines project scope, goals, and delivery targets.

**Required Fields (Conceptual):**
- project_id: Unique identifier
- title: Project name
- description: Project overview
- executive_producer: Owner reference
- target_deliverables: List of expected outputs
- timeline: Production schedule
- budget: Resource allocation (optional)
- episode_references: List of EpisodeCard IDs

**Owner Role:** Executive Producer / Product Owner

**Required References:** None (root card)

**Dependencies:** None (root card)

**Acceptance Meaning:** Project is defined and approved for production. Episode creation can begin.

**Missing/Blocked State Examples:**
- Missing: No episodes defined
- Blocked: Executive producer not assigned
- Blocked: Target deliverables undefined

---

### 2. EpisodeCard

**Purpose:** Narrative unit within a project. Defines episode story arc, character roster, and shot scope.

**Required Fields (Conceptual):**
- episode_id: Unique identifier
- project_reference: ProjectCard ID
- title: Episode name
- episode_number: Sequence number
- director: Owner reference
- synopsis: Episode story summary
- character_roster: List of CharacterCard IDs
- scenario_references: List of ScenarioCard IDs
- target_duration: Expected runtime

**Owner Role:** Director / Orchestrator

**Required References:** ProjectCard (must exist and be approved)

**Dependencies:** ProjectCard must be approved

**Acceptance Meaning:** Episode narrative structure is defined. Scenario creation can begin.

**Missing/Blocked State Examples:**
- Missing: No scenarios defined
- Blocked: Character roster empty
- Blocked: Director not assigned
- Blocked: Project reference invalid

---

### 3. ScenarioCard

**Purpose:** Narrative segment within an episode. Defines specific story beat, location, and involved characters.

**Required Fields (Conceptual):**
- scenario_id: Unique identifier
- episode_reference: EpisodeCard ID
- title: Scenario name
- screenwriter: Owner reference
- narrative_beat: Story function
- location_description: Setting description
- involved_characters: List of CharacterCard IDs
- shot_references: List of ShotCard IDs
- environment_reference: EnvironmentCard ID

**Owner Role:** Screenwriter / Script Agent

**Required References:** EpisodeCard, EnvironmentCard

**Dependencies:** EpisodeCard must be approved, EnvironmentCard must exist

**Acceptance Meaning:** Narrative segment is fully defined. Shot design can begin.

**Missing/Blocked State Examples:**
- Missing: No shots defined
- Blocked: Environment reference missing
- Blocked: No characters assigned
- Blocked: Narrative beat undefined

---

### 4. ShotCard

**Purpose:** Atomic unit of generation. Single continuous camera take with specific action, camera, and composition.

**Required Fields (Conceptual):**
- shot_id: Unique identifier
- scenario_reference: ScenarioCard ID
- shot_number: Sequence number
- shot_designer: Owner reference
- shot_type: Close-up, medium, wide, etc.
- action_description: What happens in shot
- duration_seconds: Expected length
- character_reference: CharacterCard ID (if character present)
- environment_reference: EnvironmentCard ID
- camera_reference: CameraCard ID
- lighting_reference: LightingCard ID
- style_reference: StyleCard ID
- wardrobe_reference: WardrobeCard ID (optional)
- prop_references: List of PropCard IDs (optional)

**Owner Role:** Shot Designer / Storyboard Agent

**Required References:** ScenarioCard, CharacterCard, EnvironmentCard, CameraCard, LightingCard, StyleCard

**Dependencies:** ScenarioCard approved, all asset cards complete

**Acceptance Meaning:** Shot is fully specified and ready for generation workflow.

**Missing/Blocked State Examples:**
- Missing: Camera reference undefined
- Blocked: Character reference missing for character shot
- Blocked: Lighting reference missing
- Blocked: Duration not specified

---

### 5. CharacterCard

**Purpose:** Defines character appearance, personality, and identity consistency requirements.

**Required Fields (Conceptual):**
- character_id: Unique identifier
- name: Character name
- character_director: Owner reference
- visual_reference_paths: List of reference image paths
- physical_description: Appearance details
- personality_traits: Character behavior notes
- voice_profile: VoiceCard ID (optional)
- wardrobe_references: List of WardrobeCard IDs
- identity_mode: "gorynych_identity" or "reference_locked"
- identity_consistency_requirements: Multi-shot consistency rules

**Owner Role:** Character Director

**Required References:** Visual reference images (local paths), VoiceCard (if voiced)

**Dependencies:** None (asset-level card)

**Acceptance Meaning:** Character is fully defined with sufficient references for identity-consistent generation.

**Missing/Blocked State Examples:**
- Missing: No visual references
- Blocked: Identity mode not specified
- Blocked: Physical description too vague
- Blocked: Missing voice profile for voiced character

---

### 6. EnvironmentCard

**Purpose:** Defines location, setting, and environmental conditions.

**Required Fields (Conceptual):**
- environment_id: Unique identifier
- name: Location name
- art_director: Owner reference
- visual_reference_paths: List of reference image paths
- description: Setting description
- time_of_day: Lighting conditions
- weather_conditions: Environmental factors
- prop_references: List of PropCard IDs (optional)

**Owner Role:** Environment / Art Director

**Required References:** Visual reference images (local paths)

**Dependencies:** None (asset-level card)

**Acceptance Meaning:** Environment is fully defined with sufficient references for generation.

**Missing/Blocked State Examples:**
- Missing: No visual references
- Blocked: Description too vague
- Blocked: Time of day undefined
- Blocked: Location name missing

---

### 7. LightingCard

**Purpose:** Defines lighting scheme, mood, and technical lighting parameters.

**Required Fields (Conceptual):**
- lighting_id: Unique identifier
- name: Lighting scheme name
- cinematographer: Owner reference
- mood: Emotional tone
- light_sources: List of light types and positions
- color_temperature: Kelvin value
- intensity: Brightness level
- shadow_characteristics: Hard/soft shadows

**Owner Role:** Cinematographer / Camera + Lighting Director

**Required References:** None (technical specification)

**Dependencies:** None (technical specification)

**Acceptance Meaning:** Lighting scheme is fully specified for workflow integration.

**Missing/Blocked State Examples:**
- Missing: Light sources undefined
- Blocked: Color temperature not specified
- Blocked: Mood undefined
- Blocked: Cinematographer not assigned

---

### 8. CameraCard

**Purpose:** Defines camera position, movement, and lens parameters.

**Required Fields (Conceptual):**
- camera_id: Unique identifier
- name: Camera setup name
- cinematographer: Owner reference
- position: X, Y, Z coordinates
- angle: Pitch, yaw, roll
- lens_focal_length: mm value
- depth_of_field: Aperture/f-stop
- movement_type: Static, pan, tilt, dolly, crane, etc.
- movement_parameters: Speed, direction, duration

**Owner Role:** Cinematographer / Camera + Lighting Director

**Required References:** None (technical specification)

**Dependencies:** None (technical specification)

**Acceptance Meaning:** Camera setup is fully specified for workflow integration.

**Missing/Blocked State Examples:**
- Missing: Position coordinates undefined
- Blocked: Lens focal length not specified
- Blocked: Movement type undefined
- Blocked: Cinematographer not assigned

---

### 9. StyleCard

**Purpose:** Defines visual style, aesthetic, and artistic direction.

**Required Fields (Conceptual):**
- style_id: Unique identifier
- name: Style name
- director: Owner reference
- visual_reference_paths: List of reference images
- aesthetic_description: Style description
- color_palette: Primary and secondary colors
- texture_quality: Detail level
- rendering_style: Photorealistic, stylized, etc.

**Owner Role:** Director / Orchestrator

**Required References:** Visual reference images (local paths)

**Dependencies:** None (artistic direction)

**Acceptance Meaning:** Visual style is fully defined with sufficient references.

**Missing/Blocked State Examples:**
- Missing: No visual references
- Blocked: Color palette undefined
- Blocked: Aesthetic description too vague
- Blocked: Rendering style not specified

---

### 10. WardrobeCard

**Purpose:** Defines character clothing, accessories, and appearance details.

**Required Fields (Conceptual):**
- wardrobe_id: Unique identifier
- character_reference: CharacterCard ID
- name: Outfit name
- wardrobe_director: Owner reference
- visual_reference_paths: List of reference images
- description: Clothing description
- accessories: List of items
- color_scheme: Primary colors
- material_types: Fabric/texture notes

**Owner Role:** Wardrobe/Character Director

**Required References:** CharacterCard, visual reference images

**Dependencies:** CharacterCard must exist

**Acceptance Meaning:** Wardrobe is fully defined with sufficient references for generation.

**Missing/Blocked State Examples:**
- Missing: No visual references
- Blocked: Character reference invalid
- Blocked: Description too vague
- Blocked: Color scheme undefined

---

### 11. PropCard

**Purpose:** Defines objects, items, and set dressings used in scenes.

**Required Fields (Conceptual):**
- prop_id: Unique identifier
- name: Prop name
- prop_master: Owner reference (or Environment Director)
- visual_reference_paths: List of reference images
- description: Prop description
- material: Construction material
- size_dimensions: Physical dimensions
- interaction_notes: How prop is used

**Owner Role:** Prop Master / Environment Director

**Required References:** Visual reference images (local paths)

**Dependencies:** None (asset-level card)

**Acceptance Meaning:** Prop is fully defined with sufficient references for generation.

**Missing/Blocked State Examples:**
- Missing: No visual references
- Blocked: Dimensions undefined
- Blocked: Description too vague
- Blocked: Material unspecified

---

### 12. VoiceCard

**Purpose:** Defines voice characteristics, TTS settings, and audio parameters for character dialogue.

**Required Fields (Conceptual):**
- voice_id: Unique identifier
- character_reference: CharacterCard ID (optional)
- name: Voice profile name
- audio_director: Owner reference
- tts_engine: Text-to-speech engine identifier
- voice_model: Specific voice model
- pitch: Voice pitch setting
- speed: Speech rate
- emotion: Emotional tone
- reference_audio_path: Sample audio (optional)

**Owner Role:** Audio / Voice Agent

**Required References:** CharacterCard (if character-specific), reference audio (optional)

**Dependencies:** None (technical specification)

**Acceptance Meaning:** Voice profile is fully specified for TTS generation.

**Missing/Blocked State Examples:**
- Missing: TTS engine undefined
- Blocked: Voice model not specified
- Blocked: Pitch/speed parameters missing
- Blocked: Audio director not assigned

---

### 13. WorkflowRecipeCard

**Purpose:** Defines ComfyUI workflow graph, node parameters, and generation pipeline configuration.

**Required Fields (Conceptual):**
- recipe_id: Unique identifier
- name: Workflow name
- workflow_td: Owner reference
- workflow_graph: ComfyUI API format JSON
- node_parameters: Parameter overrides
- input_mappings: Card fields to workflow inputs
- output_mappings: Workflow outputs to artifacts
- resource_requirements: GPU, memory, etc.
- estimated_generation_time: Per-frame duration

**Owner Role:** Workflow TD / ComfyUI Technical Director

**Required References:** None (technical specification)

**Dependencies:** None (technical specification)

**Acceptance Meaning:** Workflow is fully defined, tested, and approved for production use.

**Missing/Blocked State Examples:**
- Missing: Workflow graph undefined
- Blocked: Input mappings incomplete
- Blocked: Output mappings undefined
- Blocked: Workflow TD not assigned
- Blocked: Not tested or approved

---

### 14. QARequirementCard

**Purpose:** Defines quality assurance criteria, thresholds, and validation rules for generated artifacts.

**Required Fields (Conceptual):**
- qa_requirement_id: Unique identifier
- qa_supervisor: Owner reference
- target_artifact_type: Frame, audio, video
- quality_thresholds: Minimum acceptable metrics
- validation_rules: Specific checks to perform
- failure_criteria: What constitutes failure
- remediation_actions: How to handle failures

**Owner Role:** Editor / Final QA Supervisor

**Required References:** None (quality specification)

**Dependencies:** None (quality specification)

**Acceptance Meaning:** QA requirements are fully defined and ready for validation execution.

**Missing/Blocked State Examples:**
- Missing: Quality thresholds undefined
- Blocked: Validation rules incomplete
- Blocked: Failure criteria unclear
- Blocked: QA supervisor not assigned

---

### 15. ReleasePackageCard

**Purpose:** Assembles final deliverables for distribution. Defines release contents, formats, and metadata.

**Required Fields (Conceptual):**
- release_package_id: Unique identifier
- project_reference: ProjectCard ID
- episode_reference: EpisodeCard ID (optional)
- name: Release name
- version: Semantic version
- release_manager: Owner reference
- contents: List of artifact references
- formats: Output formats (MP4, PNG, etc.)
- metadata: Release metadata
- distribution_targets: Where to publish

**Owner Role:** Executive Producer / Release Manager

**Required References:** ProjectCard, generated artifacts

**Dependencies:** All generation complete, all QA passed

**Acceptance Meaning:** Release package is assembled and approved for distribution.

**Missing/Blocked State Examples:**
- Missing: Contents list empty
- Blocked: Formats undefined
- Blocked: Metadata incomplete
- Blocked: Artifacts not yet generated or QA failed

---

## Card Relationships

### Hierarchy
```
ProjectCard
  └── EpisodeCard
      └── ScenarioCard
          └── ShotCard
```

### Asset References (Cross-Shot Reuse)
- CharacterCard referenced by multiple ShotCards
- EnvironmentCard referenced by multiple ScenarioCards
- PropCard referenced by multiple ShotCards
- WardrobeCard referenced by multiple ShotCards

### Technical References
- ShotCard references: CameraCard, LightingCard, StyleCard
- CharacterCard references: VoiceCard, WardrobeCard
- EnvironmentCard references: PropCard

### Workflow References
- ShotCard references WorkflowRecipeCard
- WorkflowRecipeCard references QARequirementCard

## Validation Rules

### Completeness Check
For each card, all required fields must be populated.

### Reference Validity Check
All referenced card IDs must exist and be in "Complete" or "Approved" state.

### Dependency Check
All dependency cards must be approved before dependent card can be approved.

### Consistency Check
Card fields must be internally consistent (e.g., duration matches action description).
