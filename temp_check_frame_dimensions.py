from PIL import Image
import json
import os

frames_dir = r'F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01\output\frames\ep01_shot01'
frame_info = []

for f in sorted(os.listdir(frames_dir)):
    if f.endswith('.png'):
        img = Image.open(os.path.join(frames_dir, f))
        frame_info.append({
            'filename': f,
            'width': img.width,
            'height': img.height,
            'mode': img.mode
        })
        print(f'{f}: {img.width}x{img.height} {img.mode}')

print(json.dumps(frame_info, indent=2))
