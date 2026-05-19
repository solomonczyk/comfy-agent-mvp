import json
import urllib.request

# Load the actual workflow being submitted
with open("data/rc2_multishot1_ep01/output/control/identity_lock/submitted_identity_locked_workflow.json", "r") as f:
    workflow = json.load(f)

# Remove the metadata that ComfyUI doesn't understand
clean_workflow = {k: v for k, v in workflow.items() if k != "identity_lock_metadata"}

print(f"Clean workflow has {len(clean_workflow)} nodes")

# Submit to ComfyUI
try:
    body = json.dumps({"prompt": clean_workflow}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8188/prompt",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    print("Response:", json.dumps(data, indent=2))
    
    if "prompt_id" in data:
        prompt_id = data["prompt_id"]
        print(f"Success! Prompt ID: {prompt_id}")
        
        # Poll for completion
        import time
        max_wait = 60
        start = time.time()
        while time.time() - start < max_wait:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:8188/history/{prompt_id}", timeout=10) as resp:
                    history = json.loads(resp.read().decode("utf-8"))
                if prompt_id in history:
                    print("Generation completed!")
                    print("History:", json.dumps(history[prompt_id], indent=2))
                    break
            except:
                pass
            time.sleep(2)
    else:
        print("Error:", data)
        
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
