# Tool Hub - CustomTkinter UI
# Requires: Python 3.9+ and customtkinter >= 5.2
# Install:   pip install customtkinter
#
# This app lays out a modern dashboard similar to a "Tool Hub":
# - Collapsible left sidebar (navigation)
# - Top bar with search and appearance mode switcher
# - Category filter (segmented button)
# - Scrollable grid of "tool" cards with action buttons
#
# You can adapt the widgets, colors, spacing and icons to match your Figma exactly.
# Tip: set_default_color_theme accepts a JSON theme file if you have a brand palette.

from __future__ import annotations

import sys
import os
from typing import List, Dict, Callable, Optional

try:
    import customtkinter as ctk
except ImportError as e:
    print("customtkinter is not installed. Run: pip install customtkinter", file=sys.stderr)
    raise

APP_TITLE = "Tool Hub"
APP_MIN_W = 1100
APP_MIN_H = 700


# ---------- Data (mock) ----------
TOOLS: List[Dict] = [
    {"name": "Image Resizer", "desc": "Resize and compress images in bulk. Drag & drop supported.", "category": "Media"},
    {"name": "Video Cutter", "desc": "Trim, split and merge clips for social media.", "category": "Media"},
    {"name": "Color Picker", "desc": "Pick colors from screen and copy HEX/RGB/HSL.", "category": "Design"},
    {"name": "Icon Generator", "desc": "Export app icons and favicons in multiple sizes.", "category": "Design"},
    {"name": "Regex Tester", "desc": "Test and debug regular expressions with live matches.", "category": "Developer"},
    {"name": "JSON Formatter", "desc": "Pretty-print and validate JSON with schema hints.", "category": "Developer"},
    {"name": "Markdown Preview", "desc": "Live preview, export to PDF/HTML.", "category": "Productivity"},
    {"name": "Screenshot Annotator", "desc": "Quickly mark up screenshots with arrows and text.", "category": "Productivity"},
    {"name": "CSV Cleaner", "desc": "Deduplicate, filter, and normalize CSV datasets.", "category": "Data"},
    {"name": "UUID Maker", "desc": "Generate v4 UUIDs and copy to clipboard.", "category": "Utility"},
    {"name": "Password Generator", "desc": "Create strong passwords with custom rules.", "category": "Security"},
    {"name": "Hash Checker", "desc": "Compute MD5/SHA checksums to verify files.", "category": "Security"},
]

CATEGORIES = ["All", "Media", "Design", "Developer", "Productivity", "Data", "Utility", "Security"]


# ---------- UI Components ----------
class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_nav: Callable[[str], None], on_toggle: Callable[[], None]):
        super().__init__(master, corner_radius=0, fg_color=("gray95", "gray10"))
        self.on_nav = on_nav
        self.on_toggle = on_toggle

        self.grid_rowconfigure(6, weight=1)  # push settings to bottom

        self.logo = ctk.CTkLabel(self, text=APP_TITLE, font=ctk.CTkFont(size=18, weight="bold"))
        self.logo.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")

        self.collapse_btn = ctk.CTkButton(self, text="⟨⟨  Thu gọn", command=self.on_toggle, height=36)
        self.collapse_btn.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="we")

        self.nav_home = ctk.CTkButton(self, text="🏠  Trang chủ", anchor="w", command=lambda: self.on_nav("home"))
        self.nav_tools = ctk.CTkButton(self, text="🧰  Tất cả công cụ", anchor="w", command=lambda: self.on_nav("tools"))
        self.nav_fav = ctk.CTkButton(self, text="⭐  Yêu thích", anchor="w", command=lambda: self.on_nav("favorites"))
        self.nav_recent = ctk.CTkButton(self, text="🕘  Gần đây", anchor="w", command=lambda: self.on_nav("recent"))

        for i, btn in enumerate((self.nav_home, self.nav_tools, self.nav_fav, self.nav_recent), start=2):
            btn.grid(row=i, column=0, padx=12, pady=6, sticky="we")

        self.sep = ctk.CTkFrame(self, height=1, fg_color=("gray80", "gray20"))
        self.sep.grid(row=6, column=0, padx=12, pady=12, sticky="we")

        self.settings = ctk.CTkButton(self, text="⚙️  Cài đặt", anchor="w", command=lambda: self.on_nav("settings"))
        self.settings.grid(row=7, column=0, padx=12, pady=(0, 16), sticky="we")

    def set_collapsed(self, collapsed: bool):
        """Visually toggle between expanded and collapsed states."""
        if collapsed:
            self.logo.configure(text="TH")
            self.collapse_btn.configure(text="⟩⟩")
            for btn in (self.nav_home, self.nav_tools, self.nav_fav, self.nav_recent, self.settings):
                # Left-align icons only (truncate text)
                text = btn.cget("text")
                icon = text.split()[0] if text else ""
                btn.configure(text=icon, anchor="center")
        else:
            self.logo.configure(text=APP_TITLE)
            self.collapse_btn.configure(text="⟨⟨  Thu gọn")
            self.nav_home.configure(text="🏠  Trang chủ", anchor="w")
            self.nav_tools.configure(text="🧰  Tất cả công cụ", anchor="w")
            self.nav_fav.configure(text="⭐  Yêu thích", anchor="w")
            self.nav_recent.configure(text="🕘  Gần đây", anchor="w")
            self.settings.configure(text="⚙️  Cài đặt", anchor="w")


