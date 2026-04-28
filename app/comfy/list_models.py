import asyncio
import json
import httpx

from app.config import settings


async def main() -> None:
    url = f"{settings.comfy_base_url}/models"

    async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    print("MODELS API OK")
    print("Response type:", type(data).__name__)

    if isinstance(data, dict):
        print("Top-level keys:", list(data.keys())[:20])
        print(json.dumps(data, indent=2, ensure_ascii=False)[:4000])
    elif isinstance(data, list):
        print("Total items:", len(data))
        print(json.dumps(data[:20], indent=2, ensure_ascii=False))
    else:
        print(data)


if __name__ == "__main__":
    asyncio.run(main())
