
import sys
import os
import re
import base64
import hashlib
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

from PySide6.QtCore import Qt, QTimer, QSize, QMimeData
from PySide6.QtGui import QAction, QIcon, QPixmap, QGuiApplication, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QGroupBox, QFrame, QStatusBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QCheckBox, QProgressBar, QProgressDialog, QMessageBox, QSplitter, QTextEdit
)

_PLACEHOLDER_PNG = (
    b"iVBORw0KGgoAAAANSUhEUgAAAIAAAABgCAYAAAB5c1m+AAAACXBIWXMAAAsSAAALEgHS3X78AAABWUlEQVR4nO3QwQkCQRRG4b8k"
    b"s7QdT9k4S8Qm3b3yC5E3i6n2B0Fh8EwzR4GqQm7oEAAAAAAAAAAAAAAD4Z4QJxq8b0Hnq0v3m8bKZfYk8d6R8x1y9m5xw3mH3s/9m"
    b"cN6Hj5JrXv2kI4p2uY7w0v3mTz9rjHcB1y0k3lQ4w2J8Q9e3m3fM5p3bYf0QnWQb7m7hCzZr4w2v8LB1A1YkJ4fY3D9n3i9p9x8G8"
    b"2b7yKp8rG2h1Jm6y2Q/pw2OGlg+R7i8dZbNQe9n8jzq4t9m8y2WZ3bU6h6mN3rHq1O2cWmL7QF3o9g7b9qM7wHnoyQ6m2+oPzv6P3"
    b"G8h0nq1V5c9r9pS5fYQf0ZzHj0AAAAAAAAAAAAAAAB+7wJx1JkWmN/1WwAAAABJRU5ErkJggg=="
)


def placeholder_pixmap() -> QPixmap:
    pix = QPixmap()
    pix.loadFromData(base64.b64decode(_PLACEHOLDER_PNG))
    return pix


# ----------------------------
# Platform recognition (fake)
# ----------------------------
@dataclass
class Platform:
    name: str
    key: str
    patterns: List[str]
    color: str  # hex, used in badge

PLATFORMS: List[Platform] = [
    Platform(name="TikTok",  key="tiktok",  patterns=[r"tiktok\.com"],               color="#00F2EA"),
    Platform(name="Douyin",  key="douyin",  patterns=[r"douyin\.com"],               color="#F40076"),
    Platform(name="Facebook",key="facebook",patterns=[r"facebook\.com|fb\.watch"],   color="#1877F2"),
    Platform(name="Instagram",key="instagram",patterns=[r"instagram\.com"],          color="#E1306C"),
    Platform(name="X / Twitter",key="twitter",patterns=[r"twitter\.com|x\.com"],     color="#111111"),
    Platform(name="YouTube", key="youtube", patterns=[r"youtube\.com|youtu\.be"],    color="#FF0000"),
    Platform(name="Pinterest",key="pinterest",patterns=[r"pinterest\.com|pin\.it"],  color="#E60023"),
    Platform(name="Reddit", key="reddit",  patterns=[r"reddit\.com"],                color="#FF4500"),
]


def detect_platform(url: str) -> Optional[Platform]:
    url = url.strip().lower()
    for p in PLATFORMS:
        for pt in p.patterns:
            if re.search(pt, url):
                return p
    return None


# ----------------------------
# Fake analysis + options
# ----------------------------

def seeded_rand(url: str) -> random.Random:
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()
    seed = int(h[:8], 16)
    return random.Random(seed)


