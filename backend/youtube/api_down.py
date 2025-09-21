import sys
sys.stdout.reconfigure(encoding="utf-8")
import httpx
import re

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
            print(datas)

        if platform == "youtube":
            medias = datas['medias']
            video = None
            audio = None
            for media in medias:
                type = media['type']
                if type == "video":
                    if not video:
                        video = media
                    else:
                    #     quality = media['quality']
                    #     m = re.search(r'(\d{3,4})(?=p\b)', quality)
                        # media['quality'] = int(m.group(1)) if m else None
                        if video['height'] < media['height']:
                            video = media
                        
                elif type == "audio":
                    if not audio:
                        audio = media
                    else:
                        if audio['bitrate'] < media['bitrate']:
                            audio = media
            cnt = 0
            if video:
                cnt += 1
            if audio:
                cnt += 1
            rs = {
                "title": datas['title'],
                "url": datas['url'],
                "thumbnail": datas['thumbnail'],
                "duration": datas['duration'],
                "cnt": cnt,
                "medias": [video, audio]
            }



if __name__ == "__main__":
    import asyncio
    pinterest_down = PinterestDown()
    asyncio.run(pinterest_down.fsmvid_api("youtube", "https://www.youtube.com/watch?v=hNhQoVwXJCc&list=RD5xlNfz4hSBw&index=6"))

    

















