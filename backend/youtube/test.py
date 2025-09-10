import sys
sys.stdout.reconfigre(encoding="utf-8")
from yt_dlp import YoutubeDL

def grab(url):
    ydl_opts = {'extract_flat': True, 'skip_download': True}
    with YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False)

info_all   = grab("https://www.youtube.com/@PigReviewTruyen")          # tất cả uploads (gồm Shorts)
# info_vid   = grab("https://www.youtube.com/@handle/videos")   # chỉ tab Videos
# info_shorts= grab("https://www.youtube.com/@handle/shorts")   # chỉ tab Shorts
# info_pl    = grab("https://www.youtube.com/@handle/playlists")
print(info_all)