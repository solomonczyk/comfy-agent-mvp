"""Local deterministic QC judge that doesn't depend on vision API.

Performs hard checks using traditional computer vision:
- Face count detection
- Watermark/text detection
- Blur detection
- Exposure check
- Black/blank/corrupt detection
- Over-smoothing/plasticity heuristic
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageStat

from app.judges.base_types import JudgeInput, JudgeIssue, JudgeReport

logger = logging.getLogger(__name__)


class LocalQCJudge:
    """Local deterministic quality control judge using traditional CV."""
    
    def __init__(self) -> None:
        # Try to load face detector (optional, if available)
        self.face_cascade = None
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
        except Exception as e:
            logger.warning(f"Could not load face cascade: {e}")
    
    def evaluate(self, judge_input: JudgeInput) -> JudgeReport:
        """Evaluate image using local deterministic checks.
        
        Args:
            judge_input: Judge input with image path
            
        Returns:
            JudgeReport with blocking issues for hard defects
        """
        image_path = Path(judge_input.primary_image_path)
        if not image_path.exists():
            return JudgeReport(
                judge_name="local_qc",
                score=0.0,
                verdict="reject",
                blocking_issues=[
                    JudgeIssue(
                        code="missing_image",
                        message=f"Image not found: {image_path}",
                        severity="critical",
                    )
                ],
                recommended_repairs=["regenerate_output"],
                subscores={},
            )
        
        try:
            # Load image
            logger.info(f"Loading image: {image_path}")
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"Failed to load image: {image_path}")
                return JudgeReport(
                    judge_name="local_qc",
                    score=0.0,
                    verdict="reject",
                    blocking_issues=[
                        JudgeIssue(
                            code="corrupt_image",
                            message="Could not read image file",
                            severity="critical",
                        )
                    ],
                    recommended_repairs=["regenerate_output"],
                    subscores={},
                )
            
            logger.info(f"Image loaded successfully: {image_path}, shape: {img.shape}")
            
            # Run local QC checks
            blocking_issues = []
            issues = []
            
            # Check 1: Black/blank/corrupt
            if self._is_blank_or_black(img):
                blocking_issues.append(
                    JudgeIssue(
                        code="black_blank_image",
                        message="Image appears black or blank",
                        severity="critical",
                    )
                )
            
            # Check 2: Exposure (too dark or too bright)
            exposure_score = self._check_exposure(img)
            if exposure_score < 0.2:
                issues.append(
                    JudgeIssue(
                        code="poor_exposure",
                        message=f"Image exposure is poor (score: {exposure_score:.2f})",
                        severity="medium",
                    )
                )
            
            # Check 3: Blur detection
            blur_score = self._check_blur(img)
            if blur_score < 0.1:  # Only block on extremely blurry
                blocking_issues.append(
                    JudgeIssue(
                        code="severe_blur",
                        message=f"Image is severely blurry (score: {blur_score:.2f})",
                        severity="critical",
                    )
                )
            elif blur_score < 0.4:  # Make blur a non-blocking issue
                issues.append(
                    JudgeIssue(
                        code="blurry_image",
                        message=f"Image is blurry (score: {blur_score:.2f})",
                        severity="medium",
                    )
                )
            
            # Check 4: Face count (if detector available) - make multi-subject non-blocking unless confirmed
            if self.face_cascade is not None:
                face_count = self._detect_faces(img)
                if face_count == 0:
                    issues.append(
                        JudgeIssue(
                            code="no_face_detected",
                            message="No face detected in portrait",
                            severity="medium",
                        )
                    )
                elif face_count >= 2:  # Only hard reject if 2+ faces confirmed
                    blocking_issues.append(
                        JudgeIssue(
                            code="multi_subject_confirmed",
                            message=f"Multiple faces confirmed ({face_count})",
                            severity="critical",
                        )
                    )
            
            # Check 5: Text/watermark detection (simple heuristic)
            if self._has_text_watermark(img):
                blocking_issues.append(
                    JudgeIssue(
                        code="watermark_text_detected",
                        message="Text or watermark detected in image",
                        severity="critical",
                    )
                )
            
            # Check 6: Over-smoothing/plasticity heuristic - make non-blocking
            plasticity_score = self._check_plasticity(img)
            if plasticity_score > 0.85:  # Only flag severe plasticity
                issues.append(
                    JudgeIssue(
                        code="plastic_skin",
                        message=f"Image shows signs of over-smoothing/plasticity (score: {plasticity_score:.2f})",
                        severity="medium",
                    )
                )
            
            # Determine verdict based on blocking issues
            if blocking_issues:
                verdict = "reject"
                score = 0.0
            elif issues:
                verdict = "retry"
                score = 0.5
            else:
                verdict = "pass"
                score = 0.8
            
            # Build recommended repairs
            repairs = []
            for issue in blocking_issues + issues:
                if issue.code in ["severe_blur", "blurry_image"]:
                    repairs.append("retry_with_different_seed")
                elif issue.code in ["black_blank_image", "corrupt_image"]:
                    repairs.append("regenerate_output")
                elif issue.code in ["no_face_detected", "multi_subject_unexpected"]:
                    repairs.append("retry_prompt")
                elif issue.code == "watermark_text_detected":
                    repairs.append("reject")
                elif issue.code == "plastic_skin":
                    repairs.append("retry_settings")
            
            # Remove duplicates while preserving order
            repairs = list(dict.fromkeys(repairs))
            
            return JudgeReport(
                judge_name="local_qc",
                score=score,
                verdict=verdict,
                blocking_issues=blocking_issues,
                issues=issues,
                strengths=["local_deterministic_qc"],
                recommended_repairs=repairs if repairs else ["no_action_needed"],
                subscores={
                    "exposure_score": exposure_score,
                    "blur_score": blur_score,
                    "plasticity_score": plasticity_score,
                },
                raw_notes={
                    "_qc_method": "local_deterministic",
                    "_face_count": face_count if self.face_cascade is not None else "detector_unavailable",
                },
            )
            
        except Exception as e:
            logger.error(f"Local QC evaluation failed: {e}")
            # On failure, return neutral result to not block
            return JudgeReport(
                judge_name="local_qc",
                score=0.5,
                verdict="retry",
                blocking_issues=[
                    JudgeIssue(
                        code="local_qc_failure",
                        message=f"Local QC evaluation failed: {str(e)}",
                        severity="medium",
                    )
                ],
                recommended_repairs=["retry_with_different_model"],
                subscores={},
                raw_notes={"_error": str(e)},
            )
    
    def _is_blank_or_black(self, img: np.ndarray) -> bool:
        """Check if image is black or blank."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        std_brightness = np.std(gray)
        
        # Very low mean brightness or very low variance (blank)
        return mean_brightness < 10 or std_brightness < 5
    
    def _check_exposure(self, img: np.ndarray) -> float:
        """Check exposure quality (0.0 = poor, 1.0 = good)."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray) / 255.0  # Normalize to 0-1
        
        # Ideal brightness is around 0.4-0.6
        # Score based on distance from ideal range
        if 0.4 <= mean_brightness <= 0.6:
            return 1.0
        elif 0.3 <= mean_brightness <= 0.7:
            return 0.8
        elif 0.2 <= mean_brightness <= 0.8:
            return 0.5
        else:
            return max(0.0, 1.0 - abs(mean_brightness - 0.5) * 2)
    
    def _check_blur(self, img: np.ndarray) -> float:
        """Check blur using Laplacian variance (0.0 = severe blur, 1.0 = sharp)."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Thresholds based on empirical testing
        if laplacian_var < 50:
            return 0.0  # Severe blur
        elif laplacian_var < 100:
            return 0.3  # Blur
        elif laplacian_var < 200:
            return 0.6  # Acceptable
        else:
            return 1.0  # Sharp
    
    def _detect_faces(self, img: np.ndarray) -> int:
        """Detect faces in image."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        return len(faces)
    
    def _has_text_watermark(self, img: np.ndarray) -> bool:
        """Simple heuristic for text/watermark detection."""
        # Convert to grayscale and apply edge detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Count edge pixels in corners (where watermarks often appear)
        h, w = edges.shape
        corner_size = min(h, w) // 10
        
        top_left = edges[:corner_size, :corner_size]
        top_right = edges[:corner_size, -corner_size:]
        bottom_left = edges[-corner_size:, :corner_size]
        bottom_right = edges[-corner_size:, -corner_size:]
        
        corner_edges = np.mean([top_left, top_right, bottom_left, bottom_right])
        
        # If corners have high edge density, likely has watermark
        return corner_edges > 30
    
    def _check_plasticity(self, img: np.ndarray) -> float:
        """Check for over-smoothing/plasticity using texture analysis.
        
        Returns:
            Score from 0.0 (natural texture) to 1.0 (plastic/over-smoothed)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate local variance (texture measure)
        # High variance = natural texture, low variance = plastic/over-smoothed
        kernel_size = 15
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
        local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        local_variance = cv2.filter2D((gray.astype(np.float32) - local_mean) ** 2, -1, kernel)
        
        mean_variance = np.mean(local_variance)
        
        # Thresholds based on empirical testing
        if mean_variance > 500:
            return 0.0  # Natural texture
        elif mean_variance > 300:
            return 0.3  # Slightly smoothed
        elif mean_variance > 150:
            return 0.6  # Noticeably smoothed
        else:
            return 1.0  # Very plastic/over-smoothed
