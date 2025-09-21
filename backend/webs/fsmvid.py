# import requests
# import httpx
# import asyncio
# import re

# FSMVID_DOWNLOAD_URL = "https://fsmvid.com/api/proxy"
# FSMVID_BASE_URL = "https://fsmvid.com/"

# class FSMVIDDown:
#     _instance = None

#     def __new__(cls, *args, **kwargs):
#         if cls._instance is None:
#             cls._instance = super(FSMVIDDown, cls).__new__(cls)
#         return cls._instance

#     async def download(self, platform, download_url):
#         payload = {
#             "platform": platform,
#             "url": download_url
#         }

#         async with httpx.AsyncClient() as client:
#             await client.get(FSMVID_BASE_URL)
#             resp = await client.post(FSMVID_DOWNLOAD_URL, json=payload)
#             print(resp.json())

#     def _parse_height(media):
#         h = media.get("height")
#         if isinstance(h, int):
#             return h
#         label = media.get("label", "")
#         m = re.search(r'(\d{3,4})(?=p\b)', label)
#         return int(m.group(1)) if m else None

#     def _bitrate(media):
#         br = media.get("bitrate")
#         try:
#             return int(br) if br is not None else 0
#         except (TypeError, ValueError):
#             return 0

#     def _ext_rank(media):
#         ext = (media.get("ext") or "").lower()
#         return 0 if ext == "mp4" else 1

#     def select_best_streams(datas):
#         medias = datas.get("medias", []) or []

#         best_video = None
#         best_audio = None

#         for media in medias:
#             media_type = media.get("type")

#             if media_type == "video":
#                 if best_video is None:
#                     best_video = media
#                 else:
#                     hv = _parse_height(media) or -1
#                     hb = _parse_height(best_video) or -1

#                     if hv > hb:
#                         best_video = media
#                     elif hv == hb:
#                         # tie-break 1: ext (mp4 trước)
#                         if _ext_rank(media) < _ext_rank(best_video):
#                             best_video = media
#                         # tie-break 2: bitrate cao hơn
#                         elif _bitrate(media) > _bitrate(best_video):
#                             best_video = media
#                         # tie-break 3: fps cao hơn (nếu có)
#                         else:
#                             fps_new = media.get("fps") or 0
#                             fps_old = best_video.get("fps") or 0
#                             if fps_new > fps_old:
#                                 best_video = media

#             elif media_type == "audio":
#                 # tiêu chí: bitrate cao hơn -> tốt hơn; nếu bằng thì ưu tiên mime/ext ổn định (mp4/m4a)
#                 if best_audio is None:
#                     best_audio = media
#                 else:
#                     if _bitrate(media) > _bitrate(best_audio):
#                         best_audio = media
#                     elif _bitrate(media) == _bitrate(best_audio):
#                         # tie-break: ext m4a/mp4 trước
#                         pref = {"m4a": 0, "mp4": 1, "webm": 2}
#                         rank_new = pref.get((media.get("ext") or "").lower(), 99)
#                         rank_old = pref.get((best_audio.get("ext") or "").lower(), 99)
#                         if rank_new < rank_old:
#                             best_audio = media

#         picked = [x for x in (best_video, best_audio) if x is not None]

#         rs = {
#             "title": datas.get("title"),
#             "url": datas.get("url"),
#             "thumbnail": datas.get("thumbnail"),
#             "duration": datas.get("duration"),
#             "cnt": len(picked),
#             "medias": picked,
#         }
#         return rs


# if __name__ == "__main__":
#     fsmvid = FSMVIDDown()
#     asyncio.run(
#         fsmvid.download("pinterest", "https://www.pinterest.com/pin/14636767535799685/")
#     )



import asyncio
import re
from typing import Any, Dict, List, Optional

import httpx
import sys
sys.stdout.reconfigure(encoding="utf-8")

FSMVID_DOWNLOAD_URL = "https://fsmvid.com/api/proxy"
FSMVID_BASE_URL = "https://fsmvid.com/"


