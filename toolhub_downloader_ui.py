# ToolHub Downloader (UI Mock) - CustomTkinter
# Author: ChatGPT
# Notes: This is a UI-only mock. All data are placeholders; no real downloading occurs.
# Package as EXE via PyInstaller (see instructions at bottom).

import re
import random
import datetime as _dt
import tkinter as tk
import webbrowser
from dataclasses import dataclass, field
from typing import List, Dict, Optional

try:
    import customtkinter as ctk
except ImportError:
    raise SystemExit("Missing dependency: customtkinter. Run: pip install customtkinter pillow")

from PIL import Image, ImageDraw, ImageFont, ImageTk


# --------------------------- Mock Data Models ---------------------------

@dataclass
class MediaOption:
    id: str
    kind: str   # 'video' or 'image' or 'audio'
    quality: str
    size: str
    url: str

@dataclass
class MediaResult:
    platform: str
    title: str
    author: str
    original_url: str
    thumb_img: Image.Image
    options: List[MediaOption] = field(default_factory=list)


# --------------------------- Utilities ---------------------------

PLATFORM_PATTERNS = {
    "TikTok": r"(?:^|//)(?:www\.)?(?:vt\.)?tiktok\.com",
    "Douyin": r"(?:^|//)(?:www\.)?douyin\.com",
    "Facebook": r"(?:^|//)(?:www\.)?facebook\.com|fb\.watch",
    "Instagram": r"(?:^|//)(?:www\.)?instagram\.com",
    "X (Twitter)": r"(?:^|//)(?:www\.)?(?:twitter\.com|x\.com)",
    "YouTube": r"(?:^|//)(?:www\.)?(?:youtube\.com|youtu\.be)",
    "Pinterest": r"(?:^|//)(?:www\.)?pinterest\.",
    "Reddit": r"(?:^|//)(?:www\.)?reddit\.com",
}

def detect_platform(url: str) -> Optional[str]:
    url_l = url.strip().lower()
    for name, pattern in PLATFORM_PATTERNS.items():
        if re.search(pattern, url_l):
            return name
    return None

def _shorten(text: str, n: int = 64) -> str:
    return text if len(text) <= n else text[: n - 3] + "..."

def _rand_size() -> str:
    # 5–120 MB randomly
    size_mb = random.choice([6, 12, 18, 24, 36, 48, 64, 80, 96, 120])
    return f"{size_mb} MB"

def _rand_duration() -> str:
    s = random.randint(7, 240)
    m, s = divmod(s, 60)
    return f"{m:02d}:{s:02d}"

def _palette_for(platform: str):
    palettes = {
        "TikTok": (25, 25, 25),
        "Douyin": (18, 20, 35),
        "Facebook": (24, 119, 242),
        "Instagram": (131, 58, 180),
        "X (Twitter)": (0, 0, 0),
        "YouTube": (204, 0, 0),
        "Pinterest": (189, 8, 28),
        "Reddit": (255, 69, 0),
        "Unknown": (64, 64, 64),
    }
    return palettes.get(platform, palettes["Unknown"])

