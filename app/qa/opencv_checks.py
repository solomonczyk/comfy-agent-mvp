"""OpenCV-based technical image checks.

If OpenCV (cv2) is unavailable, returns a safe fallback result without
crashing the QA engine.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

CV2_AVAILABLE: bool = False
try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    pass


def check_opencv_available() -> bool:
    """Return whether OpenCV (cv2) is importable."""
    return CV2_AVAILABLE


def compute_blur_score(image_path: Path) -> Optional[float]:
    """Compute Laplacian variance blur score.

    Higher values = sharper image. Typical threshold: < 100 is blurry.
    Returns None if cv2 is unavailable or image cannot be read.
    """
    if not CV2_AVAILABLE:
        return None
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        return float(cv2.Laplacian(img, cv2.CV_64F).var())
    except Exception:
        return None


def compute_brightness(image_path: Path) -> Optional[float]:
    """Compute mean brightness (0-255)."""
    if not CV2_AVAILABLE:
        return None
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if img is None:
            return None
        return float(cv2.mean(img)[0])
    except Exception:
        return None


def compute_contrast(image_path: Path) -> Optional[float]:
    """Compute RMS contrast (standard deviation of pixel intensities)."""
    if not CV2_AVAILABLE:
        return None
    try:
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        return float(img.std())
    except Exception:
        return None


def detect_mouth_region_heuristic(image_path: Path) -> Dict[str, Any]:
    """Heuristic check for mouth/teeth region in a portrait.

    Uses face cascade to find face, then estimates lower-third ROI.
    If cv2 unavailable or cascade fails, returns safe fallback.
    """
    if not CV2_AVAILABLE:
        return {
            "opencv_available": False,
            "checks_executed": False,
            "fallback_reason": "cv2_not_installed",
        }

    try:
        import cv2 as cv2_mod  # type: ignore

        img = cv2_mod.imread(str(image_path))
        if img is None:
            return {
                "opencv_available": True,
                "checks_executed": False,
                "fallback_reason": "image_not_readable",
            }

        gray = cv2_mod.cvtColor(img, cv2_mod.COLOR_BGR2GRAY)
        face_cascade = cv2_mod.CascadeClassifier(
            cv2_mod.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return {
                "opencv_available": True,
                "checks_executed": True,
                "face_detected": False,
                "note": "No face detected in image",
            }

        # For the first face, estimate mouth region in lower third
        x, y, w, h = faces[0]
        mouth_y = y + int(h * 0.65)
        mouth_h = int(h * 0.25)
        mouth_x = x
        mouth_w = w

        mouth_roi = gray[mouth_y : mouth_y + mouth_h, mouth_x : mouth_x + mouth_w]
        if mouth_roi.size == 0:
            return {
                "opencv_available": True,
                "checks_executed": True,
                "face_detected": True,
                "mouth_roi_valid": False,
                "note": "Mouth ROI empty (unexpected geometry)",
            }

        # Simple heuristic: check if mouth region has high-frequency detail
        mouth_blur = float(cv2_mod.Laplacian(mouth_roi, cv2_mod.CV_64F).var())
        mouth_mean = float(cv2_mod.mean(mouth_roi)[0])
        mouth_std = float(mouth_roi.std())

        return {
            "opencv_available": True,
            "checks_executed": True,
            "face_detected": True,
            "face_count": len(faces),
            "mouth_roi_valid": True,
            "mouth_region": {
                "x": int(mouth_x),
                "y": int(mouth_y),
                "w": int(mouth_w),
                "h": int(mouth_h),
            },
            "mouth_blur_score": round(mouth_blur, 2),
            "mouth_brightness": round(mouth_mean, 2),
            "mouth_contrast": round(mouth_std, 2),
            "suspicious_mouth": mouth_blur < 50 or mouth_std < 20,
        }

    except Exception as exc:
        return {
            "opencv_available": True,
            "checks_executed": False,
            "fallback_reason": f"cascade_or_processing_error: {exc}",
        }


def run_opencv_checks(image_path: Path) -> Dict[str, Any]:
    """Run all available OpenCV checks on the given image.

    Always returns a structured result. If cv2 is unavailable, all
    checks report as not executed with a fallback reason.
    """
    if not CV2_AVAILABLE:
        return {
            "opencv_available": False,
            "checks_executed": False,
            "fallback_reason": "cv2_not_installed",
        }

    if not image_path.exists():
        return {
            "opencv_available": True,
            "checks_executed": False,
            "fallback_reason": "image_file_not_found",
        }

    blur_score = compute_blur_score(image_path)
    brightness = compute_brightness(image_path)
    contrast = compute_contrast(image_path)
    mouth_check = detect_mouth_region_heuristic(image_path)

    return {
        "opencv_available": True,
        "checks_executed": True,
        "blur_score": blur_score,
        "brightness": brightness,
        "contrast": contrast,
        "is_blurry": blur_score is not None and blur_score < 100,
        "mouth_analysis": mouth_check,
    }
