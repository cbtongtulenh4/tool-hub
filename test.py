# media_downloader_fluent.py
# PySide6 + qfluentwidgets — Fluent-style UI for a media downloader
# pip install PySide6 qfluentwidgets

from __future__ import annotations
import sys, os, time
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import (
    Qt, QSize, QUrl, Signal, QObject, QRunnable, QThreadPool, QTimer
)
from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QFileDialog, QHBoxLayout, QVBoxLayout,
    QFrame, QListWidget, QListWidgetItem, QStyle, QSpacerItem, QSizePolicy
)

# qfluentwidgets imports
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, NavigationInterface, setTheme, Theme,
    setThemeColor, InfoBar, InfoBarPosition, isDarkTheme,
    LineEdit, PrimaryPushButton, PushButton, ComboBox, HyperlinkLabel,
    ProgressBar, SwitchButton, ToolButton, BodyLabel, CaptionLabel,
    FluentIcon as FIF
)

# ------------------------------ Data Models ------------------------------

@dataclass
class DownloadTask:
    url: str
    title: str
    size_text: str = "—"
    thumbnail: Optional[QPixmap] = None
    dest_path: Optional[str] = None


class DownloadWorkerSignals(QObject):
    started = Signal()
    progress = Signal(int)       # 0..100
    status = Signal(str)
    finished = Signal(str, str)  # status, saved_path
    failed = Signal(str)         # error message


class DownloadWorker(QRunnable):
    """A demo worker that simulates downloading. Replace `run()` with real logic."""
    def __init__(self, task: DownloadTask, dest_dir: str):
        super().__init__()
        self.task = task
        self.dest_dir = dest_dir
        self.s = DownloadWorkerSignals()

    def run(self):
        self.s.started.emit()
        try:
            self.s.status.emit("Analyzing...")
            time.sleep(0.6)

            # --- Fake metadata extraction ---
            title = self.task.title or "Sample Video"
            size_mb = 12.8
            self.s.status.emit("Downloading...")
            # --- Simulated progress ---
            for i in range(101):
                time.sleep(0.02)  # simulate work
                self.s.progress.emit(i)

            # --- Fake save result ---
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
            file_name = f"{safe_title or 'video'}.mp4"
            saved_path = os.path.join(self.dest_dir, file_name)
            # touch file to visualize output (optional)
            try:
                with open(saved_path, "wb") as f:
                    f.write(b"")  # placeholder
            except Exception:
                pass

            self.s.status.emit("Completed")
            self.s.finished.emit("Completed", saved_path)
        except Exception as e:
            self.s.failed.emit(str(e))


# ------------------------------ UI Components ------------------------------

class DownloadItemWidget(QFrame):
    cancelRequested = Signal()
    openFolderRequested = Signal()
    openFileRequested = Signal()

    def __init__(self, task: DownloadTask):
        super().__init__()
        self.task = task
        self.setObjectName("DownloadItem")
        self.setProperty("transparent", True)
        self.setStyleSheet("""
        #DownloadItem {
            border-radius: 14px;
            background-color: rgba(120,120,120,0.05);
        }
        """)
        self._build_ui()

    def _build_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        # Thumbnail
        self.thumb = QLabel()
        self.thumb.setFixedSize(72, 48)
        self.thumb.setScaledContents(True)
        if self.task.thumbnail:
            self.thumb.setPixmap(self.task.thumbnail)
        else:
            # placeholder thumbnail
            pm = QPixmap(72, 48)
            pm.fill(Qt.gray if isDarkTheme() else Qt.lightGray)
            self.thumb.setPixmap(pm)

        # Title & meta
        textCol = QVBoxLayout()
        self.titleLbl = BodyLabel(self.task.title or "Untitled")
        self.metaLbl = CaptionLabel(self.task.size_text)
        self.statusLbl = CaptionLabel("Queued")
        textCol.addWidget(self.titleLbl)
        textCol.addWidget(self.metaLbl)
        textCol.addWidget(self.statusLbl)

        # Progress
        rightCol = QVBoxLayout()
        self.progress = ProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFixedWidth(240)

        btnRow = QHBoxLayout()
        self.openBtn = PushButton(FIF.FOLDER, "Mở thư mục")
        self.openFileBtn = PushButton(FIF.VIDEO, "Mở tệp")
        self.cancelBtn = PushButton(FIF.CLOSE, "Hủy")
        self.openBtn.clicked.connect(self.openFolderRequested.emit)
        self.openFileBtn.clicked.connect(self.openFileRequested.emit)
        self.cancelBtn.clicked.connect(self.cancelRequested.emit)

        btnRow.addWidget(self.openBtn)
        btnRow.addWidget(self.openFileBtn)
        btnRow.addWidget(self.cancelBtn)
        btnRow.addStretch(1)

        rightCol.addWidget(self.progress)
        rightCol.addLayout(btnRow)

        lay.addWidget(self.thumb)
        lay.addLayout(textCol, 1)
        lay.addLayout(rightCol)

    # Slots for worker signals
    def setStatus(self, txt: str):
        self.statusLbl.setText(txt)

    def setProgress(self, v: int):
        self.progress.setValue(v)

    def markDone(self, saved_path: str):
        self.setStatus("Hoàn tất")
        self.progress.setValue(100)
        self.task.dest_path = saved_path


