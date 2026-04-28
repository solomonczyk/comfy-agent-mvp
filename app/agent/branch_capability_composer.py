"""Capability composition layer for branch execution.

This module provides a builder/composer for creating BranchAdapterDependencies,
extracting composition logic from workflow_agent_service.py.
"""

from typing import Any

from app.agent.branch_service_capabilities import BranchAdapterDependencies
from app.agent.branch_capability_impls import (
    ServiceAttemptRunnerCapability,
    ServiceSwitchRunnerCapability,
    ServiceCandidateSelectionCapability,
    ServiceHistoryManagementCapability,
)


class BranchCapabilityComposer:
    """Composer for creating branch adapter dependencies.
    
    This class extracts composition logic from the service,
    allowing workflow_agent_service.py to remain thin.
    """
    
    def __init__(self, service: Any):
        """Initialize composer with service reference.
        
        Args:
            service: WorkflowAgentService instance for capability implementations
        """
        self.service = service
    
    def compose_dependencies(self) -> BranchAdapterDependencies:
        """Compose BranchAdapterDependencies from service.
        
        Returns:
            BranchAdapterDependencies bundle with concrete capability implementations
        """
        return BranchAdapterDependencies(
            attempt_runner=ServiceAttemptRunnerCapability(self.service),
            switch_runner=ServiceSwitchRunnerCapability(self.service),
            selection_reader=ServiceCandidateSelectionCapability(self.service),
            history_writer=ServiceHistoryManagementCapability(self.service),
        )
