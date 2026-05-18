"""Actor / Character Control Agent - reviews visual candidates for actor/character quality.

This agent is responsible for:
- Reviewing face quality
- Reviewing eyes for artifacts
- Reviewing mouth/teeth for artifacts
- Reviewing skin realism
- Reviewing expression/mood consistency
- Reviewing anatomy/body consistency if visible
- Reviewing identity/style consistency
- Determining whether the character is suitable to proceed to the next gate

Critical constraints:
- No new generation allowed
- No retry allowed
- No second candidate allowed
- No ComfyUI submit allowed
- No image editing allowed
- No Visual QA final acceptance allowed
- No operator acceptance by agent allowed
- No assembly allowed
- No preview/final render allowed
- No voice/audio allowed
- No downstream allowed
- production_accepted must remain false
"""

from app.agents.actor_character_control.contract import ActorCharacterControlAgentContract
from app.agents.actor_character_control.validator import ActorCharacterValidator
from app.agents.actor_character_control.reviewer import ActorCharacterReviewer
from app.agents.actor_character_control.artifacts import ActorCharacterArtifacts
from app.agents.actor_character_control.runner import ActorCharacterRunner

__all__ = [
    'ActorCharacterControlAgentContract',
    'ActorCharacterValidator',
    'ActorCharacterReviewer',
    'ActorCharacterArtifacts',
    'ActorCharacterRunner',
]
