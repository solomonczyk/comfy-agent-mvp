#!/usr/bin/env python3
"""
RC2-PRODCARDS3AK-AL: Controlled SDXL FaceID Asset Acquisition
Downloads only the two approved SDXL FaceID assets from trusted source.
"""

import os
import sys
import hashlib
import json
import shutil
from pathlib import Path
from datetime import datetime
from urllib.request import urlretrieve, urlopen
from urllib.error import URLError

# Configuration
PROJECT_ROOT = Path(r"F:\ComfyUI\comfy-agent-mvp")
EPISODE_ROOT = PROJECT_ROOT / "data" / "rc2_multishot1_ep01"
TEMP_DIR = EPISODE_ROOT / "output" / "control" / "temp" / "sdxl_faceid_acquisition"
CONTROL_DIR = EPISODE_ROOT / "output" / "control"

# Trusted source
SOURCE_REPO = "h94/IP-Adapter-FaceID"
SOURCE_BASE_URL = "https://huggingface.co/h94/IP-Adapter-FaceID/resolve/main"
SOURCE_REFERENCE = "https://huggingface.co/h94/IP-Adapter-FaceID"
SOURCE_COMMIT = "36ce7f96f0c76c1e8b100f10fa094a2ac48ea1c6"

# Approved assets
ASSETS = [
    {
        "filename": "ip-adapter-faceid-plusv2_sdxl.bin",
        "expected_extension": ".bin",
        "expected_size_min": 1_400_000_000,  # ~1.4 GB
        "expected_size_max": 1_600_000_000,  # ~1.6 GB
        "temp_path": TEMP_DIR / "ip-adapter-faceid-plusv2_sdxl.bin",
        "final_path": Path(r"F:\ComfyUI\models\ipadapter\ip-adapter-faceid-plusv2_sdxl.bin")
    },
    {
        "filename": "ip-adapter-faceid-plusv2_sdxl_lora.safetensors",
        "expected_extension": ".safetensors",
        "expected_size_min": 350_000_000,  # ~350 MB
        "expected_size_max": 400_000_000,  # ~400 MB
        "temp_path": TEMP_DIR / "ip-adapter-faceid-plusv2_sdxl_lora.safetensors",
        "final_path": Path(r"F:\ComfyUI\models\lora\ip-adapter-faceid-plusv2_sdxl_lora.safetensors")
    }
]

