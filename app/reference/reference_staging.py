"""MK-REAL3R-6 — Reference staging and clean reference gate.

MK-PROFILE1 — Project-profile-driven reference staging.
This module provides functionality to:
1. Stage non-ASCII reference paths to ASCII-safe local paths
2. Validate reference images are clean single-character references
3. Prepare clean reference candidates from multi-panel sheets
4. Generate clean references using project-profile-driven strategies
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

from app.profile.project_profile import (
    CleanReferenceConfig,
    resolve_character_profile,
)


def has_non_ascii(path: str | Path) -> bool:
    """Check if a path contains non-ASCII characters or spaces.

    Args:
        path: Path to check

    Returns:
        True if path contains non-ASCII or spaces, False otherwise
    """
    path_str = str(path)
    try:
        path_str.encode('ascii')
        has_spaces = ' ' in path_str
        return has_spaces
    except UnicodeEncodeError:
        return True


def stage_reference_to_ascii(
    original_path: str | Path,
    project_root: str | Path,
    character_name: str,
) -> tuple[str, str, dict[str, Any] | None]:
    """Stage a reference image to an ASCII-safe local path.

    MK-PROFILE1 — Project-profile-driven reference staging.
    If the original path contains non-ASCII characters or spaces:
    1. Load project profile and resolve character profile
    2. Use clean_reference strategy from profile if available
    3. Otherwise, use safe ASCII staging fallback

    Args:
        original_path: Original reference image path (may contain non-ASCII)
        project_root: Project root directory
        character_name: Character name for staging filename

    Returns:
        Tuple of (original_path, staged_path, reference_cleanliness_metadata).
        If original is already ASCII, staged_path equals original_path.
        reference_cleanliness_metadata contains strategy info if clean reference was used.
    """
    original = Path(original_path).resolve()
    project = Path(project_root).resolve()

    # If path is already ASCII-only and has no spaces, return as-is
    if not has_non_ascii(original):
        return str(original), str(original), None

    # Create staging directory
    staging_dir = project / "output" / "control" / "references"
    staging_dir.mkdir(parents=True, exist_ok=True)

    # MK-PROFILE1 — Try to use project profile for clean reference generation
    character_profile = resolve_character_profile(character_name, project)
    
    if character_profile and character_profile.clean_reference:
        config = character_profile.clean_reference
        try:
            # Use the profile's original reference path if available
            profile_original = Path(character_profile.reference_image_path)
            if profile_original.exists():
                clean_path = create_clean_reference_from_strategy(profile_original, staging_dir, config)
                
                # Build reference cleanliness metadata
                cleanliness_metadata = {
                    "verdict": "pass",
                    "strategy": config.strategy,
                    "source": "project_profile",
                    "uses_contact_sheet_directly": False,
                    "character_id": character_profile.character_id,
                }
                
                return str(profile_original), str(clean_path), cleanliness_metadata
        except Exception as e:
            # Fallback to legacy behavior if profile strategy fails
            import logging
            logging.warning(f"[MK-PROFILE1] Failed to use profile strategy: {e}")

    # Legacy fallback: Check for legacy clean reference candidate
    clean_candidate = staging_dir / f"{character_name.lower()}_clean_reference_480x640.png"
    if not clean_candidate.exists():
        # Fallback to any clean reference candidate in the staging directory
        for f in staging_dir.glob("*_clean_reference_480x640.png"):
            clean_candidate = f
            break
    if clean_candidate.exists():
        # Use clean reference candidate
        return str(original), str(clean_candidate), None

    # Fallback: Generate ASCII-safe filename and copy
    safe_name = f"{character_name.lower()}_reference.png"
    staged_path = staging_dir / safe_name

    # Copy file to staging location
    shutil.copy2(original, staged_path)

    return str(original), str(staged_path), None


def is_multi_panel_image(image_path: str | Path) -> dict[str, Any]:
    """Check if an image appears to be a multi-panel/contact sheet.

    Detects:
    - Contact sheet / grid layout
    - Large UI/text strip
    - Multiple panels
    - Visible interface controls

    Args:
        image_path: Path to image file

    Returns:
        Dict with 'is_multi_panel' (bool) and 'reason' (str)
    """
    try:
        img = Image.open(image_path)
        width, height = img.size

        # Simple heuristic: if aspect ratio is very wide or very tall, likely multi-panel
        aspect_ratio = width / height
        if aspect_ratio > 3.0 or aspect_ratio < 0.33:
            return {
                "is_multi_panel": True,
                "reason": f"Extreme aspect ratio {aspect_ratio:.2f} suggests multi-panel layout"
            }

        # Check for grid-like patterns by sampling center and corners
        # This is a simplified check - a real implementation would use CV
        # For now, we'll use a conservative threshold
        # If image is very large (>2000px in either dimension), likely multi-panel
        if width > 2000 or height > 2000:
            return {
                "is_multi_panel": True,
                "reason": f"Large image dimensions ({width}x{height}) suggest contact sheet"
            }

        return {
            "is_multi_panel": False,
            "reason": "Image appears to be single panel"
        }

    except Exception as e:
        return {
            "is_multi_panel": True,
            "reason": f"Error analyzing image: {e}"
        }


def validate_clean_reference(
    image_path: str | Path,
) -> tuple[bool, str]:
    """Validate that a reference image is a clean single-character reference.

    Args:
        image_path: Path to reference image

    Returns:
        Tuple of (is_valid, reason)
    """
    check = is_multi_panel_image(image_path)
    if check["is_multi_panel"]:
        return False, check["reason"]

    return True, "Image is a clean single-character reference"


def prepare_clean_reference_candidate(
    source_path: str | Path,
    output_path: str | Path,
    target_width: int = 480,
    target_height: int = 640,
) -> str:
    """Prepare a clean reference candidate from a multi-panel sheet.

    For now, this is a simplified implementation that:
    - Crops center region of the image
    - Resizes to target dimensions

    Args:
        source_path: Source multi-panel image path
        output_path: Output path for clean reference
        target_width: Target width in pixels
        target_height: Target height in pixels

    Returns:
        Path to the prepared clean reference
    """
    source = Path(source_path).resolve()
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as img:
        # Crop center region (simplified)
        width, height = img.size
        left = (width - min(width, height)) // 2
        top = (height - min(width, height)) // 2
        right = left + min(width, height)
        bottom = top + min(width, height)
        cropped = img.crop((left, top, right, bottom))

        # Resize to target dimensions
        resized = cropped.resize((target_width, target_height), Image.Resampling.LANCZOS)
        resized.save(output, "PNG")

    return str(output)


def create_clean_reference_from_strategy(
    original_path: Path,
    output_dir: Path,
    config: CleanReferenceConfig,
) -> Path:
    """MK-PROFILE1 — Generic clean reference generation using strategy config.

    Args:
        original_path: Path to original reference image
        output_dir: Directory to save the clean reference
        config: CleanReferenceConfig with strategy parameters

    Returns:
        Path to the generated clean reference
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / config.output_name

    if output_path.exists() and not config.force_regenerate:
        return output_path

    img = Image.open(original_path).convert("RGB")
    w, h = img.size

    # Compute crop box based on mode
    if config.crop_box_mode == "relative":
        left = int(config.crop_box[0] * w)
        top = int(config.crop_box[1] * h)
        right = int(config.crop_box[2] * w)
        bottom = int(config.crop_box[3] * h)
    else:  # absolute
        left = int(config.crop_box[0])
        top = int(config.crop_box[1])
        right = int(config.crop_box[2])
        bottom = int(config.crop_box[3])

    crop_box = (left, top, right, bottom)
    panel = img.crop(crop_box)

    # Fit to target dimensions
    clean = ImageOps.fit(
        panel,
        (config.target_width, config.target_height),
        method=Image.Resampling.LANCZOS,
        centering=tuple(config.centering),
    )

    clean.save(output_path)
    return output_path


