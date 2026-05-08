"""QA Canon Engine MVP.

A scalable Visual QA system that does not require collecting reference assets
for every possible object in advance. Supports universal visual quality rules,
domain-specific canons, task-specific visual contracts, defect taxonomy,
OpenCV-based technical region checks where available, and operator feedback memory.
"""

from app.qa.qa_canon_engine import QACanonEngine, QADecision

__all__ = ["QACanonEngine", "QADecision"]
