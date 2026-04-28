from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class VisionJudgeClient:
    """
    Real multimodal vision judge client using OpenRouter.
    Evaluates images against judge prompts and returns strict JSON.
    """

    def __init__(
        self,
        *,
        model: str = "openai/gpt-4o",
        timeout: int = 60,
    ) -> None:
        self.base_url = settings.openrouter_base_url.rstrip("/")
        self.api_key = settings.openrouter_api_key
        self.model = model
        self.timeout = timeout

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 string."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with path.open("rb") as f:
            image_data = f.read()
        
        return base64.b64encode(image_data).decode("utf-8")

    def _build_multimodal_payload(self, image_path: str, prompt: str) -> dict[str, Any]:
        """Build multimodal payload for OpenRouter API."""
        base64_image = self._encode_image(image_path)
        
        return {
            "model": self.model,
            "temperature": 0.3,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}",
                            },
                        },
                    ],
                },
            ],
        }

    def judge_image(self, *, image_path: str, prompt: str) -> dict[str, Any] | str:
        """
        Evaluate image against judge prompt using multimodal model.
        
        Args:
            image_path: Path to the image file (PNG)
            prompt: Judge prompt with evaluation criteria
            
        Returns:
            Dict with judge results (score, verdict, issues, etc.) or raw string response
            
        Raises:
            RuntimeError: If API key is missing or request fails
            ValueError: If response cannot be parsed as JSON
        """
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is empty.")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_http_referer,
            "X-OpenRouter-Title": settings.openrouter_app_title,
        }

        payload = self._build_multimodal_payload(image_path, prompt)

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"Vision judge request timed out after {self.timeout}s") from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Vision judge HTTP error: {exc.response.status_code} - {exc.response.text}") from exc
        except Exception as exc:
            raise RuntimeError(f"Vision judge request failed: {str(exc)}") from exc

        try:
            content = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            logger.error(f"Unexpected OpenRouter response structure: {data}")
            raise RuntimeError(f"Unexpected OpenRouter response: {data}") from exc

        if not content:
            logger.error("OpenRouter returned empty content")
            raise RuntimeError("OpenRouter returned empty content.")

        # Log raw response for debugging
        logger.info(f"Raw vision response length: {len(content)} chars")
        
        # Parser hardening: clean markdown fences and extract JSON
        cleaned_content = self._extract_json_from_content(content)
        
        # Try to parse as JSON
        try:
            parsed = json.loads(cleaned_content)
            logger.info(f"Successfully parsed JSON with keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'not a dict'}")
            
            if isinstance(parsed, dict):
                # Add metadata about parsing
                parsed["_vision_status"] = "valid_json"
                parsed["_raw_response_length"] = len(content)
                return parsed
            # If it's a list or other type, wrap it
            return {
                "raw_response": parsed,
                "_vision_status": "valid_json_non_dict",
                "_raw_response_length": len(content)
            }
        except json.JSONDecodeError as exc:
            logger.error(f"JSON decode error: {exc}. Content preview: {content[:200]}")
            # Return standard fallback dict for invalid JSON with vision_status
            return {
                "score": None,  # Not 0.0 to indicate invalid
                "verdict": "retry",
                "blocking_issues": [
                    {
                        "code": "invalid_json_response",
                        "message": f"Model returned non-JSON content: {str(exc)}",
                        "severity": "high"
                    }
                ],
                "issues": [],
                "strengths": [],
                "recommended_repairs": ["retry_same_judge_request_or_switch_model"],
                "subscores": {},
                "_vision_status": "invalid_json",
                "_raw_response": content,
                "_parse_error": str(exc)
            }
    
    def _extract_json_from_content(self, content: str) -> str:
        """Extract JSON from content, handling markdown fences and extra text.
        
        Args:
            content: Raw content from vision model
            
        Returns:
            Cleaned JSON string
        """
        # Remove markdown code fences
        if "```json" in content:
            # Extract content between ```json and ```
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        elif "```" in content:
            # Extract content between first ``` and next ```
            start = content.find("```") + 3
            end = content.find("```", start)
            if end != -1:
                content = content[start:end].strip()
        
        # Try to find JSON object boundaries
        content = content.strip()
        if content.startswith("{") and content.endswith("}"):
            return content
        elif content.startswith("[") and content.endswith("]"):
            return content
        else:
            # Try to find first { and last }
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                return content[start:end+1]
        
        return content