def create_alya_clean_single_portrait(
    original_path: Path,
    output_dir: Path,
) -> Path:
    """DEPRECATED: Create a clean single-character portrait from Alya contact sheet.

    RC-CORE1 — This function is deprecated. Use create_clean_reference_from_strategy
    with a CleanReferenceConfig from project_profile instead.

    This function is kept for backward compatibility but should not be used in new code.
    The generic create_clean_reference_from_strategy function provides the same
    functionality without hardcoding character-specific logic.

    This wrapper builds a CleanReferenceConfig for backward compatibility and delegates
    to create_clean_reference_from_strategy.

    Args:
        original_path: Path to original contact sheet
        output_dir: Directory to save the clean portrait

    Returns:
        Path to the clean single portrait (480x640)
    """
    import warnings
    from app.profile.project_profile import CleanReferenceConfig

    warnings.warn(
        "create_alya_clean_single_portrait is deprecated. "
        "Use create_clean_reference_from_strategy with CleanReferenceConfig instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # Build CleanReferenceConfig for backward compatibility
    config = CleanReferenceConfig(
        strategy="single_panel_crop",
        output_name="alya_clean_single_portrait_480x640.png",
        target_width=480,
        target_height=640,
        crop_box_mode="relative",
        crop_box=[0.0, 0.0, 0.3333, 0.42],
        centering=[0.5, 0.35],
        force_regenerate=True,
    )

    # Delegate to generic strategy
    return create_clean_reference_from_strategy(original_path, output_dir, config)


def create_alya_clean_single_portrait_v2(
    original_path: Path,
    output_dir: Path,
    *,
    force: bool = True,
) -> Path:
    """DEPRECATED: Create a clean single-character portrait v2 from Alya contact sheet.

    RC-CORE1 — This function is deprecated. Use create_clean_reference_from_strategy
    with a CleanReferenceConfig from project_profile instead.

    This function is kept for backward compatibility but should not be used in new code.
    The generic create_clean_reference_from_strategy function provides the same
    functionality without hardcoding character-specific logic.

    This wrapper builds a CleanReferenceConfig for backward compatibility and delegates
    to create_clean_reference_from_strategy.

    Args:
        original_path: Path to original contact sheet
        output_dir: Directory to save the clean portrait
        force: If True, always regenerate even if file exists

    Returns:
        Path to the clean single portrait v2 (480x640)
    """
    import warnings
    from app.profile.project_profile import CleanReferenceConfig

    warnings.warn(
        "create_alya_clean_single_portrait_v2 is deprecated. "
        "Use create_clean_reference_from_strategy with CleanReferenceConfig instead.",
        DeprecationWarning,
        stacklevel=2
    )

    # Build CleanReferenceConfig for backward compatibility
    config = CleanReferenceConfig(
        strategy="single_panel_crop",
        output_name="alya_clean_single_portrait_v2_480x640.png",
        target_width=480,
        target_height=640,
        crop_box_mode="relative",
        crop_box=[0.0, 0.0, 0.3333, 0.42],
        centering=[0.5, 0.35],
        force_regenerate=force,
    )

    # Delegate to generic strategy
    return create_clean_reference_from_strategy(original_path, output_dir, config)