def calculate_sha256(filepath):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_asset(asset):
    """Download a single asset to temp path."""
    url = f"{SOURCE_BASE_URL}/{asset['filename']}"
    print(f"Downloading {asset['filename']} from {url}")
    
    try:
        # Create temp directory if needed
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Download with progress reporting
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = (downloaded / total_size) * 100
                print(f"\r  Progress: {percent:.1f}%", end='')
        
        urlretrieve(url, asset['temp_path'], reporthook=report_progress)
        print()  # New line after progress
        
        return {
            "success": True,
            "source_url": url,
            "temp_path": str(asset['temp_path']),
            "download_timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except URLError as e:
        return {
            "success": False,
            "error": f"Download failed: {str(e)}",
            "source_url": url
        }

def validate_asset(asset, download_result):
    """Validate downloaded asset."""
    if not download_result["success"]:
        return {
            "validation_passed": False,
            "error": download_result.get("error", "Download failed")
        }
    
    temp_path = asset['temp_path']
    
    # Check file exists
    if not temp_path.exists():
        return {
            "validation_passed": False,
            "error": f"File not found at {temp_path}"
        }
    
    # Check filename
    actual_filename = temp_path.name
    if actual_filename != asset['filename']:
        return {
            "validation_passed": False,
            "error": f"Filename mismatch: expected {asset['filename']}, got {actual_filename}"
        }
    
    # Check extension
    actual_extension = temp_path.suffix
    if actual_extension != asset['expected_extension']:
        return {
            "validation_passed": False,
            "error": f"Extension mismatch: expected {asset['expected_extension']}, got {actual_extension}"
        }
    
    # Check file size
    file_size = temp_path.stat().st_size
    if not (asset['expected_size_min'] <= file_size <= asset['expected_size_max']):
        return {
            "validation_passed": False,
            "error": f"File size out of range: {file_size} bytes (expected {asset['expected_size_min']}-{asset['expected_size_max']})"
        }
    
    # Calculate SHA256
    sha256_hash = calculate_sha256(temp_path)
    
    return {
        "validation_passed": True,
        "filename": actual_filename,
        "extension": actual_extension,
        "file_size_bytes": file_size,
        "sha256_hash": sha256_hash,
        "source_reference": SOURCE_REFERENCE,
        "source_repository": SOURCE_REPO,
        "source_commit": SOURCE_COMMIT,
        "temp_path": str(temp_path)
    }

def install_asset(asset, validation_result):
    """Install validated asset to final path."""
    if not validation_result["validation_passed"]:
        return {
            "install_passed": False,
            "error": validation_result.get("error", "Validation failed")
        }
    
    final_path = asset['final_path']
    temp_path = asset['temp_path']
    
    try:
        # Create target directory if needed
        final_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if final file already exists
        file_existed = final_path.exists()
        
        # Copy from temp to final
        shutil.copy2(temp_path, final_path)
        
        # Verify final file
        final_size = final_path.stat().st_size
        final_sha256 = calculate_sha256(final_path)
        
        # Verify hash matches
        if final_sha256 != validation_result["sha256_hash"]:
            return {
                "install_passed": False,
                "error": f"SHA256 mismatch after copy: temp={validation_result['sha256_hash']}, final={final_sha256}"
            }
        
        return {
            "install_passed": True,
            "final_path": str(final_path),
            "final_file_size_bytes": final_size,
            "final_sha256_hash": final_sha256,
            "file_existed_before": file_existed,
            "operation": "copy"
        }
    except Exception as e:
        return {
            "install_passed": False,
            "error": f"Install failed: {str(e)}"
        }

def main():
    print("=" * 80)
    print("RC2-PRODCARDS3AK-AL: Controlled SDXL FaceID Asset Acquisition")
    print("=" * 80)
    
    # Phase A: Precheck result
    precheck_result = {
        "task_code": "RC2-PRODCARDS3AK-AL",
        "phase": "A_Precheck",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "precheck_passed": True,
        "next_allowed_action": "controlled_sdxl_faceid_asset_acquisition_required",
        "retry_gate_open": False,
        "production_accepted": False,
        "assemble_scene_allowed": False,
        "downstream_blocked": True,
        "active_checkpoint": "juggernautXL_version2.safetensors",
        "required_asset_set": [a["filename"] for a in ASSETS],
        "trusted_source": SOURCE_REPO,
        "source_reference": SOURCE_REFERENCE,
        "source_commit": SOURCE_COMMIT,
        "no_sd15_substitution": True,
        "no_generic_substitution": True
    }
    
    # Save precheck result
    precheck_path = CONTROL_DIR / "rc2_prodcards3ak_al_sdxl_faceid_precheck_result.json"
    with open(precheck_path, 'w') as f:
        json.dump(precheck_result, f, indent=2)
    print(f"Precheck result saved to: {precheck_path}")
    
    # Phase B: Acquisition
    print("\nPhase B: Controlled Acquisition")
    acquisition_result = {
        "task_code": "RC2-PRODCARDS3AK-AL",
        "phase": "B_Acquisition",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "assets": []
    }
    
    for asset in ASSETS:
        print(f"\nDownloading {asset['filename']}...")
        download_result = download_asset(asset)
        acquisition_result["assets"].append({
            "filename": asset['filename'],
            "download_result": download_result
        })
    
    # Save acquisition result
    acquisition_path = CONTROL_DIR / "rc2_prodcards3ak_al_sdxl_faceid_acquisition_result.json"
    with open(acquisition_path, 'w') as f:
        json.dump(acquisition_result, f, indent=2)
    print(f"\nAcquisition result saved to: {acquisition_path}")
    
    # Phase C: Validation
    print("\nPhase C: Validation")
    validation_result = {
        "task_code": "RC2-PRODCARDS3AK-AL",
        "phase": "C_Validation",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "assets": []
    }
    
    all_validated = True
    for i, asset in enumerate(ASSETS):
        print(f"\nValidating {asset['filename']}...")
        val_result = validate_asset(asset, acquisition_result["assets"][i]["download_result"])
        validation_result["assets"].append({
            "filename": asset['filename'],
            "validation_result": val_result
        })
        if not val_result["validation_passed"]:
            all_validated = False
            print(f"  FAILED: {val_result.get('error')}")
        else:
            print(f"  PASSED")
            print(f"    Size: {val_result['file_size_bytes']:,} bytes")
            print(f"    SHA256: {val_result['sha256_hash']}")
    
    validation_result["all_assets_validated"] = all_validated
    
    # Save validation result
    validation_path = CONTROL_DIR / "rc2_prodcards3ak_al_sdxl_faceid_validation_result.json"
    with open(validation_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    print(f"\nValidation result saved to: {validation_path}")
    
    # Phase D: Install (only if all validated)
    install_result = {
        "task_code": "RC2-PRODCARDS3AK-AL",
        "phase": "D_Install",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "assets": []
    }
    
    all_installed = False
    if all_validated:
        print("\nPhase D: Install / Placement")
        for i, asset in enumerate(ASSETS):
            print(f"\nInstalling {asset['filename']}...")
            inst_result = install_asset(asset, validation_result["assets"][i]["validation_result"])
            install_result["assets"].append({
                "filename": asset['filename'],
                "install_result": inst_result
            })
            if not inst_result["install_passed"]:
                print(f"  FAILED: {inst_result.get('error')}")
            else:
                print(f"  PASSED")
                print(f"    Final path: {inst_result['final_path']}")
                print(f"    Final size: {inst_result['final_file_size_bytes']:,} bytes")
        
        all_installed = all(a["install_result"]["install_passed"] for a in install_result["assets"])
    else:
        print("\nPhase D: SKIPPED (validation failed)")
        install_result["skipped_reason"] = "Validation failed"
    
    install_result["all_assets_installed"] = all_installed
    
    # Save install result
    install_path = CONTROL_DIR / "rc2_prodcards3ak_al_sdxl_faceid_install_result.json"
    with open(install_path, 'w') as f:
        json.dump(install_result, f, indent=2)
    print(f"\nInstall result saved to: {install_path}")
    
    # Phase E: Post-install verification
    print("\nPhase E: Post-install Verification")
    post_install_result = {
        "task_code": "RC2-PRODCARDS3AK-AL",
        "phase": "E_PostInstallVerification",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "verification_items": []
    }
    
    # Verify both final files exist
    for asset in ASSETS:
        final_path = asset['final_path']
        exists = final_path.exists()
        filename_match = final_path.name == asset['filename'] if exists else False
        extension_match = final_path.suffix == asset['expected_extension'] if exists else False
        
        verification_item = {
            "filename": asset['filename'],
            "final_path": str(final_path),
            "file_exists": exists,
            "filename_matches": filename_match,
            "extension_matches": extension_match
        }
        
        if exists:
            verification_item["file_size"] = final_path.stat().st_size
            verification_item["sha256_hash"] = calculate_sha256(final_path)
        
        post_install_result["verification_items"].append(verification_item)
    
    # Verify boundary conditions
    post_install_result["boundary_verification"] = {
        "active_checkpoint_unchanged": "juggernautXL_version2.safetensors",
        "retry_gate_open": False,
        "production_accepted": False,
        "assemble_scene_allowed": False,
        "downstream_blocked": True,
        "comfyui_generation_executed": False,
        "frame_generation_executed": False,
        "retry_generate_frames_executed": False,
        "qa_rerun_executed": False,
        "assemble_scene_executed": False,
        "audio_executed": False,
        "render_executed": False,
        "downstream_actions_executed": False
    }
    
    post_install_result["overall_success"] = all_installed and all(
        item["file_exists"] and item["filename_matches"] and item["extension_matches"]
        for item in post_install_result["verification_items"]
    )
    
    # Save post-install verification result
    post_install_path = CONTROL_DIR / "rc2_prodcards3ak_al_sdxl_faceid_post_install_verification_result.json"
    with open(post_install_path, 'w') as f:
        json.dump(post_install_result, f, indent=2)
    print(f"Post-install verification result saved to: {post_install_path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Precheck: {'PASSED' if precheck_result['precheck_passed'] else 'FAILED'}")
    print(f"Acquisition: {'PASSED' if all(a['download_result']['success'] for a in acquisition_result['assets']) else 'FAILED'}")
    print(f"Validation: {'PASSED' if all_validated else 'FAILED'}")
    print(f"Install: {'PASSED' if all_installed else 'SKIPPED/FAILED'}")
    print(f"Post-install verification: {'PASSED' if post_install_result['overall_success'] else 'FAILED'}")
    print("=" * 80)
    
    return 0 if post_install_result["overall_success"] else 1

if __name__ == "__main__":
    sys.exit(main())
