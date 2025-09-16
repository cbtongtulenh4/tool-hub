import sys
sys.stdout.reconfigure(encoding="utf-8")
import httpx

FSMVID_DOWNLOAD_URL = "https://fsmvid.com/api/proxy"
FSMVID_BASE_URL = "https://fsmvid.com/"

class PinterestDown:
    async def fsmvid_api(self, platform, download_url):
        payload = {
            "platform": platform,
            "url": download_url
        }

        datas = None
        async with httpx.AsyncClient() as client:
            await client.get(FSMVID_BASE_URL)
            resp = await client.post(FSMVID_DOWNLOAD_URL, json=payload)
            datas = resp.json()
        


if __name__ == "__main__":
    import asyncio
    pinterest_down = PinterestDown()
    asyncio.run(pinterest_down.fsmvid_api("youtube", "https://www.youtube.com/watch?v=hNhQoVwXJCc&list=RD5xlNfz4hSBw&index=6"))

    

















