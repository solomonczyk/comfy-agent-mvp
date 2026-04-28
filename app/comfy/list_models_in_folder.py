import asyncio
import json
import httpx

from app.config import settings


FOLDERS = [
    "checkpoints",
    "loras",
    "vae",
    "controlnet",
    "upscale_models",
    "embeddings",
]


async def fetch_folder(client: httpx.AsyncClient, folder: str) -> None:
    url = f"{settings.comfy_base_url}/models/{folder}"
    response = await client.get(url)
    response.raise_for_status()
    data = response.json()

    print(f"\n=== {folder.upper()} ===")
    print("Response type:", type(data).__name__)

    if isinstance(data, list):
        print("Total items:", len(data))
        print(json.dumps(data[:30], indent=2, ensure_ascii=False))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False)[:4000])


async def main() -> None:
    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        for folder in FOLDERS:
            try:
                await fetch_folder(client, folder)
            except Exception as e:
                print(f"\n=== {folder.upper()} ===")
                print("ERROR:", str(e))


if __name__ == "__main__":
    asyncio.run(main())
