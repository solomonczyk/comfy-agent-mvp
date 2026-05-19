"""Identity Lock Agent - preserves canonical character identity during generation.

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from .contract import IdentityLockContract
from .runner import IdentityLockRunner

__all__ = ["IdentityLockContract", "IdentityLockRunner"]
