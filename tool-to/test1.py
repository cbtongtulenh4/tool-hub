from __future__ import annotations

import sys
import random
from datetime import datetime
from typing import List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QTextEdit
)

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    SearchLineEdit, PrimaryPushButton, PushButton, InfoBar, InfoBarPosition,
    SpinBox, HyperlinkLabel, StrongBodyLabel, CaptionLabel,
    CardWidget, TitleLabel, SubtitleLabel, setTheme, Theme
)

# ===============================
# Helpers
# ===============================

def I(*names: str):
    """
    Icon an toàn: trả về FluentIcon đầu tiên tồn tại trong danh sách,
    nếu không có thì fallback về SETTING.
    """
    for n in names:
        if hasattr(FluentIcon, n):
            return getattr(FluentIcon, n)
    return FluentIcon.SETTING


def toast(parent: QWidget, text: str, success: bool = True):
    (InfoBar.success if success else InfoBar.info)(
        title='Thành công' if success else 'Thông báo',
        content=text,
        orient=Qt.Horizontal,
        isClosable=True,
        position=InfoBarPosition.TOP_RIGHT,
        duration=2500,
        parent=parent
    )


# ===============================
# Auto Comment Page
# ===============================

class AutoCommentPage(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("AutoCommentPage")  # ✅ BẮT BUỘC cho addSubInterface

        self._build_ui()
        self._bind()

        self.isRunning = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._do_work)

    # ---------- UI ----------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 16)
        root.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = TitleLabel("Bình luận tự động")
        header.addWidget(title, 1, Qt.AlignLeft)

        self.logout = HyperlinkLabel("Logout")
        self.logout.clicked.connect(lambda: toast(self, "Đã đăng xuất (demo)."))
        header.addWidget(self.logout, 0, Qt.AlignRight)
        root.addLayout(header)

        # ---- TOP: search + table ----
        topCard = CardWidget(self)
        topLay = QVBoxLayout(topCard)
        topLay.setContentsMargins(16, 12, 16, 16)
        topLay.setSpacing(8)

        self.search = SearchLineEdit(self)
        self.search.setPlaceholderText("Tìm kiếm Username, Name, UID…")
        topLay.addWidget(self.search)

        self.table = QTableWidget(0, 5, self)
        self.table.setHorizontalHeaderLabels(["STT", "Live", "Username", "Name", "UID"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        topLay.addWidget(self.table)

        self.selHint = CaptionLabel("0 dòng được chọn.")
        topLay.addWidget(self.selHint)

        root.addWidget(topCard)

        # Seed mẫu
        self._populate_table([
            ("Live", "haianhnguyen396800019", "Nguyễn Hải Anh", "89283498014")
        ])

        # ---- MIDDLE: config + content ----
        mid = QHBoxLayout()
        mid.setSpacing(12)

        # left config
        cfgCard = CardWidget(self)
        cfgLay = QVBoxLayout(cfgCard)
        cfgLay.setContentsMargins(16, 12, 16, 16)
        cfgLay.setSpacing(10)

        cfgLay.addWidget(SubtitleLabel("Thiết lập chạy"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        self.threads = SpinBox(); self.threads.setRange(1, 100); self.threads.setValue(1)
        self.totalCount = SpinBox(); self.totalCount.setRange(1, 100000); self.totalCount.setValue(50)
        self.delayMin = SpinBox(); self.delayMin.setRange(0, 3600); self.delayMin.setValue(10)
        self.delayMax = SpinBox(); self.delayMax.setRange(0, 3600); self.delayMax.setValue(15)

        grid.addWidget(StrongBodyLabel("Số luồng"), 0, 0); grid.addWidget(self.threads, 0, 1)
        grid.addWidget(StrongBodyLabel("Số lượng"), 0, 2); grid.addWidget(self.totalCount, 0, 3)
        grid.addWidget(StrongBodyLabel("Delay (giây)"), 1, 0); grid.addWidget(self.delayMin, 1, 1)
        grid.addWidget(StrongBodyLabel("đến"), 1, 2); grid.addWidget(self.delayMax, 1, 3)

        cfgLay.addLayout(grid)

        cfgLay.addWidget(SubtitleLabel("Danh sách link bài viết"))
        self.linkEdit = QTextEdit()
        self.linkEdit.setPlaceholderText(
            "Mỗi dòng một link…\nVD:\nhttps://www.youtube.com/watch?v=5xlNfz4hSBw\nhttps://youtu.be/UagJheg3wx0"
        )
        self.linkEdit.setFixedHeight(120)
        cfgLay.addWidget(self.linkEdit)

        btnRow = QHBoxLayout()
        self.btnStart = PrimaryPushButton("Bắt đầu", self, icon=I("PLAY", "PLAY_SOLID"))
        self.btnStop = PushButton("Dừng", self, icon=I("PAUSE", "STOP")); self.btnStop.setEnabled(False)
        btnRow.addWidget(self.btnStart); btnRow.addWidget(self.btnStop); btnRow.addStretch(1)
        cfgLay.addLayout(btnRow)

        mid.addWidget(cfgCard, 7)

        # right: content + media + history
        rightCard = CardWidget(self)
        rightLay = QVBoxLayout(rightCard)
        rightLay.setContentsMargins(16, 12, 16, 16)
        rightLay.setSpacing(10)

        rightLay.addWidget(SubtitleLabel("Nội dung bình luận"))
        self.contentEdit = QTextEdit()
        self.contentEdit.setPlaceholderText(
            "Hỗ trợ random theo format:\n<comment>Nội dung 1</comment>\n<comment>Nội dung 2</comment>"
        )
        self.contentEdit.setFixedHeight(100)
        rightLay.addWidget(self.contentEdit)

        aiRow = QHBoxLayout()
        self.btnAI = PushButton("Sử dụng AI", icon=I("ROBOT", "BRAIN", "SPARKLE"))
        self.btnAI.clicked.connect(self._demo_fill_ai)
        aiRow.addStretch(1); aiRow.addWidget(self.btnAI)
        rightLay.addLayout(aiRow)

        rightLay.addWidget(SubtitleLabel("Chọn ảnh / video"))
        pickRow = QHBoxLayout()
        self.btnPick = PushButton("Chọn tệp…", icon=I("PHOTO2", "PHOTO", "IMAGE"))
        self.btnPick.clicked.connect(self._pick_files)
        self.attachLabel = CaptionLabel("Chưa chọn tệp nào")
        pickRow.addWidget(self.btnPick); pickRow.addWidget(self.attachLabel, 1)
        rightLay.addLayout(pickRow)

        rightLay.addWidget(SubtitleLabel("Lịch sử"))
        self.logEdit = QTextEdit(); self.logEdit.setReadOnly(True); self.logEdit.setFixedHeight(140)
        rightLay.addWidget(self.logEdit)

        mid.addWidget(rightCard, 10)
        root.addLayout(mid)

    def _bind(self):
        self.search.textChanged.connect(self._filter_table)
        self.table.itemSelectionChanged.connect(self._update_sel_hint)
        self.btnStart.clicked.connect(self.start_run)
        self.btnStop.clicked.connect(self.stop_run)

    # ---------- Data & Behaviors ----------
    def _populate_table(self, rows: List[tuple[str, str, str, str]]):
        self.table.setRowCount(0)
        for i, (live, username, name, uid) in enumerate(rows, start=1):
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(i)))
            self.table.setItem(r, 1, QTableWidgetItem(live))
            self.table.setItem(r, 2, QTableWidgetItem(username))
            self.table.setItem(r, 3, QTableWidgetItem(name))
            self.table.setItem(r, 4, QTableWidgetItem(uid))
        self._update_sel_hint()

    def _update_sel_hint(self):
        model = self.table.selectionModel()
        count = len(model.selectedRows()) if model else 0
        self.selHint.setText(f"{count} dòng được chọn.")

    def _filter_table(self, text: str):
        t = text.lower().strip()
        for r in range(self.table.rowCount()):
            visible = any(
                t in (self.table.item(r, c).text().lower() if self.table.item(r, c) else "")
                for c in range(self.table.columnCount())
            ) if t else True
            self.table.setRowHidden(r, not visible)

    def _pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh/video", "",
            "Media (*.png *.jpg *.jpeg *.mp4 *.mov);;Tất cả (*)"
        )
        if not files:
            return
        self.attachLabel.setText(f"Đã chọn {len(files)} tệp")
        toast(self, f"Đã chọn {len(files)} tệp đính kèm.")

    def _demo_fill_ai(self):
        pool = [
            "Truy cập link này nhé: https://www.youtube.com/watch?v=5xlNfz4hSBw",
            "Bạn chụp gửi lại mình nhé.",
            "Cảm ơn bạn đã quan tâm!",
            "Video này hay thật đấy!",
        ]
        blocks = "\n".join(f"<comment>{s}</comment>" for s in random.sample(pool, k=min(3, len(pool))))
        self.contentEdit.setPlainText(blocks)
        toast(self, "Đã sinh nội dung mẫu bằng AI (demo).")

    def _next_comment(self) -> str:
        """
        Lấy ngẫu nhiên một block <comment>...</comment> nếu có.
        Nếu không có tag, dùng toàn bộ văn bản.
        """
        text = self.contentEdit.toPlainText().strip()
        if not text:
            return ""
        parts = []
        start_tag, end_tag = "<comment>", "</comment>"
        if "<comment" in text:
            tmp = text.replace("<comment/>", "").split(start_tag)
            for p in tmp:
                if end_tag in p:
                    parts.append(p.split(end_tag)[0].strip())
        return random.choice(parts) if parts else text

    def start_run(self):
        if self.isRunning:
            return
        links = [ln.strip() for ln in self.linkEdit.toPlainText().splitlines() if ln.strip()]
        if not links:
            toast(self, "Vui lòng nhập tối thiểu 1 link.", success=False); return
        if self.delayMax.value() < self.delayMin.value():
            toast(self, "Delay tối đa phải ≥ tối thiểu.", success=False); return
        if not self._next_comment():
            toast(self, "Vui lòng nhập nội dung bình luận.", success=False); return

        self.isRunning = True
        self.btnStart.setEnabled(False); self.btnStop.setEnabled(True)
        self._append_log("BẮT ĐẦU phiên chạy…")
        self.timer.start(1000)  # demo mỗi 1 giây thực hiện 1 tác vụ

    def stop_run(self):
        if not self.isRunning:
            return
        self.timer.stop()
        self.isRunning = False
        self.btnStart.setEnabled(True); self.btnStop.setEnabled(False)
        self._append_log("ĐÃ DỪNG phiên chạy.")

    def _do_work(self):
        links = [ln.strip() for ln in self.linkEdit.toPlainText().splitlines() if ln.strip()]
        if not links:
            self.stop_run(); return
        link = random.choice(links)
        cmt_full = self._next_comment()
        cmt = (cmt_full[:60] + "…") if len(cmt_full) > 60 else cmt_full
        now = datetime.now().strftime("%H:%M:%S %d-%m-%Y")
        user = self.table.item(0, 2).text() if self.table.rowCount() > 0 else "unknown"
        self._append_log(f"[{now}][{user}][OK] Đã bình luận: \"{cmt}\" vào {link}")

        # demo: có xác suất dừng lại
        if random.random() < 0.1:
            self.stop_run()

    def _append_log(self, text: str):
        self.logEdit.append(text)


# ===============================
# Main Window
# ===============================

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        setTheme(Theme.AUTO)        # Tự dark/light theo hệ điều hành
        self.setWindowTitle("AFlash")
        self.resize(1200, 740)

        # navigationInterface là THUỘC TÍNH
        self.nav = self.navigationInterface

        self._init_navigation()

        # Trang mặc định
        self.nav.setCurrentItem(self.autoCommentPage)

    def _init_navigation(self):
        # Helper tạo trang placeholder kèm objectName ✅
        def page(obj_name: str, title: str, desc: str) -> QWidget:
            w = QWidget(self)
            w.setObjectName(obj_name)
            lay = QVBoxLayout(w)
            lay.setContentsMargins(24, 24, 24, 24)
            lay.addWidget(TitleLabel(title))
            lay.addWidget(SubtitleLabel(desc))
            lay.addStretch(1)
            return w

        # Tạo trang
        self.dashboardPage   = page("DashboardPage",   "Dashboard", "Tổng quan")
        self.accountPage     = page("AccountPage",     "Quản lí tài khoản", "Quản lý đăng nhập, trạng thái account…")
        self.postPage        = page("PostPage",        "Quản lí bài viết", "Danh sách bài, lọc/sort, gắn tag…")
        self.schedulePage    = page("SchedulePage",    "Quản lí lịch trình", "Lập lịch chạy tác vụ.")
        self.proxyPage       = page("ProxyPage",       "Quản lí proxy", "Thiết lập proxy / rotating proxy.")
        self.aiSettingPage   = page("AISettingPage",   "AI Setting", "Cấu hình model, API key, prompt template.")
        self.autoPostPage    = page("AutoPostPage",    "Đăng bài tự động", "Soạn nội dung & đăng hàng loạt.")
        self.autoFollowPage  = page("AutoFollowPage",  "Theo dõi tự động", "Theo dõi/subscribe tự động.")
        self.autoCommentPage = AutoCommentPage(self)   # đã setObjectName ở class
        self.autoRepostPage  = page("AutoRepostPage",  "Đăng lại tự động", "Repost/Share tự động.")
        self.autoLikePage    = page("AutoLikePage",    "Thích bài tự động", "Like reaction tự động.")
        self.autoScrapePage  = page("AutoScrapePage",  "Lấy thông tin tự động", "Crawler / collector.")
        self.versionPage     = page("VersionPage",     "Phiên bản", "AFlash v1.0.1")

        # Group: Dashboard
        self.addSubInterface(self.dashboardPage, I("HOME"), "Dashboard", NavigationItemPosition.TOP)

        # Group: Manager
        self.nav.addSeparator(NavigationItemPosition.TOP)
        self.addSubInterface(self.accountPage,    I("PEOPLE", "CONTACT"), "Quản lí tài khoản", NavigationItemPosition.TOP)
        self.addSubInterface(self.postPage,       I("DOCUMENT", "FILE"),  "Quản lí bài viết", NavigationItemPosition.TOP)
        self.addSubInterface(self.schedulePage,   I("DATE_TIME", "CALENDAR"), "Quản lí lịch trình", NavigationItemPosition.TOP)
        self.addSubInterface(self.proxyPage,      I("GLOBE", "WORLD"),    "Quản lí proxy", NavigationItemPosition.TOP)

        # Group: AI Agent
        self.nav.addSeparator(NavigationItemPosition.TOP)
        self.addSubInterface(self.aiSettingPage,  I("ROBOT", "BRAIN", "SPARKLE"), "AI Setting", NavigationItemPosition.TOP)

        # Group: Automatic
        self.nav.addSeparator(NavigationItemPosition.TOP)
        self.addSubInterface(self.autoPostPage,    I("SEND", "MAIL"),     "Đăng bài tự động", NavigationItemPosition.TOP)
        self.addSubInterface(self.autoFollowPage,  I("FOLLOW", "CONTACT"),"Theo dõi tự động", NavigationItemPosition.TOP)
        self.addSubInterface(self.autoCommentPage, I("COMMENT", "CHAT"),  "Bình luận tự động", NavigationItemPosition.TOP)
        self.addSubInterface(self.autoRepostPage,  I("SHARE", "SEND"),    "Đăng lại tự động", NavigationItemPosition.TOP)
        self.addSubInterface(self.autoLikePage,    I("LIKE", "HEART"),    "Thích bài tự động", NavigationItemPosition.TOP)
        self.addSubInterface(self.autoScrapePage,  I("BRANCH", "DOWNLOAD"), "Lấy thông tin tự động", NavigationItemPosition.TOP)

        # Footer: version
        self.nav.addSeparator(NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.versionPage, I("INFO", "QUESTION"), "Version: v1.0.1", NavigationItemPosition.BOTTOM)


# ===============================
# Entrypoint
# ===============================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("AFlash")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
