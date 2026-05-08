"""Image-level technical region checks.

These checks do NOT require OpenCV. They rely on PIL for basic image
readability, dimensions, and file-level validation. OpenCV-level checks
are delegated to opencv_checks.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image, UnidentifiedImageError


def check_image_readable(image_path: Path) -> Dict[str, Any]:
    """Check if an image file is readable and has valid dimensions."""
    if not image_path.exists():
        return {
            "readable": False,
            "exists": False,
            "error": "file_not_found",
        }

    try:
        with Image.open(image_path) as img:
            img.verify()
        # Re-open to get dimensions after verify
        with Image.open(image_path) as img:
            width, height = img.size
        return {
            "readable": True,
            "exists": True,
            "width": width,
            "height": height,
            "format": image_path.suffix.lower().lstrip("."),
        }
    except (UnidentifiedImageError, OSError, ValueError) as e:
        return {
            "readable": False,
            "exists": True,
            "error": str(e),
        }


def check_dimensions(
    width: Optional[int],
    height: Optional[int],
    min_width: int = 512,
    min_height: int = 512,
) -> Dict[str, Any]:
    """Check image dimensions against minimum requirements."""
    if width is None or height is None:
        return {
            "dimensions_available": False,
            "pass": False,
            "error": "dimensions_not_available",
        }

    return {
        "dimensions_available": True,
        "width": width,
        "height": height,
        "min_width": min_width,
        "min_height": min_height,
        "pass": width >= min_width and height >= min_height,
        "note": f"{width}x{height} (min {min_width}x{min_height})",
    }


def check_file_size(image_path: Path, min_bytes: int = 1024) -> Dict[str, Any]:
    """Check that the file is not a stub (too small)."""
    if not image_path.exists():
        return {"exists": False, "pass": False, "error": "file_not_found"}

    size = image_path.stat().st_size
    return {
        "exists": True,
        "size_bytes": size,
        "min_bytes": min_bytes,
        "pass": size >= min_bytes,
        "stub_detected": size < min_bytes,
    }


def run_region_checks(image_path: Path) -> Dict[str, Any]:
    """Run all basic image-level checks.

    Returns a structured dict with readability, dimension, and file size results.
    """
    readable = check_image_readable(image_path)
    size_ok = check_file_size(image_path)

    result: Dict[str, Any] = {
        "image_path": str(image_path),
    }

    if readable.get("readable"):
        w = readable.get("width")
        h = readable.get("height")
        dims = check_dimensions(w, h)
        result["readable"] = True
        result["dimensions"] = dims
        result["file_size"] = size_ok
        result["stub_asset"] = size_ok.get("stub_detected", True)
    else:
        result["readable"] = False
        result["dimensions"] = {"pass": False, "error": readable.get("error", "unreadable")}
        result["file_size"] = size_ok
        result["stub_asset"] = True
        result["read_error"] = readable.get("error")

    result["region_checks_pass"] = (
        result.get("readable", False)
        and result.get("dimensions", {}).get("pass", False)
        and not result.get("stub_asset", True)
    )

    return result
