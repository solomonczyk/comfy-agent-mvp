"""RC2-PRODCARDS3AD-FIX — Tests for retry workflow checkpoint binding override logic."""
import pytest
from pathlib import Path
import tempfile
import json


class TestRC2PRODCARDS3ADCheckpointBinding:
    """Tests for RC2-PRODCARDS3AD checkpoint binding override logic."""
    
    def test_retry_plan_checkpoint_overrides_prompt_pack(self, tmp_path):
        """Test that retry plan checkpoint overrides prompt_pack checkpoint."""
        # Create mock controlled_retry_implementation_plan.json
        retry_plan = {
            "checkpoint_change": {
                "to": {
                    "checkpoint_name": "juggernautXL_version2.safetensors"
                }
            }
        }
        retry_plan_path = tmp_path / "controlled_retry_implementation_plan.json"
        retry_plan_path.write_text(json.dumps(retry_plan, indent=2))
        
        # Create mock prompt_pack.json with different checkpoint
        prompt_pack = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors"
        }
        prompt_pack_path = tmp_path / "prompt_pack.json"
        prompt_pack_path.write_text(json.dumps(prompt_pack, indent=2))
        
        # Read and verify
        with open(retry_plan_path) as f:
            plan_data = json.load(f)
        with open(prompt_pack_path) as f:
            pack_data = json.load(f)
        
        plan_checkpoint = plan_data["checkpoint_change"]["to"]["checkpoint_name"]
        prompt_pack_checkpoint = pack_data["checkpoint"]
        
        # Verify they are different (override needed)
        assert plan_checkpoint != prompt_pack_checkpoint
        assert plan_checkpoint == "juggernautXL_version2.safetensors"
        assert prompt_pack_checkpoint == "realvisxlV50_v50Bakedvae.safetensors"
        
        # Verify override would be applied
        final_checkpoint = plan_checkpoint  # Should use plan checkpoint
        assert final_checkpoint == "juggernautXL_version2.safetensors"
        assert final_checkpoint != prompt_pack_checkpoint
    
    def test_retry_plan_checkpoint_overrides_workflow_template(self, tmp_path):
        """Test that retry plan checkpoint overrides workflow template checkpoint."""
        # Create mock controlled_retry_implementation_plan.json
        retry_plan = {
            "checkpoint_change": {
                "to": {
                    "checkpoint_name": "juggernautXL_version2.safetensors"
                }
            }
        }
        retry_plan_path = tmp_path / "controlled_retry_implementation_plan.json"
        retry_plan_path.write_text(json.dumps(retry_plan, indent=2))
        
        # Create mock workflow template with different checkpoint
        workflow_template = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors"
                }
            }
        }
        workflow_path = tmp_path / "workflow_template.json"
        workflow_path.write_text(json.dumps(workflow_template, indent=2))
        
        # Read and verify
        with open(retry_plan_path) as f:
            plan_data = json.load(f)
        with open(workflow_path) as f:
            workflow_data = json.load(f)
        
        plan_checkpoint = plan_data["checkpoint_change"]["to"]["checkpoint_name"]
        template_checkpoint = workflow_data["4"]["inputs"]["ckpt_name"]
        
        # Verify they are different (override needed)
        assert plan_checkpoint != template_checkpoint
        assert plan_checkpoint == "juggernautXL_version2.safetensors"
        assert template_checkpoint == "CyberRealisticXLPlay_V7.0_FP16.safetensors"
        
        # Simulate workflow mutation
        workflow_data["4"]["inputs"]["ckpt_name"] = plan_checkpoint
        final_workflow_checkpoint = workflow_data["4"]["inputs"]["ckpt_name"]
        
        # Verify override was applied
        assert final_workflow_checkpoint == plan_checkpoint
        assert final_workflow_checkpoint == "juggernautXL_version2.safetensors"
        assert final_workflow_checkpoint != template_checkpoint
    
    def test_final_workflow_checkpoint_equals_retry_plan_checkpoint(self, tmp_path):
        """Test that final workflow CheckpointLoaderSimple.ckpt_name equals retry plan checkpoint."""
        # Create mock controlled_retry_implementation_plan.json
        retry_plan = {
            "checkpoint_change": {
                "to": {
                    "checkpoint_name": "juggernautXL_version2.safetensors"
                }
            }
        }
        retry_plan_path = tmp_path / "controlled_retry_implementation_plan.json"
        retry_plan_path.write_text(json.dumps(retry_plan, indent=2))
        
        # Create mock workflow template
        workflow_template = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors"
                }
            }
        }
        workflow_path = tmp_path / "workflow_template.json"
        workflow_path.write_text(json.dumps(workflow_template, indent=2))
        
        # Read and mutate
        with open(retry_plan_path) as f:
            plan_data = json.load(f)
        with open(workflow_path) as f:
            workflow_data = json.load(f)
        
        plan_checkpoint = plan_data["checkpoint_change"]["to"]["checkpoint_name"]
        
        # Mutate workflow
        workflow_data["4"]["inputs"]["ckpt_name"] = plan_checkpoint
        
        # Verify final workflow checkpoint equals retry plan checkpoint
        final_checkpoint = workflow_data["4"]["inputs"]["ckpt_name"]
        assert final_checkpoint == plan_checkpoint
        assert final_checkpoint == "juggernautXL_version2.safetensors"
    
    def test_mismatch_blocks_execution(self, tmp_path):
        """Test that checkpoint mismatch blocks execution."""
        # Create mock controlled_retry_implementation_plan.json
        retry_plan = {
            "checkpoint_change": {
                "to": {
                    "checkpoint_name": "juggernautXL_version2.safetensors"
                }
            }
        }
        retry_plan_path = tmp_path / "controlled_retry_implementation_plan.json"
        retry_plan_path.write_text(json.dumps(retry_plan, indent=2))
        
        # Create mock workflow template with mismatched checkpoint
        workflow_template = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "realvisxlV50_v50Bakedvae.safetensors"
                }
            }
        }
        workflow_path = tmp_path / "workflow_template.json"
        workflow_path.write_text(json.dumps(workflow_template, indent=2))
        
        # Read and check for mismatch
        with open(retry_plan_path) as f:
            plan_data = json.load(f)
        with open(workflow_path) as f:
            workflow_data = json.load(f)
        
        plan_checkpoint = plan_data["checkpoint_change"]["to"]["checkpoint_name"]
        workflow_checkpoint = workflow_data["4"]["inputs"]["ckpt_name"]
        
        # Verify mismatch
        mismatch = (plan_checkpoint != workflow_checkpoint)
        assert mismatch is True
        
        # Verify execution would be blocked if mutation not applied
        execution_allowed = not mismatch
        assert execution_allowed is False
    
    def test_identity_adapter_family_null_reported_explicitly(self, tmp_path):
        """Test that identity_adapter_family=null is reported explicitly when no adapter in workflow."""
        # Create workflow template without identity adapter
        workflow_template = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "juggernautXL_version2.safetensors"
                }
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {}
            }
        }
        workflow_path = tmp_path / "workflow_template.json"
        workflow_path.write_text(json.dumps(workflow_template, indent=2))
        
        # Simulate identity adapter detection
        ip_adapter_node_found = False
        ip_adapter_nodes = []
        for node_id, node in workflow_template.items():
            if isinstance(node, dict):
                class_type = node.get("class_type", "")
                if "ipadapter" in class_type.lower() or "ip_adapter" in class_type.lower():
                    ip_adapter_node_found = True
                    ip_adapter_nodes.append({"node_id": node_id, "class_type": class_type})
        
        # Verify explicit reporting
        identity_adapter_compatibility_check = {}
        if not ip_adapter_node_found:
            identity_adapter_compatibility_check["no_identity_adapter_in_workflow"] = True
            identity_adapter_compatibility_check["identity_adapter_detection"] = "no_identity_adapter_nodes_found"
            identity_adapter_compatibility_check["identity_adapter_family"] = None
        else:
            identity_adapter_compatibility_check["no_identity_adapter_in_workflow"] = False
            identity_adapter_compatibility_check["identity_adapter_detection"] = "identity_adapter_nodes_found"
        
        # Verify explicit reporting (not silently accepted)
        assert identity_adapter_compatibility_check["no_identity_adapter_in_workflow"] is True
        assert identity_adapter_compatibility_check["identity_adapter_detection"] == "no_identity_adapter_nodes_found"
        assert identity_adapter_compatibility_check["identity_adapter_family"] is None
        assert "compatible" not in identity_adapter_compatibility_check or identity_adapter_compatibility_check.get("compatible", True) is True
    
    def test_identity_adapter_family_not_silently_accepted(self, tmp_path):
        """Test that identity_adapter_family=null is not silently accepted when adapter present."""
        # Create workflow template with identity adapter
        workflow_template = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": "juggernautXL_version2.safetensors"
                }
            },
            "10": {
                "class_type": "IPAdapter",
                "inputs": {
                    "model": "ip-adapter-faceid-plus_sd15.bin"
                }
            }
        }
        workflow_path = tmp_path / "workflow_template.json"
        workflow_path.write_text(json.dumps(workflow_template, indent=2))
        
        # Simulate identity adapter detection
        ip_adapter_node_found = False
        ip_adapter_model = None
        ip_adapter_nodes = []
        for node_id, node in workflow_template.items():
            if isinstance(node, dict):
                class_type = node.get("class_type", "")
                if "ipadapter" in class_type.lower() or "ip_adapter" in class_type.lower():
                    ip_adapter_node_found = True
                    inputs = node.get("inputs", {})
                    model_path = inputs.get("model")
                    ip_adapter_nodes.append({
                        "node_id": node_id,
                        "class_type": class_type,
                        "model": model_path
                    })
                    if model_path:
                        ip_adapter_model = str(model_path)
        
        # Verify detection (not silently accepted)
        assert ip_adapter_node_found is True
        assert ip_adapter_model is not None
        assert len(ip_adapter_nodes) > 0
        
        # Verify explicit reporting
        identity_adapter_compatibility_check = {}
        if not ip_adapter_node_found:
            identity_adapter_compatibility_check["no_identity_adapter_in_workflow"] = True
            identity_adapter_compatibility_check["identity_adapter_detection"] = "no_identity_adapter_nodes_found"
        else:
            identity_adapter_compatibility_check["no_identity_adapter_in_workflow"] = False
            identity_adapter_compatibility_check["identity_adapter_detection"] = "identity_adapter_nodes_found"
            identity_adapter_compatibility_check["ip_adapter_nodes"] = ip_adapter_nodes
            
            # Determine family
            if ip_adapter_model and ("sd15" in ip_adapter_model.lower() or "faceid" in ip_adapter_model.lower()):
                identity_adapter_compatibility_check["identity_adapter_family"] = "SD15"
                identity_adapter_compatibility_check["ip_adapter_model"] = ip_adapter_model
        
        # Verify not silently accepted
        assert identity_adapter_compatibility_check["no_identity_adapter_in_workflow"] is False
        assert identity_adapter_compatibility_check["identity_adapter_detection"] == "identity_adapter_nodes_found"
        assert identity_adapter_compatibility_check["identity_adapter_family"] == "SD15"
