"""
RC-COMBINE-V2-BRAIN-ENABLED-PREVIEW-REPAIR-ARCHITECT-001
Brain call contracts — type definitions for brain request/response contracts.

Brain output is advisory only:
  - brain_response_used_as_advisory: true
  - deterministic_validation_required: true
  - brain_may_not_update_state_directly: true
  - brain_may_not_accept_visual_result: true
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class BrainCallContract:
    """Contract governing a single brain API call.

    Enforces deterministic validation:
    - Brain output is advisory, not authoritative
    - Brain may not update state directly
    - Brain may not accept visual results
    - All brain outputs must pass deterministic validation
    """

    task_id: str = ""
    agent_id: str = ""
    brain_call_count: int = 0
    brain_response_used_as_advisory: bool = True
    deterministic_validation_required: bool = True
    brain_may_not_update_state_directly: bool = True
    brain_may_not_accept_visual_result: bool = True
    max_tokens: int = 4096
    request_timestamp: str = ""
    response_timestamp: str = ""
    request_data: dict = field(default_factory=dict)
    response_data: Optional[dict] = None
    validation_result: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "brain_call_count": self.brain_call_count,
            "brain_response_used_as_advisory": self.brain_response_used_as_advisory,
            "deterministic_validation_required": self.deterministic_validation_required,
            "brain_may_not_update_state_directly": self.brain_may_not_update_state_directly,
            "brain_may_not_accept_visual_result": self.brain_may_not_accept_visual_result,
            "max_tokens": self.max_tokens,
            "request_timestamp": self.request_timestamp,
            "response_timestamp": self.response_timestamp,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "validation_result": self.validation_result,
        }


class BrainCallContractBuilder:
    """Builder for constructing brain call contracts."""

    def __init__(self, task_id: str, agent_id: str):
        self._contract = BrainCallContract(
            task_id=task_id,
            agent_id=agent_id,
            request_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def with_request_data(self, data: dict) -> "BrainCallContractBuilder":
        self._contract.request_data = data
        return self

    def with_brain_call_count(self, count: int) -> "BrainCallContractBuilder":
        self._contract.brain_call_count = count
        return self

    def with_max_tokens(self, tokens: int) -> "BrainCallContractBuilder":
        self._contract.max_tokens = tokens
        return self

    def record_response(self, response: dict) -> "BrainCallContractBuilder":
        self._contract.response_data = response
        self._contract.response_timestamp = datetime.now(
            timezone.utc
        ).isoformat()
        return self

    def with_validation(self, validation: dict) -> "BrainCallContractBuilder":
        self._contract.validation_result = validation
        return self

    def build(self) -> BrainCallContract:
        return self._contract