class ToolCard(ctk.CTkFrame):
    def __init__(self, master, name: str, desc: str, category: str, on_open: Optional[Callable[[str], None]] = None):
        super().__init__(master, corner_radius=12, border_width=1, fg_color=("white", "#151515"), border_color=("gray85", "gray22"))
        self.on_open = on_open
        self.name = name
        self.category = category

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text=name, font=ctk.CTkFont(size=15, weight="bold"), justify="left")
        title.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="w")

        category_lbl = ctk.CTkLabel(self, text=category, text_color=("gray25", "gray70"))
        category_lbl.grid(row=1, column=0, padx=14, sticky="w")

        desc_lbl = ctk.CTkLabel(self, text=desc, wraplength=280, justify="left")
        desc_lbl.grid(row=2, column=0, padx=14, pady=(6, 10), sticky="we")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=3, column=0, padx=12, pady=(4, 12), sticky="we")
        btn_row.grid_columnconfigure((0, 1, 2), weight=1)

        open_btn = ctk.CTkButton(btn_row, text="Mở", command=lambda: self.on_open(name) if self.on_open else None)
        open_btn.grid(row=0, column=0, sticky="we", padx=(2, 6))

        fav_btn = ctk.CTkButton(btn_row, text="⭐ Lưu", command=lambda: print(f"[favorite] {name}"))
        fav_btn.grid(row=0, column=1, sticky="we", padx=6)

        more_btn = ctk.CTkButton(btn_row, text="⋯", width=36, command=lambda: print(f"[more] {name}"))
        more_btn.grid(row=0, column=2, sticky="e", padx=(6, 2))


class TopBar(ctk.CTkFrame):
    def __init__(self, master, on_search: Callable[[str], None]):
        super().__init__(master, corner_radius=0, fg_color=("white", "#0f0f0f"))
        self.grid_columnconfigure(0, weight=1)
        self.on_search = on_search

        self.search = ctk.CTkEntry(self, placeholder_text="Tìm kiếm công cụ… (gõ để lọc)")
        self.search.grid(row=0, column=0, padx=(16, 8), pady=12, sticky="we")
        self.search.bind("<KeyRelease>", self._on_key)

        self.appearance = ctk.CTkOptionMenu(self, values=["System", "Light", "Dark"], command=self._on_appearance)
        self.appearance.set("System")
        self.appearance.grid(row=0, column=1, padx=(8, 16), pady=12)

    def _on_key(self, event=None):
        self.on_search(self.search.get().strip())

    @staticmethod
    def _on_appearance(value: str):
        ctk.set_appearance_mode(value)


