# GORYNYCH HEAD 2: Character Canon Knowledge

## Purpose
Defines character anchoring and consistency requirements for visual production.

## Character Canon Structure

A CharacterCanon maintains visual and behavioral consistency:
- `character_id`: Unique character identifier
- `name`: Character name
- `role`: Narrative role (protagonist, antagonist, supporting, extra)
- `age_approximate`: Age range or specific age
- `gender`: Gender presentation
- `ethnicity`: Ethnic/racial background
- `build`: Body type description
- `height_category`: (short, average, tall)
- `distinctive_features`: Array of notable physical traits
- `skin_tone`: Skin tone description
- `hair_color`: Hair color
- `hair_style`: Hair style description
- `eye_color`: Eye color
- `facial_structure`: Face shape and features
- `costume_primary`: Main outfit description
- `costume_secondary`: Alternative outfit if applicable
- `accessories`: Notable accessories or props
- `posture_default`: Default posture/mannerisms
- `expression_default`: Default facial expression
- `voice_characteristics`: Voice description if relevant
- `personality_traits`: Array of personality descriptors
- `background_summary`: Brief character background

## Character Anchors

Anchors are reference specifications:
- `anchor_id`: Unique anchor identifier
- `character_id`: Link to character
- `anchor_type`: (portrait_full, portrait_closeup, body_reference, action_pose, expression_sheet)
- `view_angle`: (front, three-quarter, profile, back)
- `lighting_condition`: Reference lighting setup
- `emotion_state`: Emotional expression in reference
- `priority`: (critical, high, medium, low)
- `status`: (pending, generated, approved, locked)
- `reference_path`: Path to approved reference image
- `generation_notes`: Specific generation instructions

## Reference Lock Contract

Controls downstream generation based on reference availability:
- `lock_id`: Unique lock identifier
- `character_id`: Character being locked
- `required_anchors`: Array of anchor_ids that must be approved
- `downstream_generation_allowed`: Boolean - false by default
- `lock_reason`: Why generation is blocked
- `unlock_conditions`: What must happen to unlock
- `approval_timestamp`: When lock was established
- `approved_by`: System or user who approved

## Validation Rules

- character_id must be unique across canon
- at least one portrait anchor is required per character
- downstream_generation_allowed defaults to false
- lock cannot be released without all required_anchors approved
- distinctive_features array must not be empty
