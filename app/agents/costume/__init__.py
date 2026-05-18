"""Costume Agent.

Reviews visual candidates for costume quality including visible costume/clothing, 
outfit consistency with character, costume style coherence, genre/era/style consistency, 
clothing artifacts, and costume continuity risk.
"""

from app.agents.costume.contract import CostumeAgentContract
from app.agents.costume.reviewer import CostumeReviewer
from app.agents.costume.validator import CostumeValidator
from app.agents.costume.artifacts import CostumeArtifacts
from app.agents.costume.runner import CostumeRunner

__all__ = [
    "CostumeAgentContract",
    "CostumeReviewer",
    "CostumeValidator",
    "CostumeArtifacts",
    "CostumeRunner"
]
