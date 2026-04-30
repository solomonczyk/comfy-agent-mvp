#!/usr/bin/env python3
"""
RC2-PRODCARDS3AA: Controlled IP-Adapter Asset Acquisition
Downloads ip-adapter-faceid-plus_sd15.bin from h94/IP-Adapter-FaceID
"""
import os
import hashlib
import json
from datetime import datetime
from pathlib import Path

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("ERROR: huggingface_hub not installed")
    exit(1)

# Configuration
REPO_ID = "h94/IP-Adapter-FaceID"
FILENAME = "ip-adapter-faceid-plus_sd15.bin"
TEMP_DIR = Path("data/rc2_multishot1_ep01/output/control/temp/ip_adapter_acquisition")
FINAL_DIR = Path("F:/ComfyUI/models/ipadapter")
TEMP_PATH = TEMP_DIR / FILENAME
FINAL_PATH = FINAL_DIR / FILENAME

def calculate_sha256(file_path):
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    print(f"RC2-PRODCARDS3AA: Controlled IP-Adapter Asset Acquisition")
    print(f"Target asset: {FILENAME}")
    print(f"Trusted source: {REPO_ID}")
    print(f"Temp path: {TEMP_PATH}")
    print(f"Final install path: {FINAL_PATH}")
    print()
    
    # Create temp directory
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Download from trusted source
    print(f"Downloading {FILENAME} from {REPO_ID}...")
    try:
        downloaded_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=str(TEMP_DIR),
            local_dir_use_symlinks=False
        )
        print(f"Downloaded to: {downloaded_path}")
    except Exception as e:
        print(f"ERROR: Download failed: {e}")
        exit(1)
    
    # Validate downloaded file
    print(f"\nValidating downloaded file...")
    if not TEMP_PATH.exists():
        print(f"ERROR: File not found at {TEMP_PATH}")
        exit(1)
    
    file_size = TEMP_PATH.stat().st_size
    sha256_hash = calculate_sha256(TEMP_PATH)
    
    print(f"File exists: {TEMP_PATH.exists()}")
    print(f"Filename exact match: {TEMP_PATH.name == FILENAME}")
    print(f"Extension: {TEMP_PATH.suffix}")
    print(f"File size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")
    print(f"SHA256: {sha256_hash}")
    
    # Record acquisition result
    acquisition_result = {
        "task_code": "RC2-PRODCARDS3AA",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "target_asset": FILENAME,
        "trusted_source": REPO_ID,
        "download_path": str(TEMP_PATH),
        "file_exists": True,
        "filename_exact_match": TEMP_PATH.name == FILENAME,
        "extension": TEMP_PATH.suffix,
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / (1024*1024), 2),
        "sha256": sha256_hash,
        "download_timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "download_complete"
    }
    
    acquisition_result_path = Path("data/rc2_multishot1_ep01/output/control/ip_adapter_acquisition_execution_result.json")
    acquisition_result_path.parent.mkdir(parents=True, exist_ok=True)
    with open(acquisition_result_path, "w") as f:
        json.dump(acquisition_result, f, indent=2)
    print(f"\nAcquisition result saved to: {acquisition_result_path}")
    
    # Install to final location
    print(f"\nInstalling to ComfyUI IP-Adapter model path...")
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if file already exists at final location
    if FINAL_PATH.exists():
        print(f"WARNING: File already exists at {FINAL_PATH}")
        print(f"Creating backup...")
        backup_path = FINAL_PATH.with_suffix(f".bin.backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        import shutil
        shutil.copy2(FINAL_PATH, backup_path)
        print(f"Backup created: {backup_path}")
    
    # Copy file to final location
    import shutil
    shutil.copy2(TEMP_PATH, FINAL_PATH)
    print(f"File installed to: {FINAL_PATH}")
    
    # Verify final installation
    print(f"\nPost-install verification...")
    final_size = FINAL_PATH.stat().st_size
    final_sha256 = calculate_sha256(FINAL_PATH)
    
    print(f"Final file exists: {FINAL_PATH.exists()}")
    print(f"Final filename exact match: {FINAL_PATH.name == FILENAME}")
    print(f"Final extension: {FINAL_PATH.suffix}")
    print(f"Final file size: {final_size} bytes")
    print(f"Final SHA256: {final_sha256}")
    print(f"SHA256 match: {sha256_hash == final_sha256}")
    
    # Record post-install verification
    verification_result = {
        "task_code": "RC2-PRODCARDS3AA",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "target_asset": FILENAME,
        "trusted_source": REPO_ID,
        "final_install_path": str(FINAL_PATH),
        "file_exists": FINAL_PATH.exists(),
        "filename_exact_match": FINAL_PATH.name == FILENAME,
        "extension": FINAL_PATH.suffix,
        "file_size_bytes": final_size,
        "sha256": final_sha256,
        "sha256_match": sha256_hash == final_sha256,
        "source": REPO_ID,
        "status": "install_verified"
    }
    
    verification_result_path = Path("data/rc2_multishot1_ep01/output/control/ip_adapter_post_install_verification_result.json")
    with open(verification_result_path, "w") as f:
        json.dump(verification_result, f, indent=2)
    print(f"\nVerification result saved to: {verification_result_path}")
    
    print(f"\n=== ACQUISITION COMPLETE ===")
    print(f"Status: SUCCESS")
    print(f"Asset: {FILENAME}")
    print(f"SHA256: {sha256_hash}")
    print(f"Installed to: {FINAL_PATH}")

if __name__ == "__main__":
    main()
