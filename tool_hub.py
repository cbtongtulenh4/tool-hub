#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tool Hub - All-in-one Social Media Downloader (CustomTkinter + yt-dlp)

✨ Tính năng chính
- Chỉ cần dán URL (TikTok/Douyin/Facebook/Instagram/Twitter/X/YouTube/Pinterest/Reddit/...)
- Tự nhận diện nền tảng qua yt-dlp, liệt kê các định dạng/độ phân giải
- Chọn thư mục lưu, theo dõi tiến trình, xem log
- Copy link tải trực tiếp của định dạng đã chọn (nếu chỉ muốn lấy URL)
- Giao diện tối/ sáng chuyển đổi tức thì

📦 Phụ thuộc
    pip install customtkinter yt-dlp pillow requests

📌 Khuyến nghị
- Nên cài đặt FFmpeg trong PATH để hợp nhất audio+video chất lượng cao hơn:
  https://ffmpeg.org/download.html

⚠️ Lưu ý pháp lý
- Chỉ tải nội dung khi bạn có quyền hợp pháp (dùng cá nhân, chủ sở hữu cho phép, hoặc theo luật áp dụng).
- Tôn trọng bản quyền và Điều khoản Dịch vụ của từng nền tảng.
"""

import os
import sys
import re
import json
import queue
import threading
import webbrowser
from urllib.parse import urlparse
from datetime import datetime

# GUI
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Optional preview
try:
    from PIL import Image
    import io
    import requests
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# Downloader
import yt_dlp as ytdlp

APP_NAME = "Tool Hub - Social Downloader"
VERSION = "1.0.0"

# ---------------------------- Utils ----------------------------

def human_filesize(num, suffix="B"):
    try:
        num = float(num)
    except Exception:
        return "-"
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Y{suffix}"

def detect_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc
    except Exception:
        return ""

def default_download_dir():
    home = os.path.expanduser("~")
    for d in ("Downloads", "Download", "Tải về"):
        p = os.path.join(home, d)
        if os.path.isdir(p):
            return p
    return home

def sanitize_filename(name: str) -> str:
    # Keep it simple & safe across OS
    return re.sub(r'[\\/*?:"<>|]+', "_", name).strip()

# ---------------------------- App ----------------------------

class ToolHubApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("980x720")
        self.minsize(900, 650)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.url_var = tk.StringVar()
        self.dir_var = tk.StringVar(value=default_download_dir())
        self.status_var = tk.StringVar(value="Sẵn sàng.")
        self.title_var = tk.StringVar(value="")
        self.meta_var = tk.StringVar(value="")
        self.format_map = {}  # label -> format_id
        self.selected_format = tk.StringVar(value="best")
        self.info_json = None
        self.stop_flag = threading.Event()
        self.progress_queue = queue.Queue()

        self._build_ui()
        self._poll_progress()

    # ---------------------------- UI ----------------------------
    def _build_ui(self):
        # Header
        header = ctk.CTkFrame(self, corner_radius=16)
        header.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text="Tool Hub", font=("Inter", 28, "bold")).pack(side="left", padx=12, pady=10)
        ctk.CTkLabel(header, text="All-in-one Social Downloader", font=("Inter", 14)).pack(side="left", padx=6)

        # Theme switch
        self.theme_opt = ctk.CTkSegmentedButton(header, values=["Dark", "Light"], command=self._switch_theme)
        self.theme_opt.set("Dark")
        self.theme_opt.pack(side="right", padx=12)

        # URL row
        url_row = ctk.CTkFrame(self, corner_radius=16)
        url_row.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(url_row, text="URL:", width=40).pack(side="left", padx=(12, 6), pady=12)
        self.url_entry = ctk.CTkEntry(url_row, textvariable=self.url_var, placeholder_text="Dán URL từ TikTok/Douyin/Facebook/Instagram/Twitter/YouTube/...",
                                      height=40)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=6, pady=12)

        paste_btn = ctk.CTkButton(url_row, text="Dán", width=80, command=self._paste_clipboard)
        paste_btn.pack(side="left", padx=6)

        clear_btn = ctk.CTkButton(url_row, text="Xóa", width=80, fg_color="#3b3b3b", command=self._clear_url)
        clear_btn.pack(side="left", padx=6)

        analyze_btn = ctk.CTkButton(url_row, text="Phân tích", width=120, command=self._analyze_url_threaded)
        analyze_btn.pack(side="left", padx=(6,12))

        # Directory row
        dir_row = ctk.CTkFrame(self, corner_radius=16)
        dir_row.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(dir_row, text="Lưu vào:", width=70).pack(side="left", padx=(12, 6), pady=12)
        self.dir_label = ctk.CTkLabel(dir_row, textvariable=self.dir_var, anchor="w")
        self.dir_label.pack(side="left", fill="x", expand=True, padx=6)
        browse_btn = ctk.CTkButton(dir_row, text="Chọn thư mục…", width=140, command=self._choose_dir)
        browse_btn.pack(side="left", padx=(6,12))

        # Main content split: left (meta/formats) & right (log)
        main = ctk.CTkFrame(self, corner_radius=16)
        main.pack(fill="both", expand=True, padx=16, pady=8)

        left = ctk.CTkFrame(main, corner_radius=16)
        left.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        right = ctk.CTkFrame(main, corner_radius=16)
        right.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        # Left: meta + formats + actions
        meta_frame = ctk.CTkFrame(left, corner_radius=16)
        meta_frame.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(meta_frame, textvariable=self.title_var, font=("Inter", 16, "bold"), anchor="w", justify="left").pack(fill="x", padx=12, pady=(10,4))
        ctk.CTkLabel(meta_frame, textvariable=self.meta_var, font=("Inter", 13), text_color=("gray70", "gray80"), anchor="w", justify="left").pack(fill="x", padx=12, pady=(0,10))

        # Thumbnail (optional)
        self.thumb_label = ctk.CTkLabel(meta_frame, text="")
        self.thumb_label.pack(padx=12, pady=(0,10))

        # Formats
        fmt_frame = ctk.CTkFrame(left, corner_radius=16)
        fmt_frame.pack(fill="both", expand=True, padx=12, pady=8)

        fmt_head = ctk.CTkLabel(fmt_frame, text="Chọn định dạng/độ phân giải:", font=("Inter", 14, "bold"))
        fmt_head.pack(anchor="w", padx=12, pady=(10,6))

        self.format_menu = ctk.CTkOptionMenu(fmt_frame, values=["best"], variable=self.selected_format, dynamic_resizing=True, width=420)
        self.format_menu.pack(fill="x", padx=12, pady=(0,10))

        # Action buttons
        action_row = ctk.CTkFrame(fmt_frame, corner_radius=16, fg_color="transparent")
        action_row.pack(fill="x", padx=12, pady=(0,12))

        self.download_btn = ctk.CTkButton(action_row, text="Tải về", width=120, command=self._download_threaded, state="disabled")
        self.download_btn.pack(side="left", padx=(0,8))

        self.copy_link_btn = ctk.CTkButton(action_row, text="Copy link trực tiếp", width=160, command=self._copy_direct_link, state="disabled")
        self.copy_link_btn.pack(side="left", padx=8)

        self.open_dir_btn = ctk.CTkButton(action_row, text="Mở thư mục", width=120, fg_color="#3b3b3b", command=self._open_dir)
        self.open_dir_btn.pack(side="left", padx=8)

        # Progress
        progress_frame = ctk.CTkFrame(left, corner_radius=16)
        progress_frame.pack(fill="x", padx=12, pady=(0,12))
        self.progress = ctk.CTkProgressBar(progress_frame)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=12, pady=(12,6))
        self.status_label = ctk.CTkLabel(progress_frame, textvariable=self.status_var)
        self.status_label.pack(anchor="w", padx=12, pady=(0,12))

        # Right: log console
        ctk.CTkLabel(right, text="Nhật ký (log)", font=("Inter", 14, "bold")).pack(anchor="w", padx=12, pady=(12,6))
        self.log_box = ctk.CTkTextbox(right, height=520)
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(0,12))
        self._log(f"{APP_NAME} v{VERSION}\n")

        # Footer / statusbar
        footer = ctk.CTkFrame(self, corner_radius=16)
        footer.pack(fill="x", padx=16, pady=(8, 16))
        ctk.CTkLabel(footer, text="© 2025 — Dùng cho mục đích hợp pháp.").pack(side="left", padx=12)
        self.domain_label = ctk.CTkLabel(footer, text="")
        self.domain_label.pack(side="right", padx=12)

    # ---------------------------- Handlers ----------------------------

    def _switch_theme(self, mode: str):
        ctk.set_appearance_mode(mode)

    def _paste_clipboard(self):
        try:
            txt = self.clipboard_get()
            self.url_var.set(txt.strip())
        except Exception:
            pass

    def _clear_url(self):
        self.url_var.set("")
        self.title_var.set("")
        self.meta_var.set("")
        self.info_json = None
        self.format_map.clear()
        self.format_menu.configure(values=["best"])
        self.format_menu.set("best")
        self.download_btn.configure(state="disabled")
        self.copy_link_btn.configure(state="disabled")
        self.progress.set(0)
        self.status_var.set("Sẵn sàng.")
        self.domain_label.configure(text="")
        if PIL_AVAILABLE:
            self.thumb_label.configure(image=None, text="")

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.dir_var.get() or default_download_dir(), title="Chọn thư mục lưu")
        if d:
            self.dir_var.set(d)

    def _open_dir(self):
        path = self.dir_var.get() or default_download_dir()
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showinfo("Mở thư mục", f"Đường dẫn: {path}")

    def _log(self, text: str):
        self.log_box.insert("end", text)
        self.log_box.see("end")

    # ---------------------------- Analyze ----------------------------

    def _analyze_url_threaded(self):
        t = threading.Thread(target=self._analyze_url, daemon=True)
        t.start()

    def _analyze_url(self):
        url = (self.url_var.get() or "").strip()
        if not url:
            messagebox.showwarning("Thiếu URL", "Vui lòng dán URL cần tải.")
            return

        self._log(f"\n[Analyze] URL: {url}\n")
        self.status_var.set("Đang phân tích URL…")
        self.progress.set(0.1)
        self.download_btn.configure(state="disabled")
        self.copy_link_btn.configure(state="disabled")

        # Show domain
        domain = detect_domain(url)
        if domain:
            self.domain_label.configure(text=f"Nền tảng: {domain}")

        ydl_opts = {
            "skip_download": True,
            "quiet": True,
            "nocheckcertificate": True,
            "cachedir": False,
            "extract_flat": False,
        }

        try:
            with ytdlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as e:
            self.status_var.set("Phân tích thất bại.")
            self._log(f"[Error] {e}\n")
            messagebox.showerror("Lỗi phân tích", f"Không thể trích xuất thông tin.\n\n{e}")
            return

        # Handle playlist vs single video/post
        if info is None:
            self.status_var.set("Không tìm thấy thông tin.")
            self._log("[Warn] info = None\n")
            return

        if info.get("_type") == "playlist":
            # Pick first entry for simplicity
            entries = info.get("entries") or []
            if not entries:
                self.status_var.set("Danh sách trống.")
                return
            info = entries[0]

        self.info_json = info
        title = info.get("title") or "Không tiêu đề"
        uploader = info.get("uploader") or info.get("uploader_id") or info.get("channel") or ""
        duration = info.get("duration")
        duration_str = f"{duration//60:02d}:{duration%60:02d}" if isinstance(duration, (int,float)) else "-"
        webpage_url = info.get("webpage_url") or ""

        self.title_var.set(sanitize_filename(title))
        meta_bits = []
        if uploader: meta_bits.append(f"Tác giả/Kênh: {uploader}")
        if duration_str != "-": meta_bits.append(f"Độ dài: {duration_str}")
        if webpage_url: meta_bits.append(f"URL nguồn: {webpage_url}")
        self.meta_var.set("   ·   ".join(meta_bits))

        # Thumbnail preview (optional)
        if PIL_AVAILABLE:
            thumb_url = (info.get("thumbnail") or (info.get("thumbnails") or [{}])[-1].get("url"))
            if thumb_url:
                try:
                    resp = requests.get(thumb_url, timeout=10)
                    resp.raise_for_status()
                    image = Image.open(io.BytesIO(resp.content))
                    # Resize to fit
                    image.thumbnail((420, 420))
                    cimg = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                    self.thumb_label.configure(image=cimg, text="")
                except Exception:
                    self.thumb_label.configure(image=None, text="")

        # Build formats
        formats = info.get("formats") or []
        items = []
        self.format_map.clear()

        # Prefer progressive muxed formats first (have both audio+video) else fallback bestvideo+bestaudio
        for f in formats:
            if f.get("acodec") in (None, "none") and f.get("vcodec") not in (None, "none"):
                # video-only; still list it
                pass
            # Skip DRM or no url
            if f.get("is_drm") or not f.get("url"):
                continue

            fmt_id = str(f.get("format_id"))
            ext = f.get("ext") or "?"
            fps = f.get("fps") or ""
            vcodec = f.get("vcodec") or ""
            acodec = f.get("acodec") or ""
            tbr = f.get("tbr")
            height = f.get("height")
            width = f.get("width")
            filesize = f.get("filesize") or f.get("filesize_approx")

            res = f"{width}x{height}" if width and height else (f"{height}p" if height else "")
            fps_str = f"{int(fps)}fps" if fps else ""
            br_str = f"{int(tbr)}k" if tbr else ""
            size_str = human_filesize(filesize) if filesize else "-"

            label = f"{fmt_id} · {ext.upper()} · {res} {fps_str} · {size_str} · {vcodec}/{acodec}".replace("  ", " ").strip()
            items.append(label)
            self.format_map[label] = fmt_id

        # Fallback
        if not items:
            items = ["best"]
            self.format_map = {"best": "best"}

        # Sort: prefer higher height/tbr inferred by text
        def _fmt_sort_key(lbl: str):
            import re
            m = re.search(r"(\d{3,4})p", lbl)
            h = int(m.group(1)) if m else 0
            m2 = re.search(r"(\d{2,4})fps", lbl)
            fps = int(m2.group(1)) if m2 else 0
            return (h, fps, "video only" in lbl.lower())

        if len(items) > 1:
            items_sorted = sorted(items, key=_fmt_sort_key, reverse=True)
        else:
            items_sorted = items

        self.format_menu.configure(values=items_sorted)
        # Default select best matching highest
        self.format_menu.set(items_sorted[0])
        self.download_btn.configure(state="normal")
        self.copy_link_btn.configure(state="normal")

        self.status_var.set("Phân tích xong. Chọn định dạng rồi bấm Tải về.")
        self.progress.set(0.0)

        self._log("[Info] Đã trích xuất thông tin & định dạng.\n")

    # ---------------------------- Download ----------------------------

    def _download_threaded(self):
        t = threading.Thread(target=self._download_run, daemon=True)
        t.start()

    def _progress_hook(self, d):
        # Called from downloader thread
        self.progress_queue.put(d)

    def _poll_progress(self):
        try:
            while True:
                d = self.progress_queue.get_nowait()
                status = d.get("status")
                if status == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    downloaded = d.get("downloaded_bytes") or 0
                    pct = (downloaded / total) if total else 0.0
                    self.progress.set(max(0.0, min(1.0, pct)))
                    speed = d.get("speed") or 0
                    eta = d.get("eta")
                    sp = f"{human_filesize(speed)}/s" if speed else "-"
                    eta_str = f"{eta}s" if eta else "-"
                    self.status_var.set(f"Đang tải… {pct*100:4.1f}%  ·  Tốc độ {sp}  ·  ETA {eta_str}")
                elif status == "finished":
                    self.progress.set(1.0)
                    self.status_var.set("Hoàn tất tải. Đang xử lý hậu kỳ (nếu có)…")
                elif status == "error":
                    self.status_var.set("Lỗi tải.")
        except queue.Empty:
            pass
        # Schedule next poll
        self.after(100, self._poll_progress)

    def _download_run(self):
        if not self.info_json:
            messagebox.showwarning("Chưa phân tích", "Hãy bấm Phân tích trước khi tải.")
            return

        url = self.url_var.get().strip()
        dstdir = self.dir_var.get().strip() or default_download_dir()
        os.makedirs(dstdir, exist_ok=True)

        selected_label = self.selected_format.get()
        fmt_id = self.format_map.get(selected_label, "best")

        self._log(f"\n[Download] format={fmt_id} -> {dstdir}\n")
        self.status_var.set("Bắt đầu tải…")
        self.progress.set(0.0)

        # Out template
        outtmpl = os.path.join(dstdir, "%(title)s [%(id)s].%(ext)s")

        ydl_opts = {
            "format": fmt_id,
            "outtmpl": outtmpl,
            "noprogress": True,
            "progress_hooks": [self._progress_hook],
            "nocheckcertificate": True,
            "cachedir": False,
            "merge_output_format": "mp4",  # if merge is needed
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4"
                }
            ],
            # Avoid unwanted warnings
            "quiet": True,
        }

        try:
            with ytdlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.status_var.set("Tải xong ✔")
            self._log("[Done] Tải xong.\n")
            self.progress.set(1.0)
        except Exception as e:
            self.status_var.set("Tải thất bại.")
            self._log(f"[Error] {e}\n")
            messagebox.showerror("Lỗi tải", f"Không thể tải nội dung.\n\n{e}")

    # ---------------------------- Direct Link ----------------------------

    def _copy_direct_link(self):
        # Copy direct media URL of selected format to clipboard (no download).
        if not self.info_json:
            messagebox.showwarning("Chưa phân tích", "Hãy bấm Phân tích trước.")
            return
        selected_label = self.selected_format.get()
        fmt_id = self.format_map.get(selected_label, "best")

        # If "best" is selected, try to find a reasonable direct URL. Otherwise, look up the format id.
        direct_url = None
        if fmt_id != "best":
            for f in (self.info_json.get("formats") or []):
                if str(f.get("format_id")) == str(fmt_id) and f.get("url"):
                    direct_url = f["url"]
                    break
        else:
            # Fall back to top format's URL
            fmts = self.info_json.get("formats") or []
            for f in reversed(fmts):  # guess highest typical
                if f.get("url"):
                    direct_url = f["url"]
                    break

        if not direct_url:
            messagebox.showinfo("Không có URL trực tiếp", "Không tìm thấy link trực tiếp cho định dạng này.")
            return

        try:
            self.clipboard_clear()
            self.clipboard_append(direct_url)
        except Exception:
            pass
        self._log("[Info] Đã copy link trực tiếp vào clipboard.\n")
        self.status_var.set("Đã copy link trực tiếp vào clipboard.")

# ---------------------------- main ----------------------------

def main():
    app = ToolHubApp()
    app.mainloop()

if __name__ == "__main__":
    main()
