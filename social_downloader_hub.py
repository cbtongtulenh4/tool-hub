import os
import random
import time
import hashlib
from dataclasses import dataclass
from pathlib import Path
import tkinter.filedialog as fd

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk

# -------------------------------
# Model (fake)
# -------------------------------
@dataclass
class MediaItem:
    mid: str
    mtype: str            # "image" | "video"
    title: str
    size_kb: int
    duration_s: int       # 0 for image
    thumb: Image.Image
    selected: bool = True
    status: str = "pending"  # pending|downloading|done|error


# -------------------------------
# Helper: create placeholder thumbnail
# -------------------------------
def make_thumb(seed: int, label: str, is_video: bool, w=320, h=180) -> Image.Image:
    rnd = random.Random(seed)
    # background gradient-ish blocks
    img = Image.new("RGB", (w, h), (rnd.randint(30, 90), rnd.randint(30, 90), rnd.randint(30, 90)))
    draw = ImageDraw.Draw(img)
    for i in range(5):
        x0 = rnd.randint(0, w//2); y0 = rnd.randint(0, h//2)
        x1 = rnd.randint(w//2, w); y1 = rnd.randint(h//2, h)
        color = (rnd.randint(80, 200), rnd.randint(80, 200), rnd.randint(80, 200))
        draw.rectangle([x0, y0, x1, y1], outline=color, width=2)

    # label
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except:
        font = ImageFont.load_default()
    tw, th = draw.textsize(label, font=font)
    draw.rectangle([10, 10, 16+tw, 16+th], fill=(0, 0, 0, 128))
    draw.text((14, 14), label, fill=(255, 255, 255), font=font)

    # video play icon
    if is_video:
        tri_w, tri_h = w//6, h//4
        cx, cy = w//2, h//2
        triangle = [(cx - tri_w//2, cy - tri_h//2),
                    (cx - tri_w//2, cy + tri_h//2),
                    (cx + tri_w//2, cy)]
        draw.ellipse([cx - tri_h, cy - tri_h, cx + tri_h, cy + tri_h], fill=(0, 0, 0, 140))
        draw.polygon(triangle, fill=(255, 255, 255))
    return img


def gen_fake_items(url: str) -> list[MediaItem]:
    # deterministic by url
    seed = int(hashlib.md5(url.encode("utf-8")).hexdigest(), 16)
    rnd = random.Random(seed)
    n = rnd.randint(6, 14)
    items: list[MediaItem] = []
    for i in range(n):
        is_video = rnd.random() < 0.5
        mtype = "video" if is_video else "image"
        title = f"{'Video' if is_video else 'Image'} #{i+1}"
        size_kb = rnd.randint(300, 12000) if not is_video else rnd.randint(1500, 50000)
        duration_s = rnd.randint(5, 240) if is_video else 0
        thumb = make_thumb(seed + i, title, is_video, 320, 180)
        items.append(MediaItem(
            mid=f"{mtype}-{i}",
            mtype=mtype,
            title=title,
            size_kb=size_kb,
            duration_s=duration_s,
            thumb=thumb,
            selected=True,
        ))
    return items


# -------------------------------
# UI
# -------------------------------
class MediaCard(ctk.CTkFrame):
    def __init__(self, master, item: MediaItem, on_toggle, on_download_one):
        super().__init__(master, corner_radius=12)
        self.item = item
        self.on_toggle = on_toggle
        self.on_download_one = on_download_one

        # Cache CTkImage
        self.ctk_img = ctk.CTkImage(light_image=item.thumb, dark_image=item.thumb, size=(256, 144))

        # Layout
        self.grid_columnconfigure(1, weight=1)

        # Thumbnail
        self.preview = ctk.CTkLabel(self, image=self.ctk_img, text="")
        self.preview.grid(row=0, column=0, columnspan=3, padx=8, pady=(8, 4), sticky="nsew")

        # Type tag
        tag_text = "VIDEO" if item.mtype == "video" else "IMAGE"
        self.tag = ctk.CTkLabel(self, text=tag_text, fg_color=("gray92", "gray22"),
                                corner_radius=8, padx=8, pady=2)
        self.tag.place(x=12, y=12)

        # Title
        self.title = ctk.CTkLabel(self, text=item.title, anchor="w", font=ctk.CTkFont(size=13, weight="bold"))
        self.title.grid(row=1, column=0, columnspan=2, padx=10, sticky="w")

        # Size / duration
        meta = f"{item.size_kb} KB"
        if item.mtype == "video":
            m, s = divmod(item.duration_s, 60)
            meta += f" • {m:02d}:{s:02d}"
        self.meta = ctk.CTkLabel(self, text=meta, anchor="w")
        self.meta.grid(row=2, column=0, columnspan=2, padx=10, sticky="w")

        # Checkbox
        self.var_sel = ctk.BooleanVar(value=item.selected)
        self.chk = ctk.CTkCheckBox(self, text="Select", variable=self.var_sel, command=self._toggle)
        self.chk.grid(row=3, column=0, padx=10, pady=(4, 8), sticky="w")

        # Per-item download button
        self.btn_dl = ctk.CTkButton(self, text="Download", width=88, command=self._download_one)
        self.btn_dl.grid(row=3, column=1, padx=10, pady=(4, 8), sticky="e")

        # Status bullet
        self.status_lbl = ctk.CTkLabel(self, text="● pending", text_color="#aaaaaa")
        self.status_lbl.grid(row=3, column=2, padx=(0, 10), pady=(4, 8), sticky="e")

    def _toggle(self):
        self.item.selected = self.var_sel.get()
        self.on_toggle(self.item)

    def _download_one(self):
        self.on_download_one(self.item)

    def set_status(self, status: str):
        self.item.status = status
        color = {"pending": "#aaaaaa", "downloading": "#ffaa00", "done": "#22cc55", "error": "#ff4444"}[status]
        self.status_lbl.configure(text=f"● {status}", text_color=color)


class SocialDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Social Downloader (Demo • CustomTkinter)")
        self.geometry("1100x720")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.items: list[MediaItem] = []
        self.cards: list[MediaCard] = []
        self.image_cache = []  # prevent GC
        self.filter_var = ctk.StringVar(value="All")
        self.select_all_var = ctk.BooleanVar(value=True)
        self.downloading = False
        self.cancel_download = False

        # default output dir
        self.output_dir = os.path.join(Path.home(), "Downloads", "SocialDownloaderDemo")
        os.makedirs(self.output_dir, exist_ok=True)

        # ---------- Header ----------
        header = ctk.CTkFrame(self, height=56, corner_radius=0)
        header.pack(fill="x")
        title = ctk.CTkLabel(header, text="📥 Social Downloader (UI Demo)", font=ctk.CTkFont(size=18, weight="bold"))
        title.pack(side="left", padx=16, pady=10)

        self.theme_opt = ctk.CTkOptionMenu(header, values=["System", "Light", "Dark"], command=self._change_theme)
        self.theme_opt.set("System")
        self.theme_opt.pack(side="right", padx=10)

        # ---------- URL Row ----------
        url_row = ctk.CTkFrame(self)
        url_row.pack(fill="x", padx=12, pady=(10, 0))

        self.url_entry = ctk.CTkEntry(url_row, placeholder_text="Dán URL bài viết / reel / tweet ...", height=40)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=10)

        search_btn = ctk.CTkButton(url_row, text="Search", height=40, command=self.on_search)
        search_btn.pack(side="left", padx=(6, 10), pady=10)

        # ---------- Toolbar ----------
        toolbar = ctk.CTkFrame(self)
        toolbar.pack(fill="x", padx=12, pady=(10, 0))

        ctk.CTkLabel(toolbar, text="Filter:").pack(side="left", padx=(10, 6))
        self.filter_seg = ctk.CTkSegmentedButton(toolbar, values=["All", "Images", "Videos"],
                                                 variable=self.filter_var, command=self.refresh_grid)
        self.filter_seg.pack(side="left", padx=(0, 12), pady=10)

        self.select_all_chk = ctk.CTkCheckBox(toolbar, text="Select All (visible)",
                                              variable=self.select_all_var, command=self.on_select_all_toggle)
        self.select_all_chk.pack(side="left", padx=6)

        self.btn_clear = ctk.CTkButton(toolbar, text="Clear Results", command=self.clear_results)
        self.btn_clear.pack(side="right", padx=10)

        # output directory
        self.out_btn = ctk.CTkButton(toolbar, text="⚙ Output Folder", command=self.choose_output_dir, width=140)
        self.out_btn.pack(side="right", padx=(0, 8))

        self.out_label = ctk.CTkLabel(toolbar, text=self.output_dir, anchor="e")
        self.out_label.pack(side="right", padx=(0, 10))

        # ---------- Main Grid (scrollable) ----------
        self.scroll = ctk.CTkScrollableFrame(self, label_text="Results", height=460)
        self.scroll.pack(fill="both", expand=True, padx=12, pady=10)
        self.scroll.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")

        # ---------- Footer / Actions ----------
        footer = ctk.CTkFrame(self)
        footer.pack(fill="x", padx=12, pady=(0, 12))
        self.btn_dl_selected = ctk.CTkButton(footer, text="Download Selected", command=self.download_selected)
        self.btn_dl_all = ctk.CTkButton(footer, text="Download All", command=self.download_all)
        self.btn_cancel = ctk.CTkButton(footer, text="Cancel", fg_color="#444444", command=self.cancel_all)

        self.btn_dl_selected.pack(side="left", padx=10, pady=10)
        self.btn_dl_all.pack(side="left", padx=(0, 10), pady=10)
        self.btn_cancel.pack(side="left", padx=(0, 10), pady=10)

        self.progress = ctk.CTkProgressBar(footer, height=12)
        self.progress.pack(fill="x", expand=True, side="left", padx=(10, 10))
        self.progress.set(0)

        self.status = ctk.CTkLabel(footer, text="Ready")
        self.status.pack(side="right", padx=10)

        # ---------- Log ----------
        self.log = ctk.CTkTextbox(self, height=120)
        self.log.pack(fill="both", padx=12, pady=(0, 12))
        self.log.insert("end", "• This is a UI demo. Data is fake for preview only.\n")

    # ----------------- Actions -----------------
    def _change_theme(self, val: str):
        ctk.set_appearance_mode(val)

    def choose_output_dir(self):
        chosen = fd.askdirectory(initialdir=self.output_dir, title="Chọn thư mục lưu (demo)")
        if chosen:
            self.output_dir = chosen
            self.out_label.configure(text=chosen)

    def clear_results(self):
        self.items.clear()
        self.refresh_grid()
        self.log_write("Cleared results.")
        self.status.configure(text="Cleared")

    def on_select_all_toggle(self):
        visible_cards = self.get_visible_cards()
        for card in visible_cards:
            card.var_sel.set(self.select_all_var.get())
            card.item.selected = card.var_sel.get()

    def on_search(self):
        url = self.url_entry.get().strip()
        if not url:
            self.status.configure(text="Please enter a URL.")
            return
        self.log_write(f"Searching: {url}")
        # Fake load
        self.items = gen_fake_items(url)
        self.status.configure(text=f"Found {len(self.items)} items (fake).")
        self.refresh_grid()

    def refresh_grid(self, *_):
        # clear
        for w in self.scroll.winfo_children():
            w.destroy()
        self.cards.clear()
        self.image_cache.clear()

        # filter
        mode = self.filter_var.get()
        def visible(item: MediaItem):
            return (mode == "All"
                    or (mode == "Images" and item.mtype == "image")
                    or (mode == "Videos" and item.mtype == "video"))

        # rebuild
        r, c = 0, 0
        for item in self.items:
            if not visible(item): 
                continue
            card = MediaCard(self.scroll, item,
                             on_toggle=self.on_item_toggle,
                             on_download_one=self.download_one_item)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            self.cards.append(card)
            c += 1
            if c > 2:
                c = 0
                r += 1

        # update select-all checkbox based on visible
        vis_cards = self.get_visible_cards()
        if vis_cards:
            self.select_all_var.set(all(cd.item.selected for cd in vis_cards))
        else:
            self.select_all_var.set(False)

    def get_visible_cards(self) -> list[MediaCard]:
        mode = self.filter_var.get()
        out = []
        for cd in self.cards:
            if mode == "All" or cd.item.mtype == ("image" if mode == "Images" else "video"):
                out.append(cd)
        return out

    def on_item_toggle(self, item: MediaItem):
        vis_cards = self.get_visible_cards()
        if vis_cards:
            self.select_all_var.set(all(cd.item.selected for cd in vis_cards))

    def log_write(self, text: str):
        self.log.insert("end", f"{text}\n")
        self.log.see("end")

    # ----------------- Download Simulation (no real network) -----------------
    def download_list(self, items: list[MediaItem]):
        if self.downloading or not items:
            return
        self.downloading = True
        self.cancel_download = False
        total = len(items)
        self.status.configure(text=f"Downloading {total} item(s)... (demo)")
        self.progress.set(0)

        # ensure folder exists
        os.makedirs(self.output_dir, exist_ok=True)

        # make an iterator state we can step with after()
        state = {"i": 0, "total": total, "items": items}

        def step():
            if self.cancel_download:
                self.status.configure(text="Canceled")
                self.downloading = False
                self.progress.set(0)
                self.log_write("Download canceled.")
                return

            i = state["i"]
            if i >= state["total"]:
                self.status.configure(text="Done")
                self.downloading = False
                self.progress.set(1)
                self.log_write("All done.")
                return

            item = state["items"][i]
            card = next((c for c in self.cards if c.item.mid == item.mid), None)
            if card:
                card.set_status("downloading")

            # simulate "saving a file" by writing a small placeholder image (for demo)
            fake_filename = f"{item.title.replace(' ', '_')}{'.mp4' if item.mtype=='video' else '.jpg'}"
            target = os.path.join(self.output_dir, fake_filename)
            try:
                # for the demo, save thumbnail as the "downloaded file"
                item.thumb.save(target)
                time.sleep(0.05)  # tiny delay to visualize progress
                if card:
                    card.set_status("done")
                self.log_write(f"Saved → {target}")
            except Exception as e:
                if card:
                    card.set_status("error")
                self.log_write(f"Error saving {target}: {e}")

            state["i"] += 1
            self.progress.set(state["i"] / state["total"])
            self.after(80, step)  # schedule next

        step()

    def download_selected(self):
        items = [it for it in self.items if it.selected]
        if not items:
            self.status.configure(text="No items selected.")
            return
        self.download_list(items)

    def download_all(self):
        if not self.items:
            self.status.configure(text="Nothing to download.")
            return
        self.download_list(list(self.items))

    def download_one_item(self, item: MediaItem):
        self.download_list([item])

    def cancel_all(self):
        if self.downloading:
            self.cancel_download = True


if __name__ == "__main__":
    app = SocialDownloaderApp()
    app.mainloop()