class FSMVIDDown:
    _instance: Optional["FSMVIDDown"] = None

    def __new__(cls, *args, **kwargs) -> "FSMVIDDown":
        if cls._instance is None:
            cls._instance = super(FSMVIDDown, cls).__new__(cls)
        return cls._instance

    async def download(self, platform: str, download_url: str) -> Dict[str, Any]:
        """
        Gọi API fsmvid và trả về kết quả đã rút gọn: best video + best audio (nếu có).
        Nếu API không trả về đúng schema kỳ vọng, trả luôn JSON gốc để bạn tự xử lý.
        """
        payload = {"platform": platform, "url": download_url}

        timeout = httpx.Timeout(15.0, connect=10.0, read=10.0)
        headers = {
            "Accept": "application/json",
            "User-Agent": "fsmvid-client/1.0",
            "Origin": FSMVID_BASE_URL.rstrip("/"),
            "Referer": FSMVID_BASE_URL,
        }

        async with httpx.AsyncClient(http2=True, timeout=timeout, headers=headers) as client:
            try:
                await client.get(FSMVID_BASE_URL)
            except Exception:
                pass

            resp = await client.post(FSMVID_DOWNLOAD_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()

        if isinstance(data, dict) and data.get("status") == "success" and "medias" in data:
            return self.select_best_streams(data, platform)

        return data

    # -----------------------
    # Helpers chọn stream tốt
    # -----------------------

    @staticmethod
    def _parse_height(media: Dict[str, Any]) -> Optional[int]:
        """Trả về height (p) từ field 'height' hoặc parse từ 'label' dạng '(1080p)'."""
        h = media.get("height")
        if isinstance(h, int):
            return h
        label = media.get("label", "") or ""
        m = re.search(r"(\d{3,4})(?=p\b)", label)
        return int(m.group(1)) if m else None

    @staticmethod
    def _bitrate(media: Dict[str, Any]) -> int:
        """Trả về bitrate (bit/s); nếu không có thì 0."""
        br = media.get("bitrate")
        try:
            return int(br) if br is not None else 0
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _ext_rank(media: Dict[str, Any]) -> int:
        """Ưu tiên mp4 hơn webm khi chất lượng ngang nhau."""
        ext = (media.get("ext") or "").lower()
        return 0 if ext == "mp4" else 1

    @staticmethod
    def select_best_streams(datas: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        Chọn 1 best video + 1 best audio.
        - Video: height lớn hơn tốt hơn; nếu bằng → ưu tiên mp4 → bitrate cao → fps cao.
        - Audio: bitrate cao hơn; nếu bằng → ưu tiên m4a/mp4 → webm.
        """
        medias: List[Dict[str, Any]] = datas.get("medias", []) or []
        for media in medias:
            best_video, best_audio = FSMVIDDown._switch_platform(media, platform)

        picked = [x for x in (best_video, best_audio) if x is not None]

        return {
            "title": datas.get("title"),
            "url": datas.get("url"),
            "thumbnail": datas.get("thumbnail"),
            "duration": datas.get("duration"),
            "cnt": len(picked),
            "medias": picked,
            "debug": {
                "video_height": FSMVIDDown._parse_height(best_video) if best_video else None,
                "video_bitrate": FSMVIDDown._bitrate(best_video) if best_video else None,
                "video_fps": best_video.get("fps") if best_video else None,
                "audio_bitrate": FSMVIDDown._bitrate(best_audio) if best_audio else None,
            },
        }

    @staticmethod
    def _switch_platform(media: Dict[str, Any], platform: str) -> int:
        match(platform):
            case "youtube":
                return FSMVIDDown._youtube_platform(media)
            case "tiktok":
                pass
            case "douyin":
                pass
            case "facebook":
                pass



        ext = (media.get("ext") or "").lower()
        return 0 if ext == "mp4" else 1

    @staticmethod
    def _youtube_platform(media: Dict[str, Any]) -> int:
        media_type = media.get("type")
        best_video: Optional[Dict[str, Any]] = None
        best_audio: Optional[Dict[str, Any]] = None
        if media_type == "video":
            if best_video is None:
                best_video = media
            else:
                hv = FSMVIDDown._parse_height(media) or -1
                hb = FSMVIDDown._parse_height(best_video) or -1

                if hv > hb:
                    best_video = media
                elif hv == hb:
                    # tie-break 1: ext
                    if FSMVIDDown._ext_rank(media) < FSMVIDDown._ext_rank(best_video):
                        best_video = media
                    # tie-break 2: bitrate
                    elif FSMVIDDown._bitrate(media) > FSMVIDDown._bitrate(best_video):
                        best_video = media
                    # tie-break 3: fps
                    else:
                        fps_new = media.get("fps") or 0
                        fps_old = best_video.get("fps") or 0
                        if fps_new > fps_old:
                            best_video = media

        elif media_type == "audio":
            if best_audio is None:
                best_audio = media
            else:
                br_new = FSMVIDDown._bitrate(media)
                br_old = FSMVIDDown._bitrate(best_audio)
                if br_new > br_old:
                    best_audio = media
                elif br_new == br_old:
                    pref = {"m4a": 0, "mp4": 1, "webm": 2}
                    rank_new = pref.get((media.get("ext") or "").lower(), 99)
                    rank_old = pref.get((best_audio.get("ext") or "").lower(), 99)
                    if rank_new < rank_old:
                        best_audio = media
        return best_video, best_audio

if __name__ == "__main__":
    fsmvid = FSMVIDDown()
    result = asyncio.run(
        # fsmvid.download("douyin", "https://v.douyin.com/fY3CVGSTxz0/")#"youtube", "https://www.youtube.com/watch?v=hNhQoVwXJCc&list=RD5xlNfz4hSBw&index=6")#"pinterest", "https://www.pinterest.com/pin/14636767535799685/"
        fsmvid.download("youtube", "https://www.youtube.com/watch?v=hNhQoVwXJCc&list=RD5xlNfz4hSBw&index=6")#"pinterest", "https://www.pinterest.com/pin/14636767535799685/"
    )
    print(result)

