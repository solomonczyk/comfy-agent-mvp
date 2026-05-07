import os
import sys

result_path = r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01\output\control\combine_v2_clean_sdxl_v6_candidate_result.json"
if os.path.exists(result_path):
    os.remove(result_path)
    print(f"Deleted: {result_path}")
else:
    print("Result file not found, skipping delete")

os.chdir(r"F:\ComfyUI\comfy-agent-mvp")
sys.argv = [
    "cli",
    "combine-run-clean-sdxl-v6-candidate",
    "--project-root",
    r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01",
    "--execute",
    "--json",
]
from app.cli import main
sys.exit(main())
