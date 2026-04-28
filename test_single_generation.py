"""
Simple test to debug image generation issue.
"""
import asyncio
from app.agent.sdxl_agent import SDXLAgent

async def main():
    print("Testing single generation with SDXL Base...")
    agent = SDXLAgent("data/workflows/sdxl_txt2img_template.json")
    
    try:
        result = await agent.generate(
            positive_prompt="test portrait",
            negative_prompt="blurry, low quality",
            width=512,
            height=512,
            steps=10,
            cfg=6.0,
            sampler_name="euler",
            scheduler="karras",
            seed=12345,
            checkpoint="sd_xl_base_1.0_0.9vae.safetensors",
            filename_prefix="test/debug"
        )
        print(f"Success! Generated {len(result['images'])} images")
        print(f"Prompt ID: {result['prompt_id']}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
