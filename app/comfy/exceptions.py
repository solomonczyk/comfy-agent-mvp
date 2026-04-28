"""ComfyUI submission exceptions."""
from __future__ import annotations


class ComfySubmitError(RuntimeError):
    pass


class ComfyTimeoutError(RuntimeError):
    pass
