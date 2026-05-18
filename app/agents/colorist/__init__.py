"""Colorist Agent - reviews visual candidates for color/lighting quality.

This agent is responsible for:
- Reviewing color consistency
- Reviewing contrast
- Reviewing exposure
- Reviewing brightness
- Reviewing saturation/color palette
- Reviewing skin tone risk if face/skin visible
- Reviewing mood consistency
- Reviewing cinematic look consistency
- Reviewing visual tone
- Determining whether the image is suitable to proceed to the next gate

Critical constraints:
- No new generation allowed
- No retry allowed
- No second candidate allowed
- No ComfyUI submit allowed
- No image editing allowed
- No color grading output file allowed
- No Visual QA final acceptance allowed
- No operator acceptance by agent allowed
- No assembly allowed
- No preview/final render allowed
- No voice/audio allowed
- No downstream allowed
- production_accepted must remain false
"""

from app.agents.colorist.contract import ColoristAgentContract
from app.agents.colorist.validator import ColoristValidator
from app.agents.colorist.reviewer import ColoristReviewer
from app.agents.colorist.artifacts import ColoristArtifacts
from app.agents.colorist.runner import ColoristRunner

__all__ = [
    'ColoristAgentContract',
    'ColoristValidator',
    'ColoristReviewer',
    'ColoristArtifacts',
    'ColoristRunner',
]