class DownloadsPage(QWidget):
    """List page that hosts DownloadItemWidgets."""
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 12, 16, 12)
        v.setSpacing(10)

        header = QHBoxLayout()
        title = BodyLabel("Tải xuống")
        title.setStyleSheet("font-size:18px; font-weight:600;")
        self.countLbl = CaptionLabel("0 mục")
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.countLbl)

        self.list = QListWidget()
        self.list.setSpacing(10)
        self.list.setFrameShape(QFrame.NoFrame)
        self.list.setStyleSheet("QListWidget::item { margin: 0px; }")

        v.addLayout(header)
        v.addWidget(self.list, 1)

        self._count = 0

    def addDownloadItem(self, widget: DownloadItemWidget):
        item = QListWidgetItem(self.list)
        item.setSizeHint(QSize(0, 96))
        self.list.addItem(item)
        self.list.setItemWidget(item, widget)
        self._count += 1
        self.countLbl.setText(f"{self._count} mục")

    def showEmptyHint(self):
        InfoBar.info(
            title="Danh sách trống",
            content="Chưa có tác vụ tải nào. Hãy dán URL và bấm Tải.",
            orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT,
            duration=2000, parent=self
        )


class HomePage(QWidget):
    """Paste URL & Download."""
    requestDownload = Signal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(22)

        heading = BodyLabel("Tải media")
        heading.setStyleSheet("font-size:22px; font-weight:600;")

        sub = CaptionLabel("Dán URL video/ảnh từ YouTube, TikTok, Facebook, v.v.")
        sub.setWordWrap(True)

        row = QHBoxLayout()
        self.urlEdit = LineEdit(self)
        self.urlEdit.setPlaceholderText("https://…")
        self.urlEdit.setMinimumWidth(480)
        pasteBtn = PushButton(FIF.PASTE, "Dán")
        pasteBtn.clicked.connect(self._pasteFromClipboard)
        self.dlBtn = PrimaryPushButton(FIF.DOWNLOAD, "Tải")
        self.dlBtn.clicked.connect(lambda: self.requestDownload.emit(self.urlEdit.text().strip()))
        row.addWidget(self.urlEdit, 1)
        row.addWidget(pasteBtn)
        row.addWidget(self.dlBtn)

        hint = HyperlinkLabel("Lưu ý về bản quyền & điều khoản dịch vụ", self)
        hint.setUrl("https://www.youtube.com/t/terms")  # chỉ là ví dụ

        v.addWidget(heading)
        v.addWidget(sub)
        v.addLayout(row)
        v.addWidget(hint)
        v.addStretch(1)

    def _pasteFromClipboard(self):
        cb = QApplication.clipboard()
        self.urlEdit.setText(cb.text())


