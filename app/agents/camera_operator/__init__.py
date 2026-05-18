"""Camera Operator Agent - executes authorized full-frame corrective generation.

This agent is responsible for:
- Validating repaired full-frame corrective generation package
- Executing exactly one authorized ComfyUI generation
- Collecting generated asset
- Creating generation manifest and result review
- Creating operator visual review packet
- Stopping pipeline for human visual review

Critical constraints:
- Max generations: 1
- No retry allowed
- No second generation allowed
- No automatic visual acceptance
- No assembly or downstream execution
- Must stop after generation for operator visual review
"""

from app.agents.camera_operator.contract import CameraOperatorAgentContract
from app.agents.camera_operator.validator import CameraOperatorValidator
from app.agents.camera_operator.runner import CameraOperatorRunner
from app.agents.camera_operator.artifacts import CameraOperatorArtifacts

__all__ = [
    'CameraOperatorAgentContract',
    'CameraOperatorValidator',
    'CameraOperatorRunner',
    'CameraOperatorArtifacts',
]
