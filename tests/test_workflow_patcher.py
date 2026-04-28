"""Tests for WorkflowPatcher."""
import pytest

from app.comfy.workflow_patcher import WorkflowPatcher


class TestWorkflowPatcher:
    """Test suite for WorkflowPatcher."""

    def test_patch_ksampler_nodes_returns_new_dict_does_not_mutate_input(self):
        """Test that patch_ksampler_nodes returns a new dict and does not mutate input."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.96,
                    "cfg": 6.0,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["16", 0],
                },
            }
        }
        original_workflow = workflow.copy()
        original_inputs = workflow["3"]["inputs"].copy()

        result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3"])

        # Verify input was not mutated
        assert workflow == original_workflow
        assert workflow["3"]["inputs"] == original_inputs
        # Verify result is a different object
        assert result is not workflow
        assert result["3"] is not workflow["3"]

    def test_denoise_above_threshold_gets_patched(self):
        """Test that denoise > 0.95 gets patched to 0.75."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.96,
                    "cfg": 6.0,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["16", 0],
                },
            }
        }

        result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3"])

        assert result["3"]["inputs"]["denoise"] == 0.75

    def test_denoise_below_threshold_unchanged(self):
        """Test that denoise <= 0.95 is left unchanged."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.9,
                    "cfg": 6.0,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["16", 0],
                },
            }
        }

        result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3"])

        assert result["3"]["inputs"]["denoise"] == 0.9

    def test_cfg_below_threshold_gets_patched(self):
        """Test that cfg < 3.0 gets patched to 7.0."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.96,
                    "cfg": 2.0,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["16", 0],
                },
            }
        }

        result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3"])

        assert result["3"]["inputs"]["cfg"] == 7.0

    def test_multiple_node_ids_patched_in_one_call(self):
        """Test that multiple node IDs are patched in one call."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.96,
                    "cfg": 2.0,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["16", 0],
                },
            },
            "10": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.97,
                    "cfg": 2.5,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["17", 0],
                },
            },
            "13": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.98,
                    "cfg": 1.0,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["18", 0],
                },
            },
        }

        result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3", "10", "13"])

        assert result["3"]["inputs"]["denoise"] == 0.75
        assert result["3"]["inputs"]["cfg"] == 7.0
        assert result["10"]["inputs"]["denoise"] == 0.75
        assert result["10"]["inputs"]["cfg"] == 7.0
        assert result["13"]["inputs"]["denoise"] == 0.75
        assert result["13"]["inputs"]["cfg"] == 7.0

    def test_unknown_node_id_skipped_without_error(self):
        """Test that unknown node ID is skipped without error."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.96,
                    "cfg": 6.0,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["16", 0],
                },
            }
        }

        # Should not raise an exception
        result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3", "999"])

        # Node 3 sampler should be overridden to fast default
        assert result["3"]["inputs"]["sampler_name"] == "dpmpp_sde"
        assert result["3"]["inputs"]["scheduler"] == "karras"
        # Node 999 should not exist in result
        assert "999" not in result

    def test_non_ksampler_node_skipped(self):
        """Test that non-KSampler nodes are skipped."""
        workflow = {
            "3": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["2", 0],
                    "vae": ["4", 2],
                },
            }
        }

        # Should not raise an exception
        result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3"])

        # Node should remain unchanged
        assert result["3"]["class_type"] == "VAEDecode"

    def test_missing_positive_conditioning_logged(self, caplog):
        """Test that missing positive conditioning is logged."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.96,
                    "cfg": 6.0,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "negative": ["7", 0],
                    "latent_image": ["16", 0],
                },
            }
        }

        with caplog.at_level("WARNING"):
            result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3"])

        assert "positive conditioning is missing or empty" in caplog.text

    def test_missing_negative_conditioning_logged(self, caplog):
        """Test that missing negative conditioning is logged."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.96,
                    "cfg": 6.0,
                    "steps": 20,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "latent_image": ["16", 0],
                },
            }
        }

        with caplog.at_level("WARNING"):
            result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3"])

        assert "negative conditioning is missing or empty" in caplog.text

    def test_patch_resolution_4_3(self):
        """Test that patch_resolution sets 640x480 for 4:3."""
        workflow = {
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            }
        }
        result = WorkflowPatcher.patch_resolution(workflow, "4:3")
        assert result["5"]["inputs"]["width"] == 640
        assert result["5"]["inputs"]["height"] == 480

    def test_patch_resolution_16_9(self):
        """Test that patch_resolution sets 768x432 for 16:9."""
        workflow = {
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            }
        }
        result = WorkflowPatcher.patch_resolution(workflow, "16:9")
        assert result["5"]["inputs"]["width"] == 768
        assert result["5"]["inputs"]["height"] == 432

    def test_patch_resolution_1_1(self):
        """Test that patch_resolution sets 512x512 for 1:1."""
        workflow = {
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 1024, "height": 768, "batch_size": 1},
            }
        }
        result = WorkflowPatcher.patch_resolution(workflow, "1:1")
        assert result["5"]["inputs"]["width"] == 512
        assert result["5"]["inputs"]["height"] == 512

    def test_patch_resolution_unknown_falls_back_to_4_3(self):
        """Test that unknown aspect ratio falls back to 4:3 (640x480)."""
        workflow = {
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            }
        }
        result = WorkflowPatcher.patch_resolution(workflow, "99:1")
        assert result["5"]["inputs"]["width"] == 640
        assert result["5"]["inputs"]["height"] == 480

    def test_steps_above_threshold_gets_patched(self):
        """Test that steps > 25 gets patched to 6."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.5,
                    "cfg": 6.0,
                    "steps": 26,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            }
        }
        result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3"])
        assert result["3"]["inputs"]["steps"] == 6

    def test_steps_at_or_below_threshold_unchanged(self):
        """Test that steps <= 6 is left unchanged."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "denoise": 0.5,
                    "cfg": 6.0,
                    "steps": 6,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            }
        }
        result = WorkflowPatcher.patch_ksampler_nodes(workflow, ["3"])
        assert result["3"]["inputs"]["steps"] == 6

    def test_patch_checkpoint_sets_correct_field(self):
        """Test that patch_checkpoint sets ckpt_name on CheckpointLoaderSimple."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "realvisxlV50_v50Bakedvae.safetensors"},
            }
        }
        result = WorkflowPatcher.patch_checkpoint(workflow, "realisticVisionV60B1_v51VAE.safetensors")
        assert result["4"]["inputs"]["ckpt_name"] == "realisticVisionV60B1_v51VAE.safetensors"

    def test_patch_checkpoint_does_not_mutate_input(self):
        """Test that patch_checkpoint mutates in place but returns same dict."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "old.safetensors"},
            }
        }
        original_id = id(workflow)
        result = WorkflowPatcher.patch_checkpoint(workflow, "new.safetensors")
        assert id(result) == original_id
        assert result["4"]["inputs"]["ckpt_name"] == "new.safetensors"

    def test_patch_checkpoint_no_checkpoint_node_is_noop(self):
        """Test that patch_checkpoint with no matching node is a noop."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 20},
            }
        }
        result = WorkflowPatcher.patch_checkpoint(workflow, "some.safetensors")
        assert "ckpt_name" not in result["3"]["inputs"]

    def test_patch_checkpoint_injects_cyber_realistic_xl(self):
        """Test that patch_checkpoint correctly injects CyberRealisticXLPlay checkpoint."""
        checkpoint = "CyberRealisticXLPlay_V7.0_FP16.safetensors"
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "old_model.safetensors"},
            }
        }
        result = WorkflowPatcher.patch_checkpoint(workflow, checkpoint)
        assert result["4"]["inputs"]["ckpt_name"] == checkpoint

    def test_patch_resolution_9_16(self):
        """Test that patch_resolution sets 480x640 for 9:16 vertical format."""
        workflow = {
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            }
        }
        result = WorkflowPatcher.patch_resolution(workflow, "9:16")
        assert result["5"]["inputs"]["width"] == 480
        assert result["5"]["inputs"]["height"] == 640

    # ── strip_ipadapter ───────────────────────────────────────────────────────

    def _full_ipadapter_workflow(self):
        """Workflow with checkpoint + IPAdapter chain + KSampler pointing at node 20."""
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 1, "steps": 20, "cfg": 7.0,
                    "sampler_name": "euler", "scheduler": "karras",
                    "denoise": 1.0, "model": ["20", 0],
                    "positive": ["6", 0], "negative": ["7", 0],
                    "latent_image": ["5", 0],
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "20": {
                "class_type": "IPAdapterAdvanced",
                "inputs": {"model": ["21", 0], "ipadapter": ["21", 1], "image": ["22", 0], "weight": 0.6},
            },
            "21": {
                "class_type": "IPAdapterUnifiedLoader",
                "inputs": {"model": ["4", 0], "preset": "PLUS (high strength)"},
            },
            "22": {
                "class_type": "LoadImage",
                "inputs": {"image": "", "upload": "image"},
            },
        }

    def test_strip_ipadapter_removes_nodes(self):
        """strip_ipadapter removes nodes 20, 21, 22."""
        wf = self._full_ipadapter_workflow()
        WorkflowPatcher.strip_ipadapter(wf)
        assert "20" not in wf
        assert "21" not in wf
        assert "22" not in wf

    def test_strip_ipadapter_preserves_non_ipadapter_nodes(self):
        """strip_ipadapter keeps KSampler, checkpoint, etc."""
        wf = self._full_ipadapter_workflow()
        WorkflowPatcher.strip_ipadapter(wf)
        assert "3" in wf
        assert "4" in wf

    def test_strip_ipadapter_reconnects_ksampler_model(self):
        """KSampler model input is reconnected to checkpoint node."""
        wf = self._full_ipadapter_workflow()
        WorkflowPatcher.strip_ipadapter(wf)
        assert wf["3"]["inputs"]["model"] == ["4", 0]

    def test_strip_ipadapter_workflow_without_ipadapter_is_noop(self):
        """Calling strip on a workflow with no IPAdapter nodes is safe."""
        wf = {
            "3": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "steps": 20}},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "x.safetensors"}},
        }
        WorkflowPatcher.strip_ipadapter(wf)
        assert "3" in wf and "4" in wf
        assert wf["3"]["inputs"]["model"] == ["4", 0]

    def test_strip_ipadapter_returns_workflow(self):
        """strip_ipadapter returns the same workflow dict."""
        wf = self._full_ipadapter_workflow()
        result = WorkflowPatcher.strip_ipadapter(wf)
        assert result is wf

    # ── patch_ipadapter ───────────────────────────────────────────────────────

    def _ipadapter_workflow(self):
        """Helper: minimal workflow with IPAdapterAdvanced + LoadImage nodes."""
        return {
            "20": {
                "class_type": "IPAdapterAdvanced",
                "inputs": {
                    "model": ["4", 0],
                    "ipadapter": ["21", 0],
                    "image": ["22", 0],
                    "weight": 0.6,
                    "weight_type": "linear",
                },
            },
            "21": {
                "class_type": "IPAdapterUnifiedLoader",
                "inputs": {"preset": "PLUS (high strength)", "model": ["4", 0]},
            },
            "22": {
                "class_type": "LoadImage",
                "inputs": {"image": "", "upload": "image"},
            },
        }

    def test_patch_ipadapter_sets_weight(self, tmp_path):
        """patch_ipadapter sets the weight on the IPAdapter node."""
        from pathlib import Path
        workflow = self._ipadapter_workflow()
        ref = tmp_path / "grid.png"
        ref.write_bytes(b"PNG")
        WorkflowPatcher.patch_ipadapter(workflow, ref, weight=0.42)
        assert workflow["20"]["inputs"]["weight"] == 0.42

    def test_patch_ipadapter_sets_image_path(self, tmp_path):
        """patch_ipadapter sets the LoadImage image field to the resolved path."""
        from pathlib import Path
        workflow = self._ipadapter_workflow()
        ref = tmp_path / "Alia_reference_grid.png"
        ref.write_bytes(b"PNG")
        WorkflowPatcher.patch_ipadapter(workflow, ref, weight=0.6)
        img_field = workflow["22"]["inputs"]["image"]
        assert str(ref.resolve()).replace("\\", "/") == img_field

    def test_patch_ipadapter_does_not_mutate_separate_copy(self, tmp_path):
        """patch_ipadapter mutates in-place; a deepcopy is unaffected."""
        import copy
        workflow = self._ipadapter_workflow()
        original = copy.deepcopy(workflow)
        ref = tmp_path / "grid.png"
        ref.write_bytes(b"PNG")
        WorkflowPatcher.patch_ipadapter(workflow, ref, weight=0.9)
        # original is not changed
        assert original["20"]["inputs"]["weight"] == 0.6
        assert original["22"]["inputs"]["image"] == ""

    def test_patch_ipadapter_missing_node_logs_warning_no_exception(self, tmp_path, caplog):
        """No IPAdapter node → warning logged, no exception raised."""
        from pathlib import Path
        workflow = {
            "3": {"class_type": "KSampler", "inputs": {"steps": 20}},
        }
        ref = tmp_path / "grid.png"
        ref.write_bytes(b"PNG")
        with caplog.at_level("WARNING"):
            result = WorkflowPatcher.patch_ipadapter(workflow, ref)
        assert "no IPAdapter node found" in caplog.text
        assert result is workflow  # same object returned

    def test_patch_ipadapter_default_weight_is_0_6(self, tmp_path):
        """Default weight parameter is 0.6."""
        workflow = self._ipadapter_workflow()
        ref = tmp_path / "grid.png"
        ref.write_bytes(b"PNG")
        WorkflowPatcher.patch_ipadapter(workflow, ref)
        assert workflow["20"]["inputs"]["weight"] == 0.6

    def test_patch_ipadapter_returns_workflow(self, tmp_path):
        """patch_ipadapter returns the workflow dict."""
        workflow = self._ipadapter_workflow()
        ref = tmp_path / "grid.png"
        ref.write_bytes(b"PNG")
        result = WorkflowPatcher.patch_ipadapter(workflow, ref)
        assert result is workflow

    # ── patch_reference_image (MK-REF1R-4) ─────────────────────────────────────

    def test_patch_reference_image_rewires_ksampler_to_vaeencode(self):
        """MK-REF1R-4: patch_reference_image rewires KSampler.latent_image to VAEEncode output."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 1,
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["10", 0],  # Initially connected to EmptyLatentImage
                },
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "5": {
                "class_type": "LoadImage",
                "inputs": {"image": "", "upload": "image"},
            },
            "8": {
                "class_type": "VAEEncode",
                "inputs": {"pixels": ["5", 0], "vae": ["4", 2]},
            },
            "10": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
        }

        result, original, staged, _ = WorkflowPatcher.patch_reference_image(workflow, "F:/references/alya.png", denoise=0.42)

        # Verify LoadImage is patched with reference path
        assert result["5"]["inputs"]["image"] == "F:/references/alya.png"

        # Verify KSampler denoise is set
        assert result["3"]["inputs"]["denoise"] == 0.42

        # MK-REF1R-4: Verify KSampler.latent_image is rewired to VAEEncode
        assert result["3"]["inputs"]["latent_image"] == ["8", 0]

    def test_patch_reference_image_without_vaeencode_logs_warning(self, caplog):
        """MK-REF1R-4: patch_reference_image logs warning if VAEEncode not found."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {"latent_image": ["10", 0], "denoise": 1.0},
            },
            "5": {
                "class_type": "LoadImage",
                "inputs": {"image": ""},
            },
            "10": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
        }

        with caplog.at_level("WARNING"):
            _, _, _, _ = WorkflowPatcher.patch_reference_image(workflow, "F:/references/alya.png")

        assert "No VAEEncode node found" in caplog.text
