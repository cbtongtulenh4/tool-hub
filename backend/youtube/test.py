# import sys
# sys.stdout.reconfigre(encoding="utf-8")
# from yt_dlp import YoutubeDL

# def grab(url):
#     ydl_opts = {'extract_flat': True, 'skip_download': True}
#     with YoutubeDL(ydl_opts) as ydl:
#         return ydl.extract_info(url, download=False)

# info_all   = grab("https://www.youtube.com/@PigReviewTruyen")          # tất cả uploads (gồm Shorts)
# # info_vid   = grab("https://www.youtube.com/@handle/videos")   # chỉ tab Videos
# # info_shorts= grab("https://www.youtube.com/@handle/shorts")   # chỉ tab Shorts
# # info_pl    = grab("https://www.youtube.com/@handle/playlists")
# print(info_all)

import re

def get_quality_number(quality_str: str) -> int | None:
    """Extracts 360/480/720/1080/etc. from a string like 'mp4 (1080p)' or 'webm (480p)'."""
    m = re.search(r'(\d{3,4})(?=p\b)', quality_str)
    return int(m.group(1)) if m else None

# Example usage
print(get_quality_number("mp4 (1080p)"))  # 1080
print(get_quality_number("webm (480p)"))  # 480
