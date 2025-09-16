# media_downloader_fluent_polished.py
# PySide6 + qfluentwidgets (community)
# pip install PySide6 qfluentwidgets

import sys, time, random, base64, os, re
from dataclasses import dataclass
from typing import Optional, Union

from PySide6.QtCore import Qt, QSize, QRunnable, QThreadPool, QObject, Signal, QTimer
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame,
    QListWidgetItem, QSizePolicy, QListWidget, QScrollBar, QAbstractItemView, QSpacerItem
)

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, setTheme, Theme, setThemeColor,
    BodyLabel, CaptionLabel, ProgressBar, FluentIcon as FIF, isDarkTheme,
    LineEdit, PrimaryPushButton, InfoBar, InfoBarPosition
)

# ----------------- Theme & Styles -----------------
ACCENT = "#2563EB"  # blue-600
PNG1 = r"C:\source_code\tool-hub\pexels-hazardos-1535244.jpg"
PNG2 = r"C:\source_code\tool-hub\pexels-hazardos-1535244.jpg"
PNG3 = r"C:\source_code\tool-hub\pexels-hazardos-1535244.jpg"

LIGHT = {
    "bg_card": "#FFFFFF", "bg_card_alt": "#F6F8FA", "bg_track": "#E5E7EB",
    "border": "#E2E8F0", "text": "#0F172A", "subtext": "#475569"
}
DARK = {
    "bg_card": "#1E293B", "bg_card_alt": "#0F172A", "bg_track": "#334155",
    "border": "#334155", "text": "#F8FAFC", "subtext": "#CBD5E1"
}
def palette(): return DARK if isDarkTheme() else LIGHT

def apply_global_styles(widget: QWidget):
    c = palette()
    widget.setStyleSheet(f"""
    QListWidget {{ background: transparent; border: none; }}
    #ControlBar {{
        border-radius: 12px;
        background-color: {c['bg_card']};
        border: 1px solid {c['border']};
    }}
    #DownloadItem {{
        border-radius: 12px;
        background-color: {c['bg_card']};
        border: 1px solid {c['border']};
    }}
    #DownloadItem:hover {{ background-color: {c['bg_card_alt']}; }}
    BodyLabel, QLabel {{ color: {c['text']}; }}
    CaptionLabel {{ color: {c['subtext']}; }}

    QProgressBar {{
        border: 1px solid {c['border']};
        border-radius: 9px;
        background: {c['bg_track']};
        text-align: center;
        height: 18px;
        color: {c['text']};
        font-weight: 600;
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 9px;
        margin: 0px;
    }}
    """)

# ----------------- Helpers -----------------
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

def pm_placeholder(w=160, h=90) -> QPixmap:
    pm = QPixmap(w, h)
    pm.fill(QColor("#CBD5E1") if not isDarkTheme() else QColor("#475569"))
    return pm

def pm_from_source(data: Optional[Union[str, bytes]], w=160, h=90) -> QPixmap:
    if not data:
        return pm_placeholder(w, h)
    pm = QPixmap()
    try:
        if isinstance(data, str):
            if os.path.exists(data):
                pm.load(data)
            else:
                return pm_placeholder(w, h)
        elif isinstance(data, (bytes, bytearray)):
            raw = base64.b64decode(data)
            pm.loadFromData(raw)
    except Exception:
        return pm_placeholder(w, h)
    if pm.isNull():
        return pm_placeholder(w, h)
    return pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

# ----------------- Model + Worker -----------------
@dataclass
class DownloadTask:
    url: str
    description: str = "Đang phân tích…"
    size_text: str = "—"
    thumbnail: Optional[QPixmap] = None

class FakeWorkerSignals(QObject):
    progress = Signal(int)
    status = Signal(str)

class FakeWorker(QRunnable):
    """Demo worker: giả lập tiến độ tải. Thay thế bằng logic thật (yt-dlp, requests, ...)."""
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.s = FakeWorkerSignals()
    def run(self):
        self.s.status.emit("Đang tải…")
        for i in range(101):
            time.sleep(0.018 + random.uniform(0, 0.008))
            self.s.progress.emit(i)
        self.s.status.emit("Hoàn tất")

