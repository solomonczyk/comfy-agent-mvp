"""Visual Reference Curator Agent - manages canonical references and corrective packages.

RC-COMBINE-V2-VISUAL-REFERENCE-CURATOR-AGENT-001
"""

from .contract import VisualReferenceCuratorContract
from .classifier import ReferenceClassifier
from .runner import VisualReferenceCuratorRunner
from .artifacts import VisualReferenceCuratorArtifacts

__all__ = [
    "VisualReferenceCuratorContract",
    "ReferenceClassifier",
    "VisualReferenceCuratorRunner",
    "VisualReferenceCuratorArtifacts",
]
