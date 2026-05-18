"""Production Designer Agent - reviews visual candidates for production design quality.

This agent is responsible for:
- Reviewing visual world
- Reviewing location/environment
- Reviewing set design
- Reviewing decor and background coherence
- Reviewing genre/era consistency
- Reviewing atmosphere
- Reviewing scene support/readiness
- Determining whether the environment supports the intended scene

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

from app.agents.production_designer.contract import ProductionDesignerAgentContract
from app.agents.production_designer.validator import ProductionDesignerValidator
from app.agents.production_designer.reviewer import ProductionDesignerReviewer
from app.agents.production_designer.artifacts import ProductionDesignerArtifacts
from app.agents.production_designer.runner import ProductionDesignerRunner

__all__ = [
    'ProductionDesignerAgentContract',
    'ProductionDesignerValidator',
    'ProductionDesignerReviewer',
    'ProductionDesignerArtifacts',
    'ProductionDesignerRunner',
]
