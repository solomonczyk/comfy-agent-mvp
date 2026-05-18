"""Props Agent - reviews visual candidates for props quality.

This agent is responsible for:
- Reviewing visible props
- Reviewing object placement
- Reviewing object continuity risk
- Reviewing object shape/color consistency
- Reviewing character-object interaction if visible
- Reviewing props consistency with scene/genre/production design
- Reviewing missing/extra/contradictory props
- Determining whether props are suitable to proceed to the next agent gate

Critical constraints:
- No new generation allowed
- No retry allowed
- No second candidate allowed
- No ComfyUI submit allowed
- No image editing allowed
- No object modification allowed
- No Visual QA final acceptance allowed
- No operator acceptance by agent allowed
- No assembly allowed
- No preview/final render allowed
- No voice/audio allowed
- No downstream allowed
- production_accepted must remain false
"""

from app.agents.props.contract import PropsAgentContract
from app.agents.props.validator import PropsValidator
from app.agents.props.reviewer import PropsReviewer
from app.agents.props.artifacts import PropsArtifacts
from app.agents.props.runner import PropsRunner

__all__ = [
    'PropsAgentContract',
    'PropsValidator',
    'PropsReviewer',
    'PropsArtifacts',
    'PropsRunner',
]
