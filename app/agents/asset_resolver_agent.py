import json
from pathlib import Path
from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class AssetResolverAgent(BaseRoleAgent):
    """Asset resolution and validation agent.
    
    Identifies and validates required production assets.
    Controlled asset resolution layer - no silent substitution.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["asset_resolution_required", "controlled_asset_resolution_review_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]
    
    @property
    def output_contract_type(self) -> str:
        return "ControlledAssetResolutionLayer"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        project_root = Path(context.project_root)
        # Requirements are usually created by CreativeDirector or similar in production_plan_review
        # But we search for it in output/control
        requirements_path = project_root / "output" / "control" / "combine_v2_asset_requirements_contract.json"
        
        # 1. Read asset requirements
        requirements = {}
        if requirements_path.exists():
            try:
                with open(requirements_path, 'r') as f:
                    requirements = json.load(f)
            except (json.JSONDecodeError, IOError):
                requirements = {}
        
        # 2. Local asset search stub
        # Logic: if we are in 'controlled_asset_resolution_review_required', we "resolve" everything.
        # If we are in 'asset_resolution_required', we "simulate" a missing asset to trigger review.
        
        req_assets = requirements.get("asset_requirements", {
            "characters": ["hero"],
            "environments": ["office"],
            "audio": ["voiceover", "background_music"]
        })
        
        characters = req_assets.get("characters", [])
        environments = req_assets.get("environments", [])
        audio = req_assets.get("audio", [])
        
        missing_assets = []
        # Simulate missing background_music only in the first stage to trigger review
        if context.stage == "asset_resolution_required" and "background_music" in audio:
            missing_assets.append("background_music")
            
        resolved_assets = {
            "characters": characters,
            "environments": environments,
            "audio": [a for a in audio if a not in missing_assets]
        }
        
        candidate_assets = ["candidate_bgm_01", "candidate_bgm_02"] if missing_assets else []
        rejected_candidates = ["rejected_bgm_01"] if missing_assets else []
        
        # 3. Create Inventory Contract
        inventory_contract = {
            "agent": self.role_name,
            "stage": context.stage,
            "inventory": {
                "local_repository": "f:/Assets/LocalStub",
                "available_assets": resolved_assets,
                "missing_assets": missing_assets,
                "silent_substitution_allowed": False
            }
        }
        
        # 4. Create Resolution Result
        resolution_result = {
            "agent": self.role_name,
            "stage": context.stage,
            "resolved": not bool(missing_assets),
            "missing": missing_assets,
            "candidates": candidate_assets,
            "rejected": rejected_candidates,
            "manual_review_required": bool(missing_assets),
            "no_silent_substitution": True
        }
        
        # 5. Create Gate Decision
        gate_decision = {
            "agent": self.role_name,
            "stage": context.stage,
            "pass": not bool(missing_assets),
            "download_authorized": False,
            "install_authorized": False,
            "generation_authorized": False,
            "reason": "Missing assets require operator review" if missing_assets else "All assets resolved and verified"
        }
        
        # 6. State transition logic
        next_stage = "workflow_plan_required"
        if missing_assets:
            next_stage = "controlled_asset_resolution_review_required"
            
        artifacts = [
            "combine_v2_asset_inventory_contract.json",
            "combine_v2_asset_resolution_result.json",
            "combine_v2_asset_gate_decision.json"
        ]
        
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=artifacts,
            next_recommended_stage=next_stage,
            metadata={
                "combine_v2_asset_inventory_contract": inventory_contract,
                "combine_v2_asset_resolution_result": resolution_result,
                "combine_v2_asset_gate_decision": gate_decision,
                "download_authorized": False,
                "install_authorized": False,
                "generation_performed": False,
                "comfyui_execution": False,
                "silent_substitution": False
            }
        )