class SettingsPage(QWidget):
    saveDirChanged = Signal(str)

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        v = QVBoxLayout(self)
        v.setContentsMargins(28, 28, 28, 28)
        v.setSpacing(18)

        heading = BodyLabel("Cài đặt")
        heading.setStyleSheet("font-size:22px; font-weight:600;")

        # Save directory
        pathRow = QHBoxLayout()
        self.pathLabel = LineEdit(self)
        self.pathLabel.setReadOnly(True)
        self.chooseBtn = PushButton(FIF.FOLDER_ADD, "Chọn thư mục…")
        self.chooseBtn.clicked.connect(self._chooseFolder)
        pathRow.addWidget(self.pathLabel, 1)
        pathRow.addWidget(self.chooseBtn)

        # Format & quality (demo)
        fmtRow = QHBoxLayout()
        self.formatBox = ComboBox()
        self.formatBox.addItems(["MP4", "MP3", "WEBM"])
        self.qualityBox = ComboBox()
        self.qualityBox.addItems(["Best", "1080p", "720p", "480p", "Audio only"])
        fmtRow.addWidget(BodyLabel("Định dạng:"))
        fmtRow.addWidget(self.formatBox)
        fmtRow.addSpacing(16)
        fmtRow.addWidget(BodyLabel("Chất lượng:"))
        fmtRow.addWidget(self.qualityBox)
        fmtRow.addStretch(1)

        # Dark mode toggle
        themeRow = QHBoxLayout()
        themeRow.addWidget(BodyLabel("Dark mode"))
        self.darkSwitch = SwitchButton()
        self.darkSwitch.setChecked(isDarkTheme())
        self.darkSwitch.checkedChanged.connect(self._toggleTheme)
        themeRow.addWidget(self.darkSwitch)
        themeRow.addStretch(1)

        v.addWidget(heading)
        v.addLayout(pathRow)
        v.addLayout(fmtRow)
        v.addLayout(themeRow)
        v.addStretch(1)

        # Default save path
        from PySide6.QtCore import QStandardPaths
        default = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        self.pathLabel.setText(default)

    def _chooseFolder(self):
        d = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu", self.pathLabel.text())
        if d:
            self.pathLabel.setText(d)
            self.saveDirChanged.emit(d)

    def _toggleTheme(self, on: bool):
        setTheme(Theme.DARK if on else Theme.LIGHT)


