"""
Create canonical reference contact sheet combining character and environment references.
"""

from PIL import Image, ImageDraw, ImageFont
import json
from pathlib import Path

def create_canonical_contact_sheet():
    project_root = Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
    
    # Load canonical assets
    character_asset_path = project_root / "output" / "assets" / "identity_lock__00001_.png"
    environment_asset_path = project_root / "output" / "assets" / "corrective_visual_recovery__00001_.png"
    
    char_img = Image.open(character_asset_path)
    env_img = Image.open(environment_asset_path)
    
    # Create contact sheet (side by side)
    width, height = char_img.size
    contact_sheet = Image.new('RGB', (width * 2 + 100, height + 100), (30, 30, 30))
    
    # Paste character reference
    contact_sheet.paste(char_img, (25, 50))
    
    # Paste environment reference
    contact_sheet.paste(env_img, (width + 75, 50))
    
    # Add labels
    draw = ImageDraw.Draw(contact_sheet)
    
    # Title
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    title = "CANONICAL IDENTITY & ENVIRONMENT REFERENCES"
    draw.text((25, 10), title, fill=(255, 255, 255), font=font)
    
    # Character label
    draw.text((25, height + 60), "CHARACTER LOCK: identity_lock__00001_.png", fill=(200, 200, 200), font=font)
    draw.text((25, height + 85), "char_lock_001", fill=(150, 150, 255), font=font)
    
    # Environment label
    draw.text((width + 75, height + 60), "ENVIRONMENT LOCK: corrective_visual_recovery__00001_.png", fill=(200, 200, 200), font=font)
    draw.text((width + 75, height + 85), "env_lock_001 | scene_rc2_multishot1_ep01", fill=(150, 255, 150), font=font)
    
    # Save contact sheet
    output_dir = project_root / "output" / "control" / "identity_environment_lock"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    contact_sheet_path = output_dir / "canonical_reference_contact_sheet.jpg"
    contact_sheet.save(contact_sheet_path, 'JPEG', quality=95)
    
    print(f"Created canonical reference contact sheet: {contact_sheet_path}")
    
    return str(contact_sheet_path)

if __name__ == "__main__":
    create_canonical_contact_sheet()