def make_placeholder_thumbnail(platform: str, title: str, size=(320, 180)) -> Image.Image:
    bg = _palette_for(platform)
    img = Image.new("RGB", size, color=bg)
    draw = ImageDraw.Draw(img)

    # Draw a subtle diagonal overlay
    draw.polygon([(0, size[1]), (size[0], 0), (size[0], size[1])], outline=None, fill=(255, 255, 255, 16))

    # Use default PIL font; avoid external dependencies
    font1 = ImageFont.load_default()
    font2 = ImageFont.load_default()

    # Platform text
    platform_text = platform.upper()
    tw, th = draw.textsize(platform_text, font=font1)
    draw.text(((size[0] - tw) / 2, 16), platform_text, fill="white", font=font1)

    # Title text (wrapped roughly)
    wrapped = _shorten(title, 40)
    tw2, th2 = draw.textsize(wrapped, font=font2)
    draw.text(((size[0] - tw2) / 2, size[1] // 2 - th2 // 2), wrapped, fill="white", font=font2)

    # Duration pill
    dur = _rand_duration()
    pill_w, pill_h = 48, 18
    x, y = size[0] - pill_w - 8, size[1] - pill_h - 8
    draw.rounded_rectangle([x, y, x + pill_w, y + pill_h], radius=9, fill=(0, 0, 0))
    draw.text((x + 8, y + 3), dur, fill="white", font=font2)

    return img

def mock_fetch_media(url: str) -> MediaResult:
    platform = detect_platform(url) or "Unknown"
    base_title = {
        "TikTok": "Dance Challenge 2025",
        "Douyin": "街头美食探店",
        "Facebook": "Family Picnic Highlights",
        "Instagram": "Sunset Reel at Bali",
        "X (Twitter)": "Tech Event Clip",
        "YouTube": "Ultimate Travel Vlog",
        "Pinterest": "Home Office Inspo",
        "Reddit": "Cat does a flip",
        "Unknown": "Untitled Media",
    }[platform]
    title = f"{base_title} · {_dt.datetime.now().strftime('%b %d')}"
    author = random.choice(["@alex", "@linh", "@minh", "@truong", "@hannah", "@kyle"])

    thumb = make_placeholder_thumbnail(platform, title)

    # Build fake options
    options: List[MediaOption] = []
    if platform in ("TikTok", "Douyin", "Facebook", "Instagram", "X (Twitter)", "YouTube", "Reddit"):
        # Video qualities
        qualities = ["1080p", "720p", "480p"]
        for q in qualities:
            options.append(
                MediaOption(
                    id=f"{platform[:2].lower()}_{q}",
                    kind="video",
                    quality=q,
                    size=_rand_size(),
                    url=f"https://cdn.example.com/{platform.lower().replace(' ', '')}/{q}/file.mp4",
                )
            )
        # Sometimes images too
        if platform in ("Instagram", "Pinterest", "Facebook"):
            for i in range(random.randint(1, 4)):
                options.append(
                    MediaOption(
                        id=f"img_{i+1}",
                        kind="image",
                        quality=f"{random.choice([720, 1080, 1440])}p",
                        size=f"{random.choice([0.8,1.2,2.4]):.1f} MB",
                        url=f"https://cdn.example.com/{platform.lower()}/images/{i+1}.jpg",
                    )
                )
    else:
        # Unknown: just one generic option
        options.append(
            MediaOption(
                id="gen_720",
                kind="video",
                quality="720p",
                size=_rand_size(),
                url="https://cdn.example.com/unknown/720/file.mp4",
            )
        )

    return MediaResult(platform=platform, title=title, author=author, original_url=url, thumb_img=thumb, options=options)


# --------------------------- GUI Components ---------------------------

class Toast(ctk.CTkToplevel):
    def __init__(self, master, message: str, duration_ms: int = 1500):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#222222")
        label = ctk.CTkLabel(self, text=message, padx=14, pady=10)
        label.pack()
        self.after(duration_ms, self.destroy)

        # Position near bottom-right of master
        self.update_idletasks()
        mx, my = master.winfo_rootx(), master.winfo_rooty()
        mw, mh = master.winfo_width(), master.winfo_height()
        sw, sh = self.winfo_width(), self.winfo_height()
        x = mx + mw - sw - 24
        y = my + mh - sh - 24
        self.geometry(f"{sw}x{sh}+{x}+{y}")


class ResultCard(ctk.CTkFrame):
    def __init__(self, master, result: MediaResult, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.result = result

        # Thumbnail
        self.ctk_image = ctk.CTkImage(light_image=result.thumb_img, dark_image=result.thumb_img, size=(320, 180))
        self.thumb_label = ctk.CTkLabel(self, image=self.ctk_image, text="")
        self.thumb_label.grid(row=0, column=0, rowspan=3, padx=(12, 12), pady=12, sticky="nw")

        # Header
        self.title_label = ctk.CTkLabel(self, text=result.title, font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=1, columnspan=3, padx=(0, 8), pady=(14, 0), sticky="w")

        self.meta_label = ctk.CTkLabel(self, text=f"{result.platform} • {result.author}", text_color=("gray20","gray80"))
        self.meta_label.grid(row=1, column=1, columnspan=3, padx=(0, 8), sticky="w")

        self.url_label = ctk.CTkLabel(self, text=_shorten(result.original_url, 80), text_color=("gray30","gray70"))
        self.url_label.grid(row=2, column=1, columnspan=3, padx=(0, 8), pady=(0, 6), sticky="w")

        # Options header
        hdr = ctk.CTkLabel(self, text="Available Downloads (Mock)", text_color=("gray20","gray70"))
        hdr.grid(row=3, column=0, columnspan=4, padx=12, pady=(8, 4), sticky="w")

        # Options list (scrollable)
        self.options_frame = ctk.CTkScrollableFrame(self, height=160, fg_color=("gray95","#0f0f0f"))
        self.options_frame.grid(row=4, column=0, columnspan=4, padx=12, pady=(0, 12), sticky="nsew")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self._populate_options()

    def _populate_options(self):
        for i, opt in enumerate(self.result.options, start=1):
            row = ctk.CTkFrame(self.options_frame, corner_radius=10)
            row.grid(row=i, column=0, padx=6, pady=6, sticky="ew")
            row.grid_columnconfigure(0, weight=0)
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, weight=0)
            row.grid_columnconfigure(3, weight=0)

            # Kind badge
            kind = opt.kind.capitalize()
            badge = ctk.CTkLabel(row, text=kind, width=64, fg_color=("gray88","#1f1f1f"), corner_radius=8, padx=8, pady=6)
            badge.grid(row=0, column=0, padx=8, pady=8, sticky="w")

            # Quality & size
            q = ctk.CTkLabel(row, text=f"Quality: {opt.quality}   •   Size: {opt.size}")
            q.grid(row=0, column=1, padx=6, pady=8, sticky="w")

            # Copy Link
            def _mk_copy(url=opt.url):
                return lambda: (row.clipboard_clear(), row.clipboard_append(url), Toast(self.winfo_toplevel(), "Copied link"))

            copy_btn = ctk.CTkButton(row, text="Copy Link", command=_mk_copy(), width=100)
            copy_btn.grid(row=0, column=2, padx=6, pady=8)

            # Download (mock)
            def _mock_download():
                Toast(self.winfo_toplevel(), "Download is mocked in UI demo")

            dl_btn = ctk.CTkButton(row, text="Download", command=_mock_download, width=110, state="normal")
            dl_btn.grid(row=0, column=3, padx=8, pady=8)



class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_filter_platform):
        super().__init__(master, corner_radius=0)
        self.on_filter_platform = on_filter_platform
        ctk.CTkLabel(self, text="Platforms", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=12, pady=(12, 6), anchor="w")

        self.buttons = []
        for name in ["All"] + list(PLATFORM_PATTERNS.keys()):
            btn = ctk.CTkButton(self, text=name, width=160, command=lambda n=name: self.on_filter_platform(n))
            btn.pack(padx=12, pady=6, anchor="w")
            self.buttons.append(btn)

        ctk.CTkLabel(self, text="History (Mock)", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=12, pady=(16, 6), anchor="w")
        self.history_frame = ctk.CTkScrollableFrame(self, height=240)
        self.history_frame.pack(padx=12, pady=(0, 12), fill="both", expand=True)

    def add_history(self, url: str, platform: str):
        item = ctk.CTkLabel(self.history_frame, text=_shorten(f"[{platform}] {url}", 40), anchor="w")
        item.pack(fill="x", padx=6, pady=4)


class Topbar(ctk.CTkFrame):
    def __init__(self, master, on_analyze, on_settings):
        super().__init__(master, corner_radius=0, height=56)
        self.grid_columnconfigure(2, weight=1)

        self.logo = ctk.CTkLabel(self, text="ToolHub Downloader", font=ctk.CTkFont(size=18, weight="bold"))
        self.logo.grid(row=0, column=0, padx=16, pady=12, sticky="w")

        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste any social media URL…", width=640)
        self.url_entry.grid(row=0, column=1, padx=8, pady=10, sticky="ew")
        self.url_entry.bind("<Return>", lambda e: on_analyze(self.url_entry.get()))

        self.paste_btn = ctk.CTkButton(self, text="Paste", width=80, command=self._paste)
        self.paste_btn.grid(row=0, column=2, padx=(8, 4), pady=10, sticky="e")

        self.analyze_btn = ctk.CTkButton(self, text="Analyze", width=100, command=lambda: on_analyze(self.url_entry.get()))
        self.analyze_btn.grid(row=0, column=3, padx=(4, 12), pady=10, sticky="e")

        self.settings_btn = ctk.CTkButton(self, text="⚙", width=40, command=on_settings)
        self.settings_btn.grid(row=0, column=4, padx=(0, 12), pady=10, sticky="e")

    def _paste(self):
        try:
            txt = self.clipboard_get()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, txt)
        except tk.TclError:
            pass


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Settings")
        self.geometry("380x200")
        ctk.CTkLabel(self, text="Appearance", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=16, pady=(16, 8), anchor="w")

        self.appearance_option = ctk.CTkOptionMenu(self, values=["System", "Light", "Dark"], command=self._change_appearance)
        self.appearance_option.set("System")
        self.appearance_option.pack(padx=16, pady=8, anchor="w")

        ctk.CTkLabel(self, text="UI Scale", font=ctk.CTkFont(size=14, weight="bold")).pack(padx=16, pady=(16, 8), anchor="w")
        self.scale_option = ctk.CTkOptionMenu(self, values=["80%", "90%", "100%", "110%", "120%"], command=self._change_scale)
        self.scale_option.set("100%")
        self.scale_option.pack(padx=16, pady=8, anchor="w")

    def _change_appearance(self, value):
        ctk.set_appearance_mode(value.lower())

    def _change_scale(self, value):
        pct = int(value.strip("%"))
        ctk.set_widget_scaling(pct / 100.0)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ToolHub Downloader (UI Mock)")
        self.geometry("1080x720")

        # Global config
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Layout: sidebar | main
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Top bar
        self.topbar = Topbar(self, on_analyze=self.on_analyze, on_settings=self.open_settings)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Separator
        ctk.CTkFrame(self, height=1, fg_color=("gray80","#1a1a1a")).grid(row=1, column=0, columnspan=2, sticky="ew")

        # Sidebar
        self.sidebar = Sidebar(self, on_filter_platform=self.on_filter_platform)
        self.sidebar.grid(row=2, column=0, sticky="nsew")

        # Main results area
        self.results_area = ctk.CTkScrollableFrame(self, fg_color=("gray98","#0b0b0b"))
        self.results_area.grid(row=2, column=1, sticky="nsew", padx=(0,0))

        # Status bar
        self.status = ctk.CTkLabel(self, text="Ready", anchor="w")
        self.status.grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=6)

        self.cards: List[ResultCard] = []
        self.filter_platform: Optional[str] = "All"

        # Welcome card
        self._show_welcome()

    # ----------------- Actions -----------------

    def _show_welcome(self):
        frame = ctk.CTkFrame(self.results_area, corner_radius=12)
        frame.pack(padx=16, pady=18, fill="x")
        ctk.CTkLabel(frame, text="Paste a link to begin", font=ctk.CTkFont(size=20, weight="bold")).pack(padx=16, pady=(16, 8), anchor="w")
        tips = "This UI demonstrates an all-in-one downloader interface.\n• Auto-detects platform from URL\n• Parses and lists mock download options\n• Copy Link / Download buttons are mocked"
        ctk.CTkLabel(frame, text=tips, justify="left").pack(padx=16, pady=(4, 16), anchor="w")

    def on_analyze(self, url: str):
        url = url.strip()
        if not url:
            Toast(self, "Please paste a URL")
            return

        platform = detect_platform(url) or "Unknown"
        self.status.configure(text=f"Detected: {platform}")
        self.sidebar.add_history(url, platform)

        # Fetch mock data and render card
        result = mock_fetch_media(url)
        self._add_result_card(result)

    def on_filter_platform(self, name: str):
        self.filter_platform = name
        self._refresh_cards()
        Toast(self, f"Filter: {name}")

    def open_settings(self):
        SettingsDialog(self)

    # ----------------- Rendering -----------------

    def _clear_results(self):
        for w in self.results_area.winfo_children():
            w.destroy()
        self.cards.clear()

    def _add_result_card(self, result: MediaResult):
        card = ResultCard(self.results_area, result=result)
        card.pack(padx=16, pady=12, fill="x")
        self.cards.append(card)

    def _refresh_cards(self):
        # Re-render cards according to filter
        for card in self.cards:
            if self.filter_platform in (None, "All"):
                card.pack_configure(padx=16, pady=12, fill="x")
                card.configure(fg_color=None)
                card.grid_propagate(True)
                card.pack_forget()
                card.pack(padx=16, pady=12, fill="x")
                card.update_idletasks()
            else:
                show = (card.result.platform == self.filter_platform)
                if show:
                    card.pack_configure(padx=16, pady=12, fill="x")
                    try:
                        card.pack_info()
                    except tk.TclError:
                        card.pack(padx=16, pady=12, fill="x")
                else:
                    card.pack_forget()


if __name__ == "__main__":
    app = App()
    app.mainloop()

# ---------------------------
# Packaging notes (readme):
#
# 1) Install dependencies:
#    pip install customtkinter pillow pyinstaller
#
# 2) Run the app from source:
#    python toolhub_downloader_ui.py
#
# 3) Build a Windows .exe with PyInstaller:
#    pyinstaller --noconsole --onefile --name ToolHubDownloader toolhub_downloader_ui.py
#
#    The resulting EXE will be in the 'dist' folder.
#
# 4) (Optional) Icon / assets:
#    This script is self-contained and doesn't require external assets.
# ---------------------------
