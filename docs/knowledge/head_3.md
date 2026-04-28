# GORYNYCH HEAD 3: Shot and Prompt Knowledge

## Purpose
Defines shot composition, camera work, and prompt engineering specifications.

## Shot Contract Structure

A ShotContract specifies visual execution parameters:
- `shot_id`: Unique shot identifier
- `scene_id`: Parent scene
- `beat_id`: Parent beat if applicable
- `shot_type`: (wide, medium, closeup, extreme_closeup, establishing, insert)
- `camera_angle`: (eye_level, low_angle, high_angle, dutch, over_shoulder, pov)
- `focal_length_mm`: Lens focal length in millimeters
- `aperture`: f-stop value
- `depth_of_field`: (shallow, medium, deep)
- `camera_movement`: (static, pan, tilt, dolly, truck, pedestal, zoom, handheld, crane)
- `movement_speed`: (static, slow, medium, fast)
- `framing`: Subject positioning in frame
- `composition_rule`: (rule_of_thirds, center_frame, golden_ratio, symmetrical)
- `aspect_ratio`: Frame aspect ratio (e.g., "16:9")
- `lighting_setup`: Lighting scheme description
- `lighting_key`: (key_high, key_low, flat, dramatic, silhouette, backlit)
- `lighting_direction`: (front, side, back, top, bottom, rembrandt, split)
- `color_palette`: Dominant color scheme
- `color_grading_intent': Post-processing color intent
- `focus_subject`: Primary focus element
- `background_elements`: Notable background elements
- `atmosphere': Mood and atmosphere description
- `technical_notes`: Any technical constraints

## Prompt Pack Structure

A PromptPack contains generation instructions:
- `prompt_pack_id`: Unique identifier
- `shot_id`: Associated shot
- `positive_prompt`: English positive generation prompt
- `negative_prompt`: English negative generation prompt
- `style_modifiers`: Array of style keywords
- `quality_tags`: Array of quality enhancement tags
- `technical_params`: Dictionary of technical parameters
- `seed_policy`: (fixed, random, controlled_random)
- `seed_value`: Specific seed if fixed
- `generation_steps': Number of inference steps
- `cfg_scale`: Classifier-free guidance scale
- `denoising_strength`: For img2img workflows
- `language_requirement`: Must be "en" for English
- `prompt_validation_passed`: Boolean validation flag

## Validation Rules

- positive_prompt must be in English
- negative_prompt must be in English
- seed_policy defaults to "controlled_random" unless explicitly set to "random"
- random seed policy requires explicit allow_random_seed flag
- focal_length_mm must be realistic (e.g., 24mm-200mm)
- camera_movement must match shot_type appropriateness
- lighting_key must be compatible with lighting_setup
