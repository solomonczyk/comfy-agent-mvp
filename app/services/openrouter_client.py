from typing import Any

import httpx

from app.config import settings


class OpenRouterClient:
    def __init__(self) -> None:
        self.base_url = settings.openrouter_base_url.rstrip("/")
        self.api_key = settings.openrouter_api_key
        self.model = settings.agent_model
        self.timeout = settings.request_timeout

    async def rewrite_prompt(self, user_prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is empty.")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_http_referer,
            "X-OpenRouter-Title": settings.openrouter_app_title,
        }

        system_prompt = (
            "You rewrite user prompts for SDXL image generation. "
            "Return only one final prompt string. "
            "Do not explain anything. "
            "Make the prompt visually clear, compact, cinematic, realistic, and production-friendly."
        )

        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": 0.4,
            "max_tokens": 200,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": (
                        "Rewrite this user request into a strong SDXL image prompt. "
                        "Keep the intent, add quality and visual clarity, avoid long rambling text.\n\n"
                        f"User request: {user_prompt}"
                    ),
                },
            ],
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        try:
            content = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected OpenRouter response: {data}") from exc

        if not content:
            raise RuntimeError("OpenRouter returned empty content.")

        return content
