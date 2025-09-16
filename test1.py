# media_downloader_demo_images_progress.py
# pip install PySide6 qfluentwidgets
import sys, time, random, base64, os
from dataclasses import dataclass
from typing import Optional, Union

from PySide6.QtCore import Qt, QSize, QRunnable, QThreadPool, QObject, Signal, QTimer
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame,
    QListWidgetItem, QSizePolicy, QListWidget, QScrollBar, QAbstractItemView
)
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, setTheme, Theme, setThemeColor,
    BodyLabel, CaptionLabel, ProgressBar, FluentIcon as FIF, isDarkTheme
)

# ----------------- Theme helpers -----------------
ACCENT = "#2563EB"  # blue-600

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
    QListWidget {{ background: transparent; }}
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

# ----------------- Thumbnails nguồn (path hoặc base64) -----------------
PNG1 = r"C:\source_code\tool-hub\pexels-hazardos-1535244.jpg"
PNG2 = r"C:\source_code\tool-hub\pexels-hazardos-1535244.jpg"
PNG3 = r"C:\source_code\tool-hub\pexels-hazardos-1535244.jpg"

def pm_from_source(data: Union[str, bytes], w=160, h=90) -> QPixmap:
    pm = QPixmap()
    try:
        if isinstance(data, str) and os.path.exists(data):
            pm.load(data)
        elif isinstance(data, (bytes, bytearray)):
            raw = base64.b64decode(data)
            pm.loadFromData(raw)
    except Exception:
        pm = QPixmap()

    if pm.isNull():
        pm = QPixmap(w, h)
        pm.fill(QColor("#CBD5E1") if not isDarkTheme() else QColor("#475569"))
        return pm
    return pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

# ----------------- Model + Worker -----------------
@dataclass
class DownloadTask:
    title: str
    size_text: str
    thumbnail: Optional[QPixmap] = None

class FakeWorkerSignals(QObject):
    progress = Signal(int)
    status = Signal(str)

class FakeWorker(QRunnable):
    """Giả lập tải 0→100%"""
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.s = FakeWorkerSignals()
    def run(self):
        self.s.status.emit("Đang tải…")
        for i in range(101):
            time.sleep(0.02 + random.uniform(0, 0.008))
            self.s.progress.emit(i)
        self.s.status.emit("Hoàn tất")

# ----------------- List mượt & chậm hơn -----------------
class SmoothListWidget(QListWidget):
    """Giảm tốc độ cuộn theo pixel; hỗ trợ cả wheel và touchpad."""
    def __init__(self, parent=None, pixels_per_notch: int = 20, page_step: int = 280):
        super().__init__(parent)
        self.pixels_per_notch = pixels_per_notch
        # ✅ Dùng hằng số lớp QAbstractItemView
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

        sb: QScrollBar = self.verticalScrollBar()
        sb.setSingleStep(max(1, self.pixels_per_notch // 2))
        sb.setPageStep(page_step)

    def wheelEvent(self, e):
        # Touchpad: pixelDelta có giá trị mượt, ưu tiên dùng
        if not e.pixelDelta().isNull():
            delta_px = e.pixelDelta().y()
        else:
            # Chuột bánh xe: mỗi nấc = 120
            notches = e.angleDelta().y() / 120.0
            delta_px = int(notches * self.pixels_per_notch)

        sb = self.verticalScrollBar()
        sb.setValue(sb.value() - delta_px)
        e.accept()

# ----------------- UI Item -----------------
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

        self.thumb = QLabel()
        self.thumb.setFixedSize(160, 90)   # 16:9
        self.thumb.setScaledContents(True)
        if self.task.thumbnail:
            self.thumb.setPixmap(self.task.thumbnail)
        else:
            self.thumb.setPixmap(pm_from_source(PNG1))

        col = QVBoxLayout()
        col.setSpacing(8)

        self.titleLbl = BodyLabel(self.task.title)
        self.titleLbl.setStyleSheet("font-size:16px; font-weight:700;")
        metaRow = QHBoxLayout()
        self.metaLbl = CaptionLabel(self.task.size_text)
        self.statusLbl = CaptionLabel("Đang chuẩn bị…")
        metaRow.addWidget(self.metaLbl)
        metaRow.addSpacing(12)
        metaRow.addWidget(self.statusLbl)
        metaRow.addStretch(1)

        self.progress = ProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.progress.setMinimumWidth(520)

        col.addWidget(self.titleLbl)
        col.addLayout(metaRow)
        col.addWidget(self.progress)

        lay.addWidget(self.thumb)
        lay.addLayout(col, 1)

    def setStatus(self, txt: str): self.statusLbl.setText(txt)
    def setProgress(self, v: int): self.progress.setValue(v)

# ----------------- Downloads Page -----------------
class DownloadsPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(12)

        header = BodyLabel("Danh sách tải")
        header.setStyleSheet("font-size:18px; font-weight:700;")

        self.list = SmoothListWidget(pixels_per_notch=20, page_step=300)
        self.list.setSpacing(5)
        self.list.setFrameShape(QFrame.NoFrame)

        v.addWidget(header)
        v.addWidget(self.list, 1)

    def addDownloadItem(self, widget: DownloadItemWidget):
        item = QListWidgetItem(self.list)
        item.setSizeHint(QSize(0, 140))
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)

# ----------------- Main Window -----------------
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        setTheme(Theme.LIGHT)           # có thể đổi Theme.AUTO
        setThemeColor(ACCENT)
        self.resize(1040, 640)
        self.setWindowTitle("Media Downloader")

        self.threadPool = QThreadPool.globalInstance()

        self.downloadsPage = DownloadsPage()
        self.initNavigation()
        apply_global_styles(self)

        QTimer.singleShot(200, self._populate_fake)

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

    def _populate_fake(self):
        thumbs = [pm_from_source(PNG1), pm_from_source(PNG2), pm_from_source(PNG3)]
        fake_items = [
            ("Funny Cat Compilation 2025", "12.3 MB", thumbs[0]),
            ("How to Cook Pho Bo", "54.1 MB", thumbs[1]),
            ("AI Conference Keynote", "108 MB", thumbs[2]),
            ("Lo-fi Chill Beats Playlist", "89 MB", thumbs[0]),
            ("Travel Vlog: Đà Lạt", "1.2 GB", thumbs[1]),
            ("Hanoi Street Food Tour", "640 MB", thumbs[2]),
            ("Python Asyncio Tutorial", "420 MB", thumbs[0]),
            ("Nature Timelapse 4K", "2.1 GB", thumbs[1]),
            ("Game Trailer 2025", "950 MB", thumbs[2]),
        ]
        for t, s, pm in fake_items:
            task = DownloadTask(title=t, size_text=s, thumbnail=pm)
            widget = DownloadItemWidget(task)
            self.downloadsPage.addDownloadItem(widget)

            worker = FakeWorker(widget)
            worker.s.status.connect(widget.setStatus)
            worker.s.progress.connect(widget.setProgress)
            self.threadPool.start(worker)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
