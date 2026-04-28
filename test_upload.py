"""Test upload flow to ComfyUI."""
import asyncio
from pathlib import Path

from app.comfy.comfy_client import ComfyClient


async def test_upload():
    """Test image upload to ComfyUI."""
    client = ComfyClient()
    
    # Test upload_image
    print("Testing upload_image...")
    result = await client.upload_image("test_portrait.png")
    print(f"Upload result: {result}")
    print(f"Uploaded filename: {result.get('name')}")
    
    # Test upload_mask
    print("\nTesting upload_mask...")
    result = await client.upload_mask("test_portrait.png")
    print(f"Mask upload result: {result}")
    print(f"Uploaded mask filename: {result.get('name')}")


if __name__ == "__main__":
    asyncio.run(test_upload())
