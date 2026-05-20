"""
Create canonical reference contact sheet combining character and environment references.
"""

from PIL import Image, ImageDraw, ImageFont
import json
from pathlib import Path

def create_canonical_contact_sheet():
    project_root = Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
    
    # Load REAL canonical assets from input/canonical_references
    canonical_char_path = project_root / "input" / "canonical_references" / "01_identity" / "headshot_front.png"
    canonical_env_path = project_root / "input" / "canonical_references" / "05_environment" / "character_in_environment.png"
    
    char_img = Image.open(canonical_char_path)
    env_img = Image.open(canonical_env_path)
    
    # Resize to match dimensions for contact sheet
    char_img = char_img.resize((1254, 1254), Image.Resampling.LANCZOS)
    env_img = env_img.resize((1254, 1254), Image.Resampling.LANCZOS)
    
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
    draw.text((25, height + 60), "CHARACTER: input/canonical_references/01_identity/headshot_front.png", fill=(200, 200, 200), font=font)
    draw.text((25, height + 85), "char_lock_001 (operator-prepared canonical)", fill=(150, 255, 150), font=font)
    
    # Environment label
    draw.text((width + 75, height + 60), "ENVIRONMENT: input/canonical_references/05_environment/character_in_environment.png", fill=(200, 200, 200), font=font)
    draw.text((width + 75, height + 85), "env_lock_001 (operator-prepared canonical)", fill=(150, 255, 150), font=font)
    
    # Save contact sheet
    output_dir = project_root / "output" / "control" / "identity_environment_lock"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    contact_sheet_path = output_dir / "canonical_reference_contact_sheet.jpg"
    contact_sheet.save(contact_sheet_path, 'JPEG', quality=95)
    
    print(f"Created canonical reference contact sheet: {contact_sheet_path}")
    
    return str(contact_sheet_path)

if __name__ == "__main__":
    create_canonical_contact_sheet()