def fake_analyze(url: str) -> Dict:
    """Return a fake info dict with preview + media options derived from url hash.
    Structure:
    {
        'title': str,
        'author': str,
        'duration': str or None,
        'type': 'video'|'image'|'gallery',
        'thumb': QPixmap,
        'video_opts': [ {quality, fmt, size}, ... ],
        'audio_opts': [ {quality, fmt, size}, ... ],
        'image_opts': [ {resolution, fmt, size}, ... ]
    }
    """
    rnd = seeded_rand(url)
    # Fake basic metadata
    words = ["Dance", "Travel", "Food", "Vlog", "Prank", "Tutorial", "Review", "Memes", "Tech", "Fashion"]
    title = f"{rnd.choice(words)} #{rnd.randint(1000,9999)}"
    author = f"user_{rnd.randint(10000,99999)}"
    duration_secs = rnd.randint(8, 240)
    duration = f"{duration_secs//60:02d}:{duration_secs%60:02d}"

    # Randomly decide media type bias by URL hash
    media_type = rnd.choice(["video", "video", "image", "gallery"])  # favor video

    # Fake options
    video_qualities = [("1080p", "MP4"), ("720p", "MP4"), ("480p", "MP4"), ("360p", "MP4")]
    audio_qualities = [("320 kbps", "MP3"), ("192 kbps", "MP3"), ("128 kbps", "MP3")]
    image_res = [("2160x3840", "JPG"), ("1440x2560", "JPG"), ("1080x1920", "JPG")]

    def size_for(q: str) -> str:
        base = sum(ord(c) for c in q) % 50 + 10
        return f"{base + rnd.randint(0,15)} MB"

    video_opts = [
        {"quality": q, "fmt": f, "size": size_for(q)} for q, f in video_qualities
    ]
    audio_opts = [
        {"quality": q, "fmt": f, "size": size_for(q)} for q, f in audio_qualities
    ]
    image_opts = [
        {"resolution": r, "fmt": f, "size": size_for(r)} for r, f in image_res
    ]

    return {
        "title": title,
        "author": author,
        "duration": duration if media_type == "video" else None,
        "type": media_type,
        "thumb": placeholder_pixmap(),
        "video_opts": video_opts,
        "audio_opts": audio_opts,
        "image_opts": image_opts,
    }


# ----------------------------
# Widgets
# ----------------------------
class UrlLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Dán URL bất kỳ (TikTok, Douyin, Facebook, Instagram, X, YouTube, …)")
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        if e.mimeData().hasText():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dropEvent(self, e: QDropEvent) -> None:
        text = e.mimeData().text()
        if text:
            # Strip url from mime text (may include 'url(... )')
            text = text.strip()
            if text.startswith("file://"):
                return
            self.setText(text)
            e.acceptProposedAction()
        else:
            super().dropEvent(e)


