import requests
import httpx
import asyncio

FSMVID_DOWNLOAD_URL = "https://fsmvid.com/api/proxy"
FSMVID_BASE_URL = "https://fsmvid.com/"

class FSMVIDDown:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FSMVIDDown, cls).__new__(cls)
        return cls._instance

    async def download(self, platform, download_url):
        payload = {
            "platform": platform,
            "url": download_url
        }

        async with httpx.AsyncClient() as client:
            await client.get(FSMVID_BASE_URL)
            resp = await client.post(FSMVID_DOWNLOAD_URL, json=payload)
            print(resp.json())


if __name__ == "__main__":
    fsmvid = FSMVIDDown()
    asyncio.run(
        fsmvid.download("pinterest", "https://www.pinterest.com/pin/14636767535799685/")
    )
