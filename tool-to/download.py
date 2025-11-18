# media_downloader_api_demo.py
# PySide6 + qfluentwidgets (community)
# pip install PySide6 qfluentwidgets

import sys, time, random, base64, os, re
from dataclasses import dataclass
from typing import Optional, Union, List

from PySide6.QtCore import Qt, QSize, QRunnable, QThreadPool, QObject, Signal
from PySide6.QtGui import QPixmap, QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame,
    QListWidgetItem, QSizePolicy, QListWidget, QScrollBar, QAbstractItemView,
    QDialog, QCheckBox, QDialogButtonBox
)

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, setTheme, Theme, setThemeColor,
    BodyLabel, CaptionLabel, ProgressBar, FluentIcon as FIF, isDarkTheme,
    LineEdit, PrimaryPushButton, InfoBar, InfoBarPosition,
    IndeterminateProgressBar
)

from PySide6.QtWidgets import QScrollArea

MAX_VISIBLE_ITEMS = 4
CARD_HEIGHT = 120  # chiều cao thực tế 1 card ~120px → bạn có thể chỉnh lại nếu khác


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

    #LoadingCard {{
        border-radius: 14px;
        background-color: {c['bg_card']};
        border: 1px solid {c['border']};
    }}

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

    QPushButton, QToolButton {{
        cursor: pointinghand;
    }}
    """)

# ----------------- Helpers -----------------
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

THUMB_W, THUMB_H = 160, 90
THUMB_RADIUS = 10  # bo góc nhẹ


def pm_placeholder(w=THUMB_W, h=THUMB_H) -> QPixmap:
    pm = QPixmap(w, h)
    pm.fill(QColor("#CBD5E1") if not isDarkTheme() else QColor("#475569"))
    return pm


def round_pixmap(pix: QPixmap, radius: int = THUMB_RADIUS) -> QPixmap:
    if pix.isNull():
        return pm_placeholder()
    w, h = pix.width(), pix.height()
    out = QPixmap(w, h)
    out.fill(Qt.transparent)
    p = QPainter(out)
    p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform, True)
    path = QPainterPath()
    path.addRoundedRect(0, 0, w, h, radius, radius)
    p.setClipPath(path)
    p.drawPixmap(0, 0, pix)
    p.end()
    return out


def pm_from_source(data: Optional[Union[str, bytes]], w=THUMB_W, h=THUMB_H) -> QPixmap:
    """Demo với file path hoặc base64; hiện tại mainly dùng cho demo thumbnail local."""
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
    scaled = pm.scaled(w, h, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    x = (scaled.width() - w) // 2
    y = (scaled.height() - h) // 2
    cropped = scaled.copy(x, y, w, h)
    return round_pixmap(cropped, THUMB_RADIUS)

# ----------------- Model + Fake API -----------------
@dataclass
class DownloadTask:
    url: str
    description: str = "Đang phân tích…"
    size_text: str = "—"
    thumbnail: Optional[QPixmap] = None


@dataclass
class VideoOption:
    """Một lựa chọn video trả về từ API phân tích URL."""
    id: str
    title: str
    quality: str
    size_text: str
    download_url: str  # direct url/endpoint để tải


def fake_api_get_video_list(url: str) -> List[VideoOption]:
    """Fake API: nhận URL, trả về list các lựa chọn video."""
    qualities = ["360p", "480p", "720p", "1080p", "720p", "1080p", "720p", "1080p", "720p", "1080p"]
    base_id = abs(hash(url)) % 100000

    results: List[VideoOption] = []
    for i, q in enumerate(qualities):
        size_mb = 5 + i * 10
        results.append(
            VideoOption(
                id=f"{base_id}_{i}",
                title=f"Demo video from API ({q})",
                quality=q,
                size_text=f"{size_mb} MB",
                # GIẢ: sau này bạn thay bằng direct link thực từ API
                download_url=f"{url}?quality={q}"
            )
        )
    return results

# ----------------- Loading Dialog -----------------
class UrlLoadingDialog(QDialog):
    """Cửa sổ loading riêng, có nút Dừng."""
    cancelRequested = Signal()

    def __init__(self, parent=None, text: str = "Đang xử lý…"):
        super().__init__(parent)

        self.setModal(True)
        self.setWindowFlags(
            Qt.Dialog
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame(self)
        card.setObjectName("LoadingCard")
        cardLay = QVBoxLayout(card)
        cardLay.setContentsMargins(24, 20, 24, 20)
        cardLay.setSpacing(12)

        self.titleLbl = BodyLabel(text, card)
        self.titleLbl.setStyleSheet("font-size: 14px; font-weight: 600;")

        self.bar = IndeterminateProgressBar(card)

        # hintLbl = CaptionLabel("Vui lòng chờ trong giây lát…", card)
        # hintLbl.setWordWrap(True)

        btnRow = QHBoxLayout()
        btnRow.addStretch(1)
        self.cancelBtn = PrimaryPushButton("Dừng", card)
        self.cancelBtn.clicked.connect(self._on_cancel_clicked)
        btnRow.addWidget(self.cancelBtn)

        cardLay.addWidget(self.titleLbl, 0, Qt.AlignHCenter)
        cardLay.addWidget(self.bar)
        # cardLay.addWidget(hintLbl)
        cardLay.addLayout(btnRow)

        root.addWidget(card)

        self.resize(340, 150)

    def _on_cancel_clicked(self):
        self.cancelRequested.emit()
        self.hideLoading()

    def showLoading(self, text: Optional[str] = None):
        if text:
            self.titleLbl.setText(text)

        self.bar.start()

        if self.parent() is not None:
            parent_geom = self.parent().frameGeometry()
            self.move(
                parent_geom.center().x() - self.width() // 2,
                parent_geom.center().y() - self.height() // 2
            )

        self.show()

    def hideLoading(self):
        self.bar.stop()
        self.hide()

# ----------------- Workers -----------------
class FetchVideoListWorkerSignals(QObject):
    finished = Signal(list)   # list[VideoOption]
    error = Signal(str)
    canceled = Signal()


class FetchVideoListWorker(QRunnable):
    """Worker: gọi API (fake) để lấy danh sách video từ URL, có hỗ trợ cancel."""
    def __init__(self, url: str):
        super().__init__()
        self.url = url
        self.s = FetchVideoListWorkerSignals()
        self._canceled = False

    def cancel(self):
        self._canceled = True

    @property
    def is_canceled(self) -> bool:
        return self._canceled

    def run(self):
        try:
            # Giả lập delay mạng, chia nhỏ để check cancel
            for _ in range(12):
                if self._canceled:
                    self.s.canceled.emit()
                    return
                time.sleep(0.1)
                # time.sleep(5)

            if self._canceled:
                self.s.canceled.emit()
                return

            options = fake_api_get_video_list(self.url)

            if self._canceled:
                self.s.canceled.emit()
                return

            self.s.finished.emit(options)
        except Exception as e:
            if not self._canceled:
                self.s.error.emit(str(e))


class APIDownloadWorkerSignals(QObject):
    progress = Signal(int)
    status = Signal(str)
    error = Signal(str)
    finished = Signal()


class APIDownloadWorker(QRunnable):
    """
    Worker: giả lập gọi API tải 1 video.
    Sau này bạn chỉ cần thay phần logic trong run() bằng call API thật.
    """
    def __init__(self, task: DownloadTask):
        super().__init__()
        self.task = task
        self.s = APIDownloadWorkerSignals()

    def run(self):
        try:
            self.s.status.emit("Đang gọi API tải…")
            # Giả lập progress tải
            for i in range(101):
                time.sleep(0.03 + random.uniform(0, 0.01))
                self.s.progress.emit(i)
            self.s.status.emit("Hoàn tất")
            self.s.finished.emit()
        except Exception as e:
            self.s.error.emit(str(e))
            self.s.status.emit("Lỗi")

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
        self.thumb.setFixedSize(THUMB_W, THUMB_H)
        self.thumb.setScaledContents(True)
        self.thumb.setAlignment(Qt.AlignCenter)
        thumb_pm = self.task.thumbnail or pm_placeholder(THUMB_W, THUMB_H)
        self.thumb.setPixmap(thumb_pm)

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
    def setStatus(self, txt: str):
        self.statusLbl.setText(txt)

    def setProgress(self, v: int):
        self.progress.setValue(v)

# ----------------- Dialog chọn video -----------------
class VideoSelectionDialog(QDialog):
    def __init__(self, options: List[VideoOption], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chọn video để tải")
        self.resize(720, 480)
        self.options = options
        self.selected_options: List[VideoOption] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        titleLbl = BodyLabel("Chọn video / chất lượng cần tải")
        titleLbl.setStyleSheet("font-size:16px; font-weight:700;")
        layout.addWidget(titleLbl)

        # ----------------------------
        # 1) Tạo widget wrap chứa list
        # ----------------------------
        contentWidget = QFrame()
        contentLayout = QVBoxLayout(contentWidget)
        contentLayout.setContentsMargins(0, 0, 0, 0)
        contentLayout.setSpacing(8)

        self.checkboxes = []

        for opt in options:
            card = self._create_card(opt)
            contentLayout.addWidget(card)

        contentLayout.addStretch(1)

        # ----------------------------
        # 2) Scroll Area bọc content
        # ----------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(contentWidget)

        # Cuộn mượt
        scroll.verticalScrollBar().setSingleStep(20)

        # Giới hạn chiều cao: hiển thị tối đa 4 items
        visible_items = min(MAX_VISIBLE_ITEMS, len(options))
        scroll.setFixedHeight(visible_items * CARD_HEIGHT + 10)

        # add vào layout
        layout.addWidget(scroll)

        # Nút
        btnBox = QDialogButtonBox()
        btnBox.addButton("Download", QDialogButtonBox.AcceptRole)
        btnBox.addButton("Hủy", QDialogButtonBox.RejectRole)
        btnBox.accepted.connect(self._on_accept)
        btnBox.rejected.connect(self.reject)

        layout.addWidget(btnBox)

    # ----------------------------
    # Tạo 1 card video như cũ
    # ----------------------------
    def _create_card(self, opt: VideoOption) -> QFrame:
        card = QFrame()
        card.setObjectName("DownloadItem")
        card.setFixedHeight(CARD_HEIGHT)

        lay = QHBoxLayout(card)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        chk = QCheckBox()
        chk.setChecked(True)

        thumb = QLabel()
        thumb.setFixedSize(THUMB_W, THUMB_H)
        thumb.setPixmap(pm_placeholder())

        textCol = QVBoxLayout()
        title = BodyLabel(opt.title)
        title.setStyleSheet("font-size:15px; font-weight:700;")

        meta = CaptionLabel(f"{opt.quality} • {opt.size_text}")

        textCol.addWidget(title)
        textCol.addWidget(meta)

        lay.addWidget(chk, 0, Qt.AlignTop)
        lay.addWidget(thumb, 0, Qt.AlignTop)
        lay.addLayout(textCol)

        self._make_card_clickable(card, chk)
        self.checkboxes.append((chk, opt))

        return card

    def _make_card_clickable(self, card: QFrame, checkbox: QCheckBox):
        """Cho phép click bất kỳ vị trí nào trên card để toggle checkbox.

        Nếu click trực tiếp vào checkbox -> để Qt xử lý bình thường (không toggle 2 lần).
        """

        def mousePressEvent(ev):
            # Lấy vị trí click trong toạ độ global
            pos_global = ev.globalPosition().toPoint()
            # Chuyển về toạ độ local của checkbox
            pos_local = checkbox.mapFromGlobal(pos_global)

            # Nếu click đúng vào vùng checkbox → để Qt xử lý mặc định
            if checkbox.rect().contains(pos_local):
                return QFrame.mousePressEvent(card, ev)

            # Ngược lại, toggle checkbox
            checkbox.setChecked(not checkbox.isChecked())

            # Gọi event gốc (hợp lệ nhưng không cần làm gì nhiều)
            return QFrame.mousePressEvent(card, ev)

        card.mousePressEvent = mousePressEvent


    def _on_accept(self):
        chosen = []
        for chk, opt in self.checkboxes:
            if chk.isChecked():
                chosen.append(opt)

        if not chosen:
            InfoBar.warning(
                title="Chưa chọn video",
                content="Hãy chọn ít nhất 1 video để tải.",
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            return

        self.selected_options = chosen
        self.accept()


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

        # Đổi label & icon cho rõ hành vi: Load trước, Download sau
        self.addBtn = PrimaryPushButton(FIF.DOWNLOAD, "Load")
        self.addBtn.setCursor(Qt.PointingHandCursor)
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
        emptyHint = CaptionLabel("Dán URL và nhấn “Load” để phân tích, sau đó chọn video cần tải.")
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
        urls = user_url_parser(url)
        if not urls:
            InfoBar.error(
                title="URL không hợp lệ",
                content="Hãy nhập đường dẫn bắt đầu bằng http(s)://",
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )
            return

        # hiện tại chỉ xử lý URL đơn lẻ
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

# ----------------- URL parser -----------------
def user_url_parser(user_url: str):
    """
    Đơn giản: chỉ chấp nhận URL http/https.
    Sau này nếu muốn hỗ trợ file .txt chứa nhiều URL thì mở rộng thêm.
    """
    if not user_url or not URL_RE.search(user_url):
        return None
    return [user_url]

# ----------------- Main Window -----------------
class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        setTheme(Theme.AUTO)
        setThemeColor(ACCENT)

        self.resize(1040, 680)
        self.setWindowTitle("Media Downloader (API Demo)")
        self.threadPool = QThreadPool.globalInstance()

        self.downloadsPage = DownloadsPage()
        self.downloadsPage.addTaskRequested.connect(self.add_task_from_url)

        # dialog loading riêng cho việc load URL
        self.loadingDialog = UrlLoadingDialog(self, "Đang phân tích URL…")
        self.loadingDialog.cancelRequested.connect(self._on_loading_canceled)
        self.currentFetchWorker: Optional[FetchVideoListWorker] = None

        self.initNavigation()
        apply_global_styles(self)

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
    def start_download_task_from_option(self, option: VideoOption):
        """
        Từ 1 VideoOption tạo DownloadTask + DownloadItemWidget + APIDownloadWorker.
        """
        desc = f"{option.title} ({option.quality})"
        size = option.size_text or "—"

        thumb = pm_placeholder(THUMB_W, THUMB_H)
        task = DownloadTask(url=option.download_url, description=desc, size_text=size, thumbnail=thumb)
        widget = DownloadItemWidget(task)
        self.downloadsPage.addDownloadItem(widget)

        worker = APIDownloadWorker(task)
        worker.s.status.connect(widget.setStatus)
        worker.s.progress.connect(widget.setProgress)
        worker.s.error.connect(lambda msg, w=widget: self._on_download_error(w, msg))
        # worker.s.finished.connect(lambda: ...)  # nếu muốn làm gì thêm khi xong

        self.threadPool.start(worker)

    def add_task_from_url(self, url: str):
        """
        Bước 1: nhận URL từ UI
        Bước 2: chạy worker gọi API để lấy list video
        Bước 3: show dialog cho user chọn
        Bước 4: tạo các download task tương ứng
        """
        # bật loading dialog khi bắt đầu gọi API
        self.loadingDialog.showLoading("Đang phân tích URL…")

        worker = FetchVideoListWorker(url)
        self.currentFetchWorker = worker

        def on_finished(options: List[VideoOption]):
            # Nếu user đã cancel thì bỏ qua
            if worker.is_canceled:
                return

            self.loadingDialog.hideLoading()
            self.currentFetchWorker = None

            if not options:
                InfoBar.warning(
                    title="Không có video",
                    content="API không trả về video nào cho URL này.",
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=3000,
                    parent=self
                )
                return

            dlg = VideoSelectionDialog(options, parent=self)
            if dlg.exec() == QDialog.Accepted and dlg.selected_options:
                for opt in dlg.selected_options:
                    self.start_download_task_from_option(opt)

        def on_error(msg: str):
            if worker.is_canceled:
                return

            self.loadingDialog.hideLoading()
            self.currentFetchWorker = None

            InfoBar.error(
                title="Lỗi khi gọi API",
                content=msg,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self
            )

        def on_canceled():
            # worker tự báo là đã bị cancel
            self.loadingDialog.hideLoading()
            if self.currentFetchWorker is worker:
                self.currentFetchWorker = None
            InfoBar.info(
                title="Đã dừng",
                content="Đã dừng việc phân tích URL.",
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )

        worker.s.finished.connect(on_finished)
        worker.s.error.connect(on_error)
        worker.s.canceled.connect(on_canceled)

        self.threadPool.start(worker)

    def _on_loading_canceled(self):
        """User bấm Dừng trên dialog."""
        if self.currentFetchWorker is not None:
            self.currentFetchWorker.cancel()

    def _on_download_error(self, widget: DownloadItemWidget, msg: str):
        widget.setStatus("Lỗi tải")
        InfoBar.error(
            title="Lỗi tải",
            content=msg,
            position=InfoBarPosition.TOP_RIGHT,
            duration=4000,
            parent=self
        )

# ----------------- Entrypoint -----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