class Badge(QLabel):
    def __init__(self, text: str = "Unknown", color: str = "#666"):
        super().__init__(text)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 14px;
                padding: 6px 12px;
                font-weight: 600;
            }}
        """)


class Divider(QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setStyleSheet("color: #333;")


class OptionsTable(QTableWidget):
    def __init__(self, columns: List[str]):
        super().__init__(0, len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("alternate-background-color: #1f1f1f;")

    def add_row(self, cells: List[str]):
        row = self.rowCount()
        self.insertRow(row)
        # First column is checkbox
        chk = QCheckBox()
        chk.setChecked(False)
        self.setCellWidget(row, 0, chk)
        for i, text in enumerate(cells, start=1):
            item = QTableWidgetItem(text)
            self.setItem(row, i, item)

    def selected_items(self) -> List[int]:
        rows = []
        for r in range(self.rowCount()):
            w = self.cellWidget(r, 0)
            if isinstance(w, QCheckBox) and w.isChecked():
                rows.append(r)
        return rows

    def check_all(self, state: bool):
        for r in range(self.rowCount()):
            w = self.cellWidget(r, 0)
            if isinstance(w, QCheckBox):
                w.setChecked(state)


# ----------------------------
# Main Window
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Social Downloader Hub – UI Demo")
        self.setWindowIcon(self._app_icon())
        self.resize(1100, 720)

        self.platform: Optional[Platform] = None
        self.analysis: Optional[Dict] = None

        # Actions / Menu
        self._create_actions()
        self._create_menu()

        # Core UI
        self.url_edit = UrlLineEdit()
        self.platform_badge = Badge("Chưa nhận diện", "#555")
        btn_paste = QPushButton("Dán từ Clipboard")
        btn_clear = QPushButton("Xoá")
        btn_analyze = QPushButton("Phân tích URL")
        btn_paste.clicked.connect(self.on_paste)
        btn_clear.clicked.connect(self.on_clear)
        btn_analyze.clicked.connect(self.on_analyze)

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("URL:"))
        url_row.addWidget(self.url_edit, 1)
        url_row.addWidget(self.platform_badge)
        url_row.addWidget(btn_paste)
        url_row.addWidget(btn_clear)
        url_row.addWidget(btn_analyze)

        # Left: Preview & Info
        self.preview = QLabel()
        self.preview.setPixmap(placeholder_pixmap().scaledToWidth(480, Qt.SmoothTransformation))
        self.preview.setFixedHeight(270)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("border-radius:16px; background:#0f0f0f;")

        info_box = QGroupBox("Thông tin nội dung (giả lập)")
        grid = QGridLayout(info_box)
        self.lbl_title = QLabel("–")
        self.lbl_author = QLabel("–")
        self.lbl_type = QLabel("–")
        self.lbl_duration = QLabel("–")
        grid.addWidget(QLabel("Tiêu đề:"), 0, 0)
        grid.addWidget(self.lbl_title, 0, 1)
        grid.addWidget(QLabel("Tác giả:"), 1, 0)
        grid.addWidget(self.lbl_author, 1, 1)
        grid.addWidget(QLabel("Loại:"), 2, 0)
        grid.addWidget(self.lbl_type, 2, 1)
        grid.addWidget(QLabel("Thời lượng:"), 3, 0)
        grid.addWidget(self.lbl_duration, 3, 1)

        left_col = QVBoxLayout()
        left_col.addLayout(url_row)
        left_col.addWidget(Divider())
        left_col.addWidget(self.preview)
        left_col.addWidget(info_box)
        left_widget = QWidget()
        left_widget.setLayout(left_col)

        # Right: Tabs & controls
        self.tabs = QTabWidget()
        # Video tab
        self.video_table = OptionsTable(["Chọn", "Chất lượng", "Định dạng", "Kích thước", "Nguồn"])
        self.btn_video_select = QPushButton("Chọn hết")
        self.btn_video_unselect = QPushButton("Bỏ chọn")
        self.btn_video_select.clicked.connect(lambda: self.video_table.check_all(True))
        self.btn_video_unselect.clicked.connect(lambda: self.video_table.check_all(False))
        vbox_v = QVBoxLayout()
        vbox_v.addWidget(self.video_table)
        row_v = QHBoxLayout()
        row_v.addWidget(self.btn_video_select)
        row_v.addWidget(self.btn_video_unselect)
        row_v.addStretch(1)
        vbox_v.addLayout(row_v)
        tab_video = QWidget(); tab_video.setLayout(vbox_v)

        # Audio tab
        self.audio_table = OptionsTable(["Chọn", "Chất lượng", "Định dạng", "Kích thước", "Nguồn"])
        self.btn_audio_select = QPushButton("Chọn hết")
        self.btn_audio_unselect = QPushButton("Bỏ chọn")
        self.btn_audio_select.clicked.connect(lambda: self.audio_table.check_all(True))
        self.btn_audio_unselect.clicked.connect(lambda: self.audio_table.check_all(False))
        vbox_a = QVBoxLayout()
        vbox_a.addWidget(self.audio_table)
        row_a = QHBoxLayout()
        row_a.addWidget(self.btn_audio_select)
        row_a.addWidget(self.btn_audio_unselect)
        row_a.addStretch(1)
        vbox_a.addLayout(row_a)
        tab_audio = QWidget(); tab_audio.setLayout(vbox_a)

        # Image tab
        self.image_table = OptionsTable(["Chọn", "Độ phân giải", "Định dạng", "Kích thước", "Nguồn"])
        self.btn_image_select = QPushButton("Chọn hết")
        self.btn_image_unselect = QPushButton("Bỏ chọn")
        self.btn_image_select.clicked.connect(lambda: self.image_table.check_all(True))
        self.btn_image_unselect.clicked.connect(lambda: self.image_table.check_all(False))
        vbox_i = QVBoxLayout()
        vbox_i.addWidget(self.image_table)
        row_i = QHBoxLayout()
        row_i.addWidget(self.btn_image_select)
        row_i.addWidget(self.btn_image_unselect)
        row_i.addStretch(1)
        vbox_i.addLayout(row_i)
        tab_image = QWidget(); tab_image.setLayout(vbox_i)

        self.tabs.addTab(tab_video, "Video")
        self.tabs.addTab(tab_audio, "Âm thanh")
        self.tabs.addTab(tab_image, "Ảnh")

        # Output controls
        output_box = QGroupBox("Thiết lập tải xuống (giả lập)")
        ob_grid = QGridLayout(output_box)
        self.output_dir_edit = QLineEdit(os.path.join(os.path.expanduser("~"), "Downloads"))
        btn_browse = QPushButton("Chọn thư mục…")
        btn_browse.clicked.connect(self.on_browse)
        self.filename_tpl = QLineEdit("{title} - {author}")
        self.chk_autorename = QCheckBox("Tự động tránh trùng tên")
        self.chk_autorename.setChecked(True)
        self.btn_download = QPushButton("Tải các mục đã chọn")
        self.btn_download.setEnabled(False)
        self.btn_download.clicked.connect(self.on_download)

        ob_grid.addWidget(QLabel("Thư mục lưu:"), 0, 0)
        ob_grid.addWidget(self.output_dir_edit, 0, 1)
        ob_grid.addWidget(btn_browse, 0, 2)
        ob_grid.addWidget(QLabel("Mẫu tên file:"), 1, 0)
        ob_grid.addWidget(self.filename_tpl, 1, 1, 1, 2)
        ob_grid.addWidget(self.chk_autorename, 2, 1)
        ob_grid.addWidget(self.btn_download, 3, 1)

        right_col = QVBoxLayout()
        right_col.addWidget(self.tabs, 1)
        right_col.addWidget(output_box)
        right_widget = QWidget(); right_widget.setLayout(right_col)

        # Splitter
        splitter = QSplitter()
        splitter.setHandleWidth(10)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([520, 580])

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Central
        root = QVBoxLayout()
        root.addWidget(splitter)
        cw = QWidget(); cw.setLayout(root)
        self.setCentralWidget(cw)

        # Initial style
        self._apply_dark_theme()
        self._apply_qss()

        # Signals
        self.url_edit.textChanged.connect(self.on_url_changed)

    # ----- UI helpers -----
    def _create_actions(self):
        self.act_theme = QAction("Chuyển theme sáng/tối", self)
        self.act_theme.setCheckable(True)
        self.act_theme.setChecked(True)  # dark by default
        self.act_theme.triggered.connect(self.on_toggle_theme)

        self.act_about = QAction("Giới thiệu", self)
        self.act_about.triggered.connect(self.on_about)

        self.act_quit = QAction("Thoát", self)
        self.act_quit.triggered.connect(self.close)

    def _create_menu(self):
        mb = self.menuBar()
        m_app = mb.addMenu("Ứng dụng")
        m_app.addAction(self.act_theme)
        m_app.addSeparator()
        m_app.addAction(self.act_quit)
        m_help = mb.addMenu("Trợ giúp")
        m_help.addAction(self.act_about)

    def _apply_qss(self):
        self.setStyleSheet(
            """
            QMainWindow { background: #0b0b0b; }
            QLabel { color: #eaeaea; }
            QLineEdit, QTextEdit {
                background: #161616; color: #eaeaea; border: 1px solid #2a2a2a; border-radius: 10px; padding: 8px;
            }
            QPushButton {
                background: #262626; color: #fff; border: 1px solid #333; border-radius: 12px; padding: 8px 14px; font-weight: 600;
            }
            QPushButton:hover { background: #2f2f2f; }
            QPushButton:disabled { background: #1a1a1a; color: #666; border-color: #222; }
            QGroupBox { border: 1px solid #2a2a2a; border-radius: 14px; margin-top: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
            QTabWidget::pane { border: 1px solid #2a2a2a; border-radius: 10px; }
            QTabBar::tab { background: #181818; color: #ddd; padding: 8px 16px; border-top-left-radius: 10px; border-top-right-radius: 10px; }
            QTabBar::tab:selected { background: #222; }
            QTableWidget { background: #121212; color: #eaeaea; gridline-color: #2a2a2a; border-radius: 10px; }
            QHeaderView::section { background: #1c1c1c; color: #ddd; border: none; padding: 6px; }
            QStatusBar { background: #0f0f0f; color: #bbb; }
            QSplitter::handle { background: #141414; }
            QCheckBox { color: #eaeaea; }
            QMenuBar { background: #0f0f0f; color: #ddd; }
            QMenu { background: #111; color: #eee; border: 1px solid #2a2a2a; }
            """
        )

    def _apply_dark_theme(self):
        QApplication.setStyle("Fusion")
        pal = self.palette()
        pal.setColor(pal.window, Qt.black)
        pal.setColor(pal.windowText, Qt.white)
        pal.setColor(pal.Base, Qt.black)
        pal.setColor(pal.AlternateBase, Qt.black)
        pal.setColor(pal.ToolTipBase, Qt.white)
        pal.setColor(pal.ToolTipText, Qt.white)
        pal.setColor(pal.Text, Qt.white)
        pal.setColor(pal.Button, Qt.black)
        pal.setColor(pal.ButtonText, Qt.white)
        pal.setColor(pal.Highlight, Qt.darkGray)
        pal.setColor(pal.HighlightedText, Qt.white)
        self.setPalette(pal)

    def _apply_light_theme(self):
        QApplication.setStyle("Fusion")
        self.setPalette(QApplication.palette())
        # minimal light QSS reset for tables
        self.setStyleSheet("")

    def _app_icon(self) -> QIcon:
        # Reuse placeholder as icon for simplicity
        pm = placeholder_pixmap().scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return QIcon(pm)

    # ----- Slots -----
    def on_toggle_theme(self):
        if self.act_theme.isChecked():
            self._apply_dark_theme(); self._apply_qss()
        else:
            self._apply_light_theme()
        self.status.showMessage("Đã chuyển theme", 2000)

    def on_about(self):
        QMessageBox.information(self, "Giới thiệu",
                                "Social Downloader Hub (UI Demo)\n\n"
                                "• Mô phỏng giao diện tool hub tải nội dung MXH.\n"
                                "• Hoạt động offline, dữ liệu giả lập.\n"
                                "• Viết bằng PySide6 (Qt).")

    def on_paste(self):
        cb = QGuiApplication.clipboard()
        text = cb.text()
        if text:
            self.url_edit.setText(text)
            self.status.showMessage("Đã dán URL từ clipboard", 2000)
        else:
            self.status.showMessage("Clipboard trống", 2000)

    def on_clear(self):
        self.url_edit.clear()
        self.platform_badge.setText("Chưa nhận diện")
        self.platform_badge.setStyleSheet("background:#555; color:white; border-radius:14px; padding:6px 12px; font-weight:600;")
        self.preview.setPixmap(placeholder_pixmap().scaledToWidth(480, Qt.SmoothTransformation))
        self.lbl_title.setText("–")
        self.lbl_author.setText("–")
        self.lbl_type.setText("–")
        self.lbl_duration.setText("–")
        for t in (self.video_table, self.audio_table, self.image_table):
            t.setRowCount(0)
        self.btn_download.setEnabled(False)

    def on_browse(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu", self.output_dir_edit.text() or os.path.expanduser("~"))
        if d:
            self.output_dir_edit.setText(d)

    def on_url_changed(self, text: str):
        p = detect_platform(text)
        if p:
            self.platform = p
            self.platform_badge.setText(p.name)
            self.platform_badge.setStyleSheet(f"background:{p.color}; color:white; border-radius:14px; padding:6px 12px; font-weight:600;")
        else:
            self.platform = None
            self.platform_badge.setText("Không rõ nền tảng")
            self.platform_badge.setStyleSheet("background:#777; color:white; border-radius:14px; padding:6px 12px; font-weight:600;")

    def on_analyze(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Thiếu URL", "Hãy dán URL trước đã nhé.")
            return
        p = detect_platform(url)
        if not p:
            QMessageBox.warning(self, "Không nhận diện được", "URL không khớp nền tảng đã hỗ trợ (demo). Vẫn sẽ phân tích giả lập.")
        self.analysis = fake_analyze(url)
        self._populate_analysis()
        self.status.showMessage("Phân tích xong (giả lập)", 2000)

    def _populate_analysis(self):
        if not self.analysis:
            return
        a = self.analysis
        self.preview.setPixmap(a["thumb"].scaledToWidth(480, Qt.SmoothTransformation))
        self.lbl_title.setText(a["title"])
        self.lbl_author.setText(a["author"])
        self.lbl_type.setText(a["type"].upper())
        self.lbl_duration.setText(a["duration"] or "–")

        # Fill tables
        self.video_table.setRowCount(0)
        for opt in a["video_opts"]:
            self.video_table.add_row([opt["quality"], opt["fmt"], opt["size"], self.platform.name if self.platform else "Auto"])  # type: ignore
        self.audio_table.setRowCount(0)
        for opt in a["audio_opts"]:
            self.audio_table.add_row([opt["quality"], opt["fmt"], opt["size"], self.platform.name if self.platform else "Auto"])  # type: ignore
        self.image_table.setRowCount(0)
        for opt in a["image_opts"]:
            self.image_table.add_row([opt["resolution"], opt["fmt"], opt["size"], self.platform.name if self.platform else "Auto"])  # type: ignore

        self.btn_download.setEnabled(True)

    def on_download(self):
        out_dir = self.output_dir_edit.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "Thiếu thư mục lưu", "Hãy chọn thư mục lưu trước.")
            return
        if not os.path.isdir(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Lỗi thư mục", f"Không tạo được thư mục: {e}")
                return

        selections = []
        for kind, table in (("video", self.video_table), ("audio", self.audio_table), ("image", self.image_table)):
            for r in table.selected_items():
                if kind == "video":
                    q = table.item(r, 1).text(); fmt = table.item(r, 2).text(); size = table.item(r, 3).text()
                    fname = self._render_filename(kind, q, fmt)
                elif kind == "audio":
                    q = table.item(r, 1).text(); fmt = table.item(r, 2).text(); size = table.item(r, 3).text()
                    fname = self._render_filename(kind, q, fmt)
                else:
                    q = table.item(r, 1).text(); fmt = table.item(r, 2).text(); size = table.item(r, 3).text()
                    fname = self._render_filename(kind, q, fmt)
                selections.append((kind, q, fmt, size, fname))

        if not selections:
            QMessageBox.information(self, "Chưa chọn mục", "Hãy tick chọn ít nhất 1 dòng trong bảng.")
            return

        # Simulate download via single progress dialog over N items
        total_steps = 100 * len(selections)
        dlg = QProgressDialog("Đang tải (giả lập)…", "Huỷ", 0, total_steps, self)
        dlg.setWindowModality(Qt.windowModal)
        dlg.setAutoClose(True)
        dlg.setMinimumWidth(420)
        step = 0

        def tick():
            nonlocal step
            if dlg.wasCanceled():
                timer.stop()
                self.status.showMessage("Đã huỷ tải (giả lập)", 3000)
                return
            # Increase in random chunks per item
            inc = random.randint(1, 6)
            step = min(step + inc, total_steps)
            dlg.setValue(step)
            if step >= total_steps:
                timer.stop()
                self.status.showMessage(f"Hoàn tất tải {len(selections)} mục (giả lập)", 4000)
                QMessageBox.information(self, "Xong", f"Đã mô phỏng tải xong {len(selections)} mục. (Không tạo file thật)")

        timer = QTimer(self)
        timer.timeout.connect(tick)
        timer.start(30)
        dlg.exec()

    def _render_filename(self, kind: str, quality: str, fmt: str) -> str:
        if not self.analysis:
            return "output"
        a = self.analysis
        title = re.sub(r"[\\/:*?\"<>|]", "_", a["title"])  # sanitize
        author = re.sub(r"[\\/:*?\"<>|]", "_", a["author"])  # sanitize
        base = self.filename_tpl.text().format(title=title, author=author, kind=kind, quality=quality, fmt=fmt)
        return f"{base}.{fmt.lower()}"


# ----------------------------
# Main
# ----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
