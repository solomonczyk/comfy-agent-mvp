from app.services.openrouter_client import OpenRouterClient


class PromptRewriter:
    def __init__(self) -> None:
        self.client = OpenRouterClient()

    @staticmethod
    def _fallback_prompt(prompt: str) -> str:
        return (
            f"{prompt}, cinematic lighting, realistic details, "
            f"high quality, professional photography, detailed texture"
        )

    async def build_prompt(
        self,
        user_prompt: str,
        mode: str = "fallback",
    ) -> tuple[str, str]:
        prompt = user_prompt.strip()

        if not prompt:
            raise ValueError("Prompt must not be empty.")

        if mode == "raw":
            return prompt, "raw"

        if mode == "llm":
            try:
                rewritten = await self.client.rewrite_prompt(prompt)
                return rewritten, "llm"
            except Exception:
                return self._fallback_prompt(prompt), "fallback"

        return self._fallback_prompt(prompt), "fallback"

    async def rewrite_for_sdxl(self, user_prompt: str, use_llm: bool = True) -> str:
        final_prompt, _ = await self.build_prompt(
            user_prompt,
            mode="llm" if use_llm else "fallback",
        )
        return final_prompt