class Filters(ctk.CTkFrame):
    def __init__(self, master, categories: List[str], on_change: Callable[[str], None]):
        super().__init__(master, corner_radius=0, fg_color=("white", "#0f0f0f"))
        self.grid_columnconfigure(0, weight=1)
        self._seg = ctk.CTkSegmentedButton(self, values=categories, command=on_change)
        self._seg.grid(row=0, column=0, sticky="w", padx=16, pady=(4, 10))
        self._seg.set(categories[0])  # default "All"

    def current(self) -> str:
        return self._seg.get()


class CardGrid(ctk.CTkScrollableFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color=("white", "#0f0f0f"))
        # 3 responsive columns
        self.grid_columnconfigure((0, 1, 2), weight=1, uniform="cards")

    def clear(self):
        for child in list(self.children.values()):
            child.destroy()

    def render(self, items: List[Dict], on_open: Callable[[str], None]):
        self.clear()
        if not items:
            ctk.CTkLabel(self, text="Không có công cụ nào khớp bộ lọc.", text_color=("gray40", "gray60")).grid(
                row=0, column=0, padx=24, pady=24, sticky="w"
            )
            return

        max_cols = 3
        for idx, tool in enumerate(items):
            r, c = divmod(idx, max_cols)
            card = ToolCard(self, tool["name"], tool["desc"], tool["category"], on_open=on_open)
            card.grid(row=r, column=c, padx=12, pady=12, sticky="nsew")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(APP_MIN_W, APP_MIN_H)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")  # or "dark-blue" / "green" or a path to JSON

        # Layout: [sidebar][content]
        self.grid_columnconfigure(0, weight=0, minsize=220)   # sidebar width
        self.grid_columnconfigure(1, weight=1)                # content
        self.grid_rowconfigure(2, weight=1)                   # card grid expands

        # Sidebar
        self._sidebar_collapsed = False
        self.sidebar = Sidebar(self, on_nav=self.on_nav, on_toggle=self.toggle_sidebar)
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsew")

        # Top bar
        self.topbar = TopBar(self, on_search=self.on_search)
        self.topbar.grid(row=0, column=1, sticky="nsew")

        # Filters
        self.filters = Filters(self, categories=CATEGORIES, on_change=self.on_filter_change)
        self.filters.grid(row=1, column=1, sticky="nsew")

        # Card grid
        self.card_grid = CardGrid(self)
        self.card_grid.grid(row=2, column=1, sticky="nsew")

        # Initial render
        self.all_tools = TOOLS[:]  # copy
        self.current_query = ""
        self.current_category = "All"
        self._apply_filters_and_render()

    # ----- Sidebar & navigation -----
    def toggle_sidebar(self):
        self._sidebar_collapsed = not self._sidebar_collapsed
        self.sidebar.set_collapsed(self._sidebar_collapsed)
        # Animate by changing minsize
        self.grid_columnconfigure(0, minsize=60 if self._sidebar_collapsed else 220)

    def on_nav(self, route: str):
        print(f"[nav] {route} clicked")
        # You can switch views here. For now we stay on the dashboard.

    # ----- Search / Filters -----
    def on_search(self, query: str):
        self.current_query = query
        self._apply_filters_and_render()

    def on_filter_change(self, category: str):
        self.current_category = category
        self._apply_filters_and_render()

    def _apply_filters_and_render(self):
        q = self.current_query.lower().strip()
        cat = self.current_category

        def include(tool: Dict) -> bool:
            if cat != "All" and tool["category"] != cat:
                return False
            if q and (q not in tool["name"].lower() and q not in tool["desc"].lower() and q not in tool["category"].lower()):
                return False
            return True

        filtered = [t for t in self.all_tools if include(t)]
        self.card_grid.render(filtered, on_open=self.open_tool)

    # ----- Actions -----
    def open_tool(self, tool_name: str):
        # Replace with real routing/opening logic
        ctk.CTkMessagebox = getattr(ctk, "CTkMessagebox", None)  # optional dependency in some setups
        if ctk.CTkMessagebox:
            ctk.CTkMessagebox(title="Open Tool", message=f"Mở công cụ: {tool_name}")
        else:
            print(f"[open] {tool_name}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
