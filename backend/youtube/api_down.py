import requests
import httpx

FSMVID_DOWNLOAD_URL = "https://fsmvid.com/api/proxy"
FSMVID_BASE_URL = "https://fsmvid.com/"

class PinterestDown:
    async def fsmvid_api(self, platform, download_url):
        payload = {
            "platform": platform,
            "url": download_url
        }

        async with httpx.AsyncClient() as client:
            await client.get(FSMVID_BASE_URL)
            resp = await client.post(FSMVID_DOWNLOAD_URL, json=payload)
            print(resp.json())


if __name__ == "__main__":
    import asyncio
    pinterest_down = PinterestDown()
    asyncio.run(pinterest_down.fsmvid_api("pinterest", "https://www.pinterest.com/pin/14636767535799685/"))

    

















