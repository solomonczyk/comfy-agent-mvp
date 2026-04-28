# GORYNYCH HEAD 1: Story Contract Knowledge

## Purpose
Defines the structural requirements for story contracts in the GORYNYCH-COMFY protocol.

## Story Contract Structure

A StoryContract must contain:
- `scenario_id`: Unique identifier for the narrative scenario
- `title`: Working title of the episode/scene
- `logline`: Single-sentence narrative summary
- `genre`: Primary genre classification
- `tone`: Emotional tone descriptor
- `setting`: Time and place of the narrative
- `protagonist`: Primary character name and role
- `antagonist`: Opposition force or character
- `conflict_type`: Type of central conflict (internal, external, interpersonal)
- `arc_type`: Narrative arc structure (linear, non-linear, episodic)
- `scene_breakdown`: List of scene identifiers in sequence
- `themes`: Array of thematic elements
- `constraints`: Production or narrative constraints

## Scene Plan Structure

A ScenePlan (part of StoryContract) includes:
- `scene_id`: Unique scene identifier
- `sequence_number`: Position in narrative sequence
- `location`: Physical setting of scene
- `time_of_day`: Lighting condition context
- `weather`: Environmental conditions
- `characters_present`: List of character identifiers
- `action_summary`: Brief description of scene action
- `emotional_beat': Primary emotional shift
- `dialogue_requirements`: If dialogue is present
- `sound_design_notes`: Audio environment requirements

## Beat Specification

A BeatSpec defines atomic narrative units:
- `beat_id`: Unique identifier
- `parent_scene_id`: Scene this beat belongs to
- `beat_type`: (action, reaction, realization, decision, transition)
- `duration_seconds`: Estimated screen time
- `camera_intent`: Suggested camera approach
- `character_focus`: Which character(s) are focal
- `action_description`: What happens in this beat
- `emotional_valence`: Positive/negative/neutral shift

## Validation Rules

- scenario_id must be non-empty and unique
- logline must be under 200 characters
- scene_breakdown must have at least one scene
- all scene_ids in scene_breakdown must have corresponding ScenePlans
- themes array must not be empty