# ----------------- Smooth List -----------------
class SmoothListWidget(QListWidget):
    def __init__(self, parent=None, pixels_per_notch: int = 20, page_step: int = 280):
        super().__init__(parent)
        self.pixels_per_notch = pixels_per_notch
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setSpacing(6)
        self.setFrameShape(QFrame.NoFrame)
        sb: QScrollBar = self.verticalScrollBar()
        sb.setSingleStep(max(1, self.pixels_per_notch // 2))
        sb.setPageStep(page_step)

    def wheelEvent(self, e):
        if not e.pixelDelta().isNull():
            delta_px = e.pixelDelta().y()
        else:
            notches = e.angleDelta().y() / 120.0
            delta_px = int(notches * self.pixels_per_notch)
        sb = self.verticalScrollBar()
        sb.setValue(sb.value() - delta_px)
        e.accept()

# ----------------- Download Item -----------------
class DownloadItemWidget(QFrame):
    def __init__(self, task: DownloadTask):
        super().__init__()
        self.task = task
        self.setObjectName("DownloadItem")
        self._build_ui()

    def _build_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(14)

        # Thumbnail
        self.thumb = QLabel()
        self.thumb.setFixedSize(160, 90)
        self.thumb.setScaledContents(True)
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setPixmap(self.task.thumbnail or pm_placeholder(PNG1))

        # Text column
        col = QVBoxLayout()
        col.setSpacing(8)
        col.setAlignment(Qt.AlignTop)

        self.urlLbl = BodyLabel(self.task.url)
        self.urlLbl.setStyleSheet("font-size:15px; font-weight:700;")
        self.urlLbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.descLbl = CaptionLabel(self.task.description)
        self.descLbl.setWordWrap(True)

        metaRow = QHBoxLayout()
        metaRow.setSpacing(12)
        self.metaLbl = CaptionLabel(self.task.size_text)
        self.statusLbl = CaptionLabel("Đang chuẩn bị…")
        metaRow.addWidget(self.metaLbl)
        metaRow.addWidget(self.statusLbl)
        metaRow.addStretch(1)

        self.progress = ProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        col.addWidget(self.urlLbl)
        col.addWidget(self.descLbl)
        col.addLayout(metaRow)
        col.addWidget(self.progress)

        lay.addWidget(self.thumb, 0, Qt.AlignTop)
        lay.addLayout(col, 1)

    # Slots
    def setStatus(self, txt: str): self.statusLbl.setText(txt)
    def setProgress(self, v: int): self.progress.setValue(v)

# ----------------- Downloads Page -----------------
class DownloadsPage(QWidget):
    """Trang chính: ControlBar (nhập URL) + Danh sách tải."""
    addTaskRequested = Signal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(12)

        header = BodyLabel("Trình tải Media")
        header.setStyleSheet("font-size:18px; font-weight:700;")

        # Control bar
        self.controlBar = QFrame()
        self.controlBar.setObjectName("ControlBar")
        cb = QHBoxLayout(self.controlBar)
        cb.setContentsMargins(14, 12, 14, 12)
        cb.setSpacing(10)

        self.urlEdit = LineEdit(self)
        self.urlEdit.setPlaceholderText("Dán URL video/ảnh… (YouTube, TikTok, Facebook, …)")
        self.urlEdit.setMinimumWidth(420)
        self.urlEdit.returnPressed.connect(self._emit_add_task)

        self.addBtn = PrimaryPushButton(FIF.ADD, "Thêm vào danh sách")
        self.addBtn.clicked.connect(self._emit_add_task)

        cb.addWidget(self.urlEdit, 1)
        cb.addWidget(self.addBtn)

        # Empty state
        self.emptyBox = QFrame()
        eb_lay = QVBoxLayout(self.emptyBox)
        eb_lay.setContentsMargins(24, 48, 24, 48)
        eb_lay.setSpacing(8)
        emptyTitle = BodyLabel("Chưa có tác vụ tải")
        emptyTitle.setStyleSheet("font-size:16px; font-weight:700;")
        emptyHint = CaptionLabel("Dán một URL vào ô bên trên và nhấn “Thêm vào danh sách”.")
        eb_lay.addStretch(1)
        eb_lay.addWidget(emptyTitle, 0, Qt.AlignHCenter)
        eb_lay.addWidget(emptyHint, 0, Qt.AlignHCenter)
        eb_lay.addStretch(2)

        # List
        self.list = SmoothListWidget(pixels_per_notch=20, page_step=300)
        self.list.setVisible(False)

        v.addWidget(header)
        v.addWidget(self.controlBar)
        v.addWidget(self.emptyBox, 1)
        v.addWidget(self.list, 1)

    def _emit_add_task(self):
        url = self.urlEdit.text().strip()
        if not url or not URL_RE.search(url):
            InfoBar.error(
                title="URL không hợp lệ",
                content="Hãy nhập đường dẫn bắt đầu bằng http(s)://",
                position=InfoBarPosition.TOP_RIGHT, duration=2000, parent=self
            )
            return
        self.addTaskRequested.emit(url)
        self.urlEdit.clear()

    def addDownloadItem(self, widget: DownloadItemWidget):
        if self.emptyBox.isVisible():
            self.emptyBox.setVisible(False)
            self.list.setVisible(True)
        item = QListWidgetItem(self.list)
        item.setSizeHint(QSize(0, 120))
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)

# ----------------- Main Window -----------------
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        setTheme(Theme.AUTO)         # theo hệ thống; có thể đổi LIGHT/DARK
        setThemeColor(ACCENT)

        self.resize(1040, 680)
        self.setWindowTitle("Media Downloader")
        self.threadPool = QThreadPool.globalInstance()

        self.downloadsPage = DownloadsPage()
        self.downloadsPage.addTaskRequested.connect(self.add_task_from_url)

        self.initNavigation()
        apply_global_styles(self)

        # Seed vài task mẫu (tùy chọn)
        QTimer.singleShot(250, self._populate_fake)

    def initNavigation(self):
        self.addSubInterface(self.downloadsPage, FIF.DOWNLOAD, "Tải xuống",
                             position=NavigationItemPosition.TOP)

    def addSubInterface(self, widget, icon, text, position):
        self.navigationInterface.addItem(
            routeKey=text, icon=icon, text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
            position=position
        )
        self.stackedWidget.addWidget(widget)

    # -------------- Actions --------------
    def add_task_from_url(self, url: str):
        # Bạn có thể phân tích URL để tạo mô tả & kích thước sơ bộ
        desc = "Đang phân tích metadata…"
        size = "—"
        task = DownloadTask(url=url, description=desc, size_text=size, thumbnail=pm_placeholder())
        widget = DownloadItemWidget(task)
        self.downloadsPage.addDownloadItem(widget)

        # Khởi worker (demo). Thay FakeWorker bằng downloader thật.
        worker = FakeWorker(widget)
        worker.s.status.connect(widget.setStatus)
        worker.s.progress.connect(widget.setProgress)
        self.threadPool.start(worker)

    def _populate_fake(self):
        # samples = [
        #     "https://www.youtube.com/watch?v=USSmhFtxUOA",
        #     "https://www.youtube.com/watch?v=aaaa1111",
        #     "https://www.youtube.com/watch?v=bbbb2222",
        # ]
        # for url in samples:
        #     self.add_task_from_url(url)
        thumbs = [pm_from_source(PNG1), pm_from_source(PNG2), pm_from_source(PNG3)]
        fake_items = [
            ("https://www.youtube.com/watch?v=USSmhFtxUOA", "Funny cat compilation with HD clips", "12.3 MB", thumbs[0]),
            ("https://www.youtube.com/watch?v=aaaa1111", "Hướng dẫn nấu phở bò chuẩn vị", "54.1 MB", thumbs[1]),
            ("https://www.youtube.com/watch?v=bbbb2222", "AI Conference 2025 - Keynote", "108 MB", thumbs[2]),
        ]
        for url, desc, size, pm in fake_items:
            task = DownloadTask(url=url, description=desc, size_text=size, thumbnail=pm)
            widget = DownloadItemWidget(task)
            self.downloadsPage.addDownloadItem(widget)

            worker = FakeWorker(widget)
            worker.s.status.connect(widget.setStatus)
            worker.s.progress.connect(widget.setProgress)
            self.threadPool.start(worker)

# ----------------- Entrypoint -----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