# ------------------------------ Main Window ------------------------------

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        setTheme(Theme.DARK)                # feel free to switch to Theme.AUTO/Theme.LIGHT
        setThemeColor("#00B894")            # accent xanh ngọc dịu

        self.setWindowTitle("Media Downloader")
        self.resize(1040, 700)
        self.threadPool = QThreadPool.globalInstance()
        self.saveDir = SettingsPage().__class__  # just to satisfy type hints

        # Pages
        self.homePage = HomePage()
        self.downloadsPage = DownloadsPage()
        self.settingsPage = SettingsPage()
        self.saveDir = self.settingsPage.pathLabel.text()

        # Wire signals
        self.homePage.requestDownload.connect(self.handleDownload)
        self.settingsPage.saveDirChanged.connect(self._updateSaveDir)

        # Navigation
        self.initNavigation()
        self.setMicaEffectEnabled(True)

        # Quick actions (title bar)
        # self._initTitleBarActions()

    # def _initTitleBarActions(self):
    #     # Optional: add a “New Download” button on title bar
    #     btn = ToolButton(FIF.ADD)
    #     btn.setToolTip("Tải mới")
    #     btn.clicked.connect(lambda: self.stackedWidget.setCurrentWidget(self.homePage))
    #     self.addTitleBarWidget(btn, align=Qt.AlignRight)

    # def initNavigation(self):
    #     self.addSubInterface(self.homePage, FIF.HOME, "Trang chủ")
    #     self.addSubInterface(self.downloadsPage, FIF.DOWNLOAD, "Tải xuống",
    #                         position=NavigationItemPosition.BOTTOM)
    #     self.addSubInterface(self.settingsPage, FIF.SETTING, "Cài đặt",
    #                         position=NavigationItemPosition.BOTTOM)

    #     # Nút nhanh trên navigation
    #     self.navigationInterface.addWidget(
    #         routeKey="new", text="Tải mới", icon=FIF.ADD,
    #         onClick=lambda: self.stackedWidget.setCurrentWidget(self.homePage)
    #     )

    def initNavigation(self):
        self.addSubInterface(self.homePage, FIF.HOME, "Trang chủ")
        self.addSubInterface(self.downloadsPage, FIF.DOWNLOAD, "Tải xuống",
                             position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settingsPage, FIF.SETTING, "Cài đặt",
                             position=NavigationItemPosition.BOTTOM)

    # FluentWindow API wrappers
    def addSubInterface(self, widget: QWidget, icon: FIF, text: str, position=NavigationItemPosition.TOP):
        self.navigationInterface.addItem(
            routeKey=text, icon=icon, text=text, onClick=lambda: self.stackedWidget.setCurrentWidget(widget),
            position=position
        )
        self.stackedWidget.addWidget(widget)

    # -------------------------- Download Handling --------------------------

    def handleDownload(self, url: str):
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            InfoBar.error(
                title="URL không hợp lệ",
                content="Hãy dán một đường dẫn bắt đầu bằng http(s)://",
                position=InfoBarPosition.TOP_RIGHT, duration=2000, parent=self
            )
            return

        # Create task model
        task = DownloadTask(
            url=url,
            title="Đang phân tích…",
            size_text="—"
        )

        # Create UI item
        itemWidget = DownloadItemWidget(task)
        self.downloadsPage.addDownloadItem(itemWidget)
        self.stackedWidget.setCurrentWidget(self.downloadsPage)

        # Build worker (replace with real download logic)
        worker = DownloadWorker(task, dest_dir=self.saveDir)

        # Connect signals to UI
        worker.s.started.connect(lambda: itemWidget.setStatus("Chuẩn bị…"))
        worker.s.status.connect(itemWidget.setStatus)
        worker.s.progress.connect(itemWidget.setProgress)

        def on_finished(status: str, saved: str):
            itemWidget.markDone(saved)
            InfoBar.success(
                title="Tải xong",
                content=os.path.basename(saved) if saved else "Đã hoàn tất",
                position=InfoBarPosition.TOP_RIGHT, duration=2500, parent=self
            )

        def on_failed(msg: str):
            itemWidget.setStatus("Lỗi")
            InfoBar.error(
                title="Lỗi tải",
                content=msg,
                position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self
            )

        worker.s.finished.connect(on_finished)
        worker.s.failed.connect(on_failed)

        # Optional: cancel/open actions
        itemWidget.cancelRequested.connect(lambda: InfoBar.info(
            title="Hủy (demo)",
            content="Bạn có thể cài đặt huỷ thực sự bằng cờ kiểm soát trong worker.",
            position=InfoBarPosition.TOP_RIGHT, duration=1800, parent=self
        ))
        itemWidget.openFolderRequested.connect(lambda: self._revealInFolder(task.dest_path))
        itemWidget.openFileRequested.connect(lambda: self._openFile(task.dest_path))

        # Submit worker
        self.threadPool.start(worker)

    def _revealInFolder(self, path: Optional[str]):
        if not path:
            return
        folder = os.path.dirname(path)
        if sys.platform.startswith("win"):
            os.startfile(folder)
        elif sys.platform == "darwin":
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')

    def _openFile(self, path: Optional[str]):
        if not path:
            return
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')

    def _updateSaveDir(self, d: str):
        self.saveDir = d
        InfoBar.success(
            title="Đã cập nhật",
            content=f"Thư mục lưu: {d}",
            position=InfoBarPosition.TOP_RIGHT, duration=1800, parent=self
        )


# ------------------------------ Entrypoint ------------------------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Media Downloader")
    app.setOrganizationName("YourTeam")

    # Optional: better font rendering on Windows
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        getattr(Qt, "HighDpiScaleFactorRoundingPolicy", type("X",(object,),{})()).PassThrough
        if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy") else 0
    )

    w = MainWindow()
    w.show()
    sys.exit(app.exec())
