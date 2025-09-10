# customtk_ui.py
# Demo UI using CustomTkinter to mimic the look in the screenshot
# pip install customtkinter

import customtkinter as ctk
import tkinter as tk

# ---- THEME ----
ctk.set_default_color_theme("dark-blue")  # base accents
ctk.set_appearance_mode("dark")

BG = "#121212"
CARD_BG = "#1a1a1a"
FG = "#e5e7eb"
MUTED = "#9ca3af"
BORDER = "#2a2a2a"
ACCENT = "#3b82f6"
DANGER = "#ef4444"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
DISABLED_BG = "#242424"
DISABLED_FG = "#606060"

class Field(ctk.CTkFrame):
    """
    A labeled input container that can render different states:
    default, focus, error, success, disabled
    """
    def __init__(self, master, label="LABEL", state="default",
                 field_type="text", placeholder="Text field data",
                 options=None, width=280, **kwargs):
        super().__init__(master, fg_color=CARD_BG, **kwargs)
        self.state = state
        self.field_type = field_type
        self.width = width
        self.placeholder = placeholder
        self.options = options or ["Option data", "Option data", "Option data"]
        self.configure(corner_radius=12, border_width=1, border_color=BORDER)

        # label
        self.lbl = ctk.CTkLabel(self, text=label.upper(), text_color=MUTED, font=("Inter", 11, "bold"))
        self.lbl.grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))

        # input area
        if field_type == "text":
            self.input = ctk.CTkEntry(self, placeholder_text=placeholder,
                                      width=width, height=34, corner_radius=8)
        else:
            # OptionMenu acts like dropdown
            self.input = ctk.CTkOptionMenu(self, values=self.options,
                                           width=width, height=34, corner_radius=8)
            self.input.set(placeholder)

        self.input.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 10))

        # icon / status
        self.icon = ctk.CTkLabel(self, text="", width=24)
        self.icon.place(relx=1.0, rely=0.5, x=-10, y=0, anchor="e")

        self.apply_state()

    def set_border(self, color):
        # Wrap input in a frame to simulate colored borders
        # CustomTkinter doesn't expose border-color for Entry directly, so we overlay a frame
        if hasattr(self, "_border_frame"):
            self._border_frame.destroy()
        self._border_frame = ctk.CTkFrame(self, fg_color=color, corner_radius=9)
        self._border_frame.place(in_=self.input, relx=0.5, rely=0.5, anchor="c",
                                 relwidth=1.0, relheight=1.0, x=0, y=0)
        # raise the input above
        self.input.lift()

    def apply_state(self):
        # baseline
        self.icon.configure(text="")
        self.input.configure(state="normal", fg_color="white", text_color="black",
                             placeholder_text_color="#6b7280")
        self.set_border(BORDER)

        if self.state == "focus":
            self.set_border(ACCENT)
            # give focus on start
            self.after(300, lambda: self.input.focus_set())

        elif self.state == "error":
            self.set_border(DANGER)
            self.icon.configure(text="  ✖", text_color=DANGER)

        elif self.state == "success":
            self.set_border(SUCCESS)
            self.icon.configure(text="  ✔", text_color=SUCCESS)

        elif self.state == "warning":
            self.set_border(WARNING)
            self.icon.configure(text="  ⚠", text_color=WARNING)

        elif self.state == "disabled":
            self.input.configure(state="disabled", fg_color=DISABLED_BG, text_color=DISABLED_FG)
            self.set_border(BORDER)

def build_column(master, xcol, start_focus=False):
    # Column with five rows matching the screenshot
    rows = [
        ("LABEL", "default", "text", "Text field data"),
        ("LABEL", "focus",   "text", "Text field data"),
        ("LABEL", "error",   "text", "Text field data"),
        ("LABEL", "success", "text", "Text field data"),
        ("LABEL", "disabled","text", "Text field data"),
    ]
    drows = [
        ("LABEL", "default", "dropdown", "Dropdown field data"),
        ("LABEL", "focus",   "dropdown", "Dropdown field data"),
        ("LABEL", "warning", "dropdown", "Dropdown field data"),
        ("LABEL", "default", "dropdown", "Dropdown field data"),
        ("LABEL", "disabled","dropdown", "Dropdown field data"),
    ]

    for i, r in enumerate(rows):
        Field(master, label=r[0], state=r[1], field_type="text", placeholder=r[3]).grid(
            row=i, column=xcol, padx=(16, 8), pady=(8, 4), sticky="ew"
        )
        Field(master, label=drows[i][0], state=drows[i][1],
              field_type="dropdown", placeholder=drows[i][3]).grid(
            row=i, column=xcol+1, padx=(8, 16), pady=(8, 4), sticky="ew"
        )

def main():
    root = ctk.CTk()
    root.title("CustomTkinter Form States Demo")
    root.geometry("820x580")
    root.configure(fg_color=BG)

    container = ctk.CTkFrame(root, fg_color=BG)
    container.pack(fill="both", expand=True)

    grid = ctk.CTkFrame(container, fg_color=BG)
    grid.pack(padx=12, pady=12, fill="both", expand=True)

    grid.grid_columnconfigure(0, weight=1, uniform="col")
    grid.grid_columnconfigure(1, weight=1, uniform="col")

    # dashed purple outline to mimic the screenshot bounds
    dash = ctk.CTkFrame(grid, fg_color=BG, border_width=2, border_color="#8b5cf6", corner_radius=0)
    dash.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=4, pady=4)
    dash.grid_columnconfigure(0, weight=1, uniform="col")
    dash.grid_columnconfigure(1, weight=1, uniform="col")

    build_column(dash, 0)

    # footer note
    note = ctk.CTkLabel(root, text="States: default • focus • error • success • warning • disabled",
                        text_color=MUTED)
    note.pack(pady=(0, 10))

    root.mainloop()

if __name__ == "__main__":
    main()
