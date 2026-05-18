"""Set Decorator Agent - reviews visual candidates for set decoration quality.

This agent is responsible for:
- Reviewing set dressing
- Reviewing background objects
- Reviewing decoration coherence
- Reviewing background clutter / distracting objects
- Reviewing decoration continuity
- Reviewing consistency with production design
- Reviewing scene support/readability
- Determining whether the set details support the scene

Critical constraints:
- No new generation allowed
- No retry allowed
- No second candidate allowed
- No ComfyUI submit allowed
- No image editing allowed
- No set/background modification allowed
- No Visual QA final acceptance allowed
- No operator acceptance by agent allowed
- No assembly allowed
- No preview/final render allowed
- No voice/audio allowed
- No downstream allowed
- production_accepted must remain false
"""

from app.agents.set_decorator.contract import SetDecoratorAgentContract
from app.agents.set_decorator.validator import SetDecoratorValidator
from app.agents.set_decorator.reviewer import SetDecoratorReviewer
from app.agents.set_decorator.artifacts import SetDecoratorArtifacts
from app.agents.set_decorator.runner import SetDecoratorRunner

__all__ = [
    'SetDecoratorAgentContract',
    'SetDecoratorValidator',
    'SetDecoratorReviewer',
    'SetDecoratorArtifacts',
    'SetDecoratorRunner',
]
