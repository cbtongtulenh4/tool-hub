# -*- coding: utf-8 -*-
# UI: PySide6 + qfluentwidgets (no backend, fake data)
# pip install PySide6 qfluentwidgets

from PySide6.QtCore import Qt, QRect, QAbstractTableModel, QModelIndex, QSize, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QHBoxLayout, QVBoxLayout, QGridLayout,
    QSplitter, QFrame, QLabel, QTableView, QHeaderView,
    QStyledItemDelegate, QStyleOptionButton, QStyle, QStyleOptionViewItem,
    QAbstractItemView, QToolButton, QSpinBox, QTextEdit, QMenu, QFileDialog, QPushButton
)

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, FluentIcon as FIF, setTheme, Theme,
    LineEdit, PrimaryPushButton, PushButton, InfoBar, InfoBarPosition, setThemeColor
)

# -------------------------------
# Helpers & custom components
# -------------------------------

class CheckableTableModel(QAbstractTableModel):
    """Simple model with checkable first column and text data for the rest."""
    def __init__(self, headers, rows, parent=None):
        super().__init__(parent)
        self.headers = headers
        # rows: list of [checked(bool), STT, Live, Username, Name, UID]
        self.rows = [[bool(r[0])] + r[1:] for r in rows]

    def rowCount(self, parent=QModelIndex()):
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()

        if col == 0:
            if role == Qt.CheckStateRole:
                return Qt.Checked if self.rows[row][0] else Qt.Unchecked
            if role in (Qt.DisplayRole, Qt.EditRole):
                return ""
            return None

        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.rows[row][col]

        return None

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        row, col = index.row(), index.column()

        if col == 0 and role == Qt.CheckStateRole:
            self.rows[row][0] = (value == Qt.Checked)
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            return True

        if role == Qt.EditRole and col > 0:
            self.rows[row][col] = value
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
            return True
        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.headers[section]
        return section + 1

    def set_all_checked(self, checked: bool):
        for r in range(len(self.rows)):
            self.rows[r][0] = checked
        topLeft = self.index(0, 0)
        bottomRight = self.index(self.rowCount()-1, 0)
        self.dataChanged.emit(topLeft, bottomRight, [Qt.CheckStateRole])

    def count_checked(self):
        return sum(1 for r in self.rows if r[0])

class HeaderSelectAll(QHeaderView):
    """Tri-state checkbox in header section 0 (select all / none / partial)."""
    stateChanged = Signal(Qt.CheckState)

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self._checkState = Qt.Unchecked
        self._rect = QRect()
        self.setDefaultAlignment(Qt.AlignVCenter)

    def paintSection(self, painter, rect, logicalIndex):
        super().paintSection(painter, rect, logicalIndex)
        if logicalIndex == 0:
            opt = QStyleOptionButton()
            opt.rect = self._checkboxRect(rect)
            opt.state = QStyle.State_Enabled | QStyle.State_Active
            if self._checkState == Qt.Checked:
                opt.state |= QStyle.State_On
            elif self._checkState == Qt.PartiallyChecked:
                opt.state |= QStyle.State_NoChange
            else:
                opt.state |= QStyle.State_Off
            self.style().drawControl(QStyle.CE_CheckBox, opt, painter)

    def mousePressEvent(self, event):
        if self._rect.contains(event.pos()):
            next_state = {
                Qt.Unchecked: Qt.Checked,
                Qt.Checked: Qt.Unchecked,
                Qt.PartiallyChecked: Qt.Checked
            }[self._checkState]
            self.setCheckState(next_state)
            self.stateChanged.emit(next_state)
            event.accept()
        else:
            super().mousePressEvent(event)

    def _checkboxRect(self, rect: QRect):
        size = 18
        x = rect.x() + 8
        y = rect.y() + (rect.height() - size) // 2
        self._rect = QRect(x, y, size, size)
        return self._rect

    def setCheckState(self, state: Qt.CheckState):
        self._checkState = state
        self.viewport().update()

class CheckBoxDelegate(QStyledItemDelegate):
    """Delegate to draw checkbox centered in the first column cells."""
    def paint(self, painter, option: QStyleOptionViewItem, index: QModelIndex):
        if index.column() == 0:
            opt = QStyleOptionButton()
            opt.state = QStyle.State_Enabled | QStyle.State_Active
            st = index.data(Qt.CheckStateRole)
            opt.state |= QStyle.State_On if st == Qt.Checked else QStyle.State_Off
            size = 18
            opt.rect = QRect(
                option.rect.x() + (option.rect.width() - size) // 2,
                option.rect.y() + (option.rect.height() - size) // 2,
                size, size
            )
            QApplication.style().drawControl(QStyle.CE_CheckBox, opt, painter)
        else:
            super().paint(painter, option, index)

    def editorEvent(self, event, model, option, index):
        if index.column() == 0 and event.type() == event.MouseButtonRelease:
            current = index.data(Qt.CheckStateRole)
            model.setData(index, Qt.Unchecked if current == Qt.Checked else Qt.Checked, Qt.CheckStateRole)
            return True
        return super().editorEvent(event, model, option, index)

# -------------------------------
# Pages
# -------------------------------

class AutoCommentPage(QWidget):
    """Trang 'Bình luận tự động' – bố cục sạch, theo grid 8px, fake data."""
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # --- Bảng danh sách tài khoản/đối tượng ---
        tableWrap = QFrame()
        tLay = QVBoxLayout(tableWrap)
        tLay.setContentsMargins(0, 0, 0, 0)
        tLay.setSpacing(8)

        hdr = QLabel("Danh sách mục tiêu")
        hdr.setProperty("cssClass", "h6")
        tLay.addWidget(hdr)

        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setItemDelegateForColumn(0, CheckBoxDelegate(self.table))
        self.table.setShowGrid(False)

        headers = ["", "STT", "Live", "Username", "Name", "UID"]
        rows = [
            [True, 1, "Live", "haianhnguyen396800019", "Nguyễn Hải Anh", "89283498014"],
            [False, 2, "Live", "maihoa_2103", "Mai Hoa", "1029384756"],
            [True, 3, "Live", "user_alpha", "User Alpha", "5566778899"],
        ]
        self.model = CheckableTableModel(headers, rows, self)
        self.table.setModel(self.model)

        header = HeaderSelectAll(Qt.Horizontal, self.table)
        self.table.setHorizontalHeader(header)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        def update_header_state():
            total = self.model.rowCount()
            checked = self.model.count_checked()
            if checked == 0:
                header.setCheckState(Qt.Unchecked)
            elif checked == total:
                header.setCheckState(Qt.Checked)
            else:
                header.setCheckState(Qt.PartiallyChecked)
        update_header_state()

        header.stateChanged.connect(lambda st: self.model.set_all_checked(st == Qt.Checked))
        self.model.dataChanged.connect(lambda *_: update_header_state())

        tLay.addWidget(self.table)
        selectedHint = QLabel(f"{self.model.count_checked()} trong {self.model.rowCount()} mục đã chọn.")
        tLay.addWidget(selectedHint)

        # --- Khu cấu hình & nội dung ---
        mid = QFrame()
        midLay = QGridLayout(mid)
        midLay.setContentsMargins(0, 0, 0, 0)
        midLay.setHorizontalSpacing(16)
        midLay.setVerticalSpacing(12)

        # Cột trái
        leftCard = QFrame()
        leftLay = QVBoxLayout(leftCard)
        leftLay.setContentsMargins(12, 12, 12, 12)
        leftLay.setSpacing(8)

        titleMode = QLabel("Chọn chế độ bình luận")
        titleMode.setProperty("cssClass", "h6")
        leftLay.addWidget(titleMode)

        modeLbl = QLabel("Bài viết")
        modeLbl.setProperty("cssClass", "subtitle2")
        leftLay.addWidget(modeLbl)

        modeInfo = QLabel("Bạn đang chọn chế độ bài viết • Enter xuống dòng cho mỗi link")
        leftLay.addWidget(modeInfo)

        self.linksEdit = QTextEdit()
        self.linksEdit.setPlaceholderText("https://youtu.be/...\nhttps://www.youtube.com/watch?v=...")
        self.linksEdit.setFixedHeight(120)
        self.linksEdit.setText("https://www.youtube.com/watch?v=5xlNfz4hSBw\nhttps://youtu.be/UagJheg3wx0?si=pSJedjtCRWx1VqH_")
        leftLay.addWidget(self.linksEdit)

        row1 = QHBoxLayout()
        row1.setSpacing(12)
        row1.addWidget(QLabel("Số luồng"))
        self.threadSpin = QSpinBox()
        self.threadSpin.setRange(1, 64)
        self.threadSpin.setValue(1)
        self.threadSpin.setFixedWidth(72)
        row1.addWidget(self.threadSpin)

        row1.addSpacing(8)
        row1.addWidget(QLabel("Số lượng"))
        self.amountSpin = QSpinBox()
        self.amountSpin.setRange(1, 10000)
        self.amountSpin.setValue(50)
        self.amountSpin.setFixedWidth(88)
        row1.addWidget(self.amountSpin)
        row1.addStretch(1)
        leftLay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)
        row2.addWidget(QLabel("Delay"))
        self.delayMin = QSpinBox()
        self.delayMin.setRange(0, 3600)
        self.delayMin.setValue(10)
        self.delayMin.setFixedWidth(72)
        row2.addWidget(self.delayMin)
        row2.addWidget(QLabel("đến"))
        self.delayMax = QSpinBox()
        self.delayMax.setRange(0, 3600)
        self.delayMax.setValue(15)
        self.delayMax.setFixedWidth(72)
        row2.addWidget(self.delayMax)
        row2.addWidget(QLabel("giây"))
        row2.addStretch(1)
        leftLay.addLayout(row2)

        btnRow = QHBoxLayout()
        self.startBtn = PrimaryPushButton("Bắt đầu", icon=FIF.PLAY)
        self.stopBtn = PushButton("Dừng", icon=FIF.PAUSE)   # ← đổi từ STOP sang PAUSE
        self.scheduleLabel = QLabel("Đặt lịch")
        btnRow.addWidget(self.startBtn)
        btnRow.addWidget(self.stopBtn)
        btnRow.addSpacing(8)
        btnRow.addWidget(self.scheduleLabel)
        btnRow.addStretch(1)
        leftLay.addLayout(btnRow)

        # Cột phải
        rightCard = QFrame()
        rightLay = QVBoxLayout(rightCard)
        rightLay.setContentsMargins(12, 12, 12, 12)
        rightLay.setSpacing(12)

        cLabel = QLabel("Nội dung")
        cLabel.setProperty("cssClass", "subtitle2")
        rightLay.addWidget(cLabel)

        self.contentEdit = QTextEdit()
        self.contentEdit.setPlaceholderText("<comment>Nội dung bình luận</comment>\n<comment>Nội dung khác</comment>")
        self.contentEdit.setFixedHeight(90)
        self.contentEdit.setText("<comment>Truy cập link này nhé: https://www.youtube.com/watch?v=5xlNfz4hSBw</comment>\n<comment>Bạn chụp gửi lại mình nhé.</comment>")
        rightLay.addWidget(self.contentEdit)

        aiRow = QHBoxLayout()
        self.aiBtn = PushButton("Sử dụng AI", icon=FIF.ROBOT)
        aiRow.addStretch(1)
        aiRow.addWidget(self.aiBtn)
        rightLay.addLayout(aiRow)

        hint = QLabel("Random nội dung theo format: <comment>nội dung bình luận</comment>")
        rightLay.addWidget(hint)

        mediaLbl = QLabel("Chọn ảnh/video")
        mediaLbl.setProperty("cssClass", "subtitle2")
        rightLay.addWidget(mediaLbl)

        self.mediaDrop = DropArea("Kéo thả, hoặc nhấp để chọn file hình ảnh hoặc video")
        self.mediaDrop.clicked.connect(self.pick_files)
        rightLay.addWidget(self.mediaDrop)

        historyLbl = QLabel("Lịch sử")
        historyLbl.setProperty("cssClass", "subtitle2")
        rightLay.addWidget(historyLbl)

        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setFixedHeight(90)
        self.history.setText(
            "[14:31:44 09-10-2025][haianhnguyen396800019][OK] Trả lời bình luận thành công link comment <>\n"
            "[14:40:31 09-10-2025][haianhnguyen396800019][OK] Trả lời bình luận thành công link comment <>\n"
            "[14:43:12 09-10-2025][haianhnguyen396800019][OK] Trả lời bình luận thành công link comment <>\n"
            "[14:50:04 09-10-2025][haianhnguyen396800019][OK] Trả lời bình luận thành công link comment <>"
        )
        rightLay.addWidget(self.history)

        midLay.addWidget(leftCard, 0, 0, 1, 6)
        midLay.addWidget(rightCard, 0, 6, 1, 6)

        root.addWidget(tableWrap)
        root.addWidget(mid)

        self.startBtn.clicked.connect(self._start)
        self.stopBtn.clicked.connect(self._stop)

    def _start(self):
        InfoBar.success(
            title="Đã bắt đầu",
            content=f"Chạy {self.threadSpin.value()} luồng • {self.amountSpin.value()} lần • delay {self.delayMin.value()}–{self.delayMax.value()} giây",
            orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=3000, parent=self
        )

    def _stop(self):
        InfoBar.warning(
            title="Đã dừng",
            content="Tác vụ hiện tại đã dừng.",
            orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2500, parent=self
        )

    def pick_files(self):
        QFileDialog.getOpenFileNames(self, "Chọn ảnh/video", "", "Media (*.png *.jpg *.jpeg *.bmp *.gif *.mp4 *.mov)")

class DropArea(QFrame):
    """Ô kéo-thả đơn giản (fake UX) + click để chọn file."""
    clicked = Signal()
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("DropArea")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 16, 12, 16)
        lay.setSpacing(0)
        self.label = QLabel(text)
        self.label.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.label)
        self.setProperty("cssClass", "card")
        self.setStyleSheet("""
        QFrame#DropArea {
            border: 1px dashed rgba(120,120,120,0.6);
            border-radius: 12px;
        }
        QFrame#DropArea:hover {
            border: 1px dashed rgba(60,130,250,0.9);
            background: rgba(60,130,250,0.05);
        }
        """)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()

# -------------------------------
# Main window with Navigation + Topbar
# -------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AFlash • Admin")
        self.resize(1280, 800)

        # ánh xạ routeKey → tiêu đề hiển thị
        self.ROUTE_TITLES = {
            "dashboard": "Dashboard",
            "acc": "Quản lí tài khoản",
            "post": "Quản lí bài viết",
            "calendar": "Quản lí lịch trình",
            "proxy": "Quản lí proxy",
            "ai": "AI Setting",
            "auto-post": "Đăng bài tự động",
            "auto-follow": "Theo dõi tự động",
            "auto-comment": "Bình luận tự động",
            "auto-repost": "Đăng lại tự động",
            "auto-like": "Thích bài tự động",
            "auto-scan": "Lấy thông tin tự động",
            "about": "Version: v1.0.1",
        }

        # Theme
        setTheme(Theme.AUTO)
        setThemeColor("#3B82F6")

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        self.setCentralWidget(splitter)

        # Sidebar
        self.nav = NavigationInterface(splitter, showMenuButton=True, showReturnButton=False)
        self.nav.setMaximumWidth(320)
        self.nav.setMinimumWidth(72)
        self.nav.setExpandWidth(240)

        # TOP group
        self.nav.addItem("dashboard", icon=FIF.HOME, text=self.ROUTE_TITLES["dashboard"],
                         onClick=lambda rk="dashboard": self.stack_set(rk), position=NavigationItemPosition.TOP)

        self.nav.addSeparator()
        self.nav.addItem("acc", icon=FIF.PEOPLE, text=self.ROUTE_TITLES["acc"],
                         onClick=lambda rk="acc": self.stack_set(rk), position=NavigationItemPosition.TOP)
        self.nav.addItem("post", icon=FIF.DOCUMENT, text=self.ROUTE_TITLES["post"],
                         onClick=lambda rk="post": self.stack_set(rk), position=NavigationItemPosition.TOP)
        self.nav.addItem("calendar", icon=FIF.CALENDAR, text=self.ROUTE_TITLES["calendar"],
                         onClick=lambda rk="calendar": self.stack_set(rk), position=NavigationItemPosition.TOP)

        self.nav.addSeparator()
        self.nav.addItem("proxy", icon=FIF.GLOBE, text=self.ROUTE_TITLES["proxy"],
                         onClick=lambda rk="proxy": self.stack_set(rk), position=NavigationItemPosition.TOP)
        self.nav.addItem("ai", icon=FIF.ROBOT, text=self.ROUTE_TITLES["ai"],
                         onClick=lambda rk="ai": self.stack_set(rk), position=NavigationItemPosition.TOP)

        self.nav.addSeparator()
        self.nav.addItem("auto-post", icon=FIF.SEND, text=self.ROUTE_TITLES["auto-post"],
                         onClick=lambda rk="auto-post": self.stack_set(rk), position=NavigationItemPosition.TOP)
        self.nav.addItem("auto-follow", icon=FIF.PEOPLE, text=self.ROUTE_TITLES["auto-follow"],
                         onClick=lambda rk="auto-follow": self.stack_set(rk), position=NavigationItemPosition.TOP)
        self.nav.addItem("auto-comment", icon=FIF.MESSAGE, text=self.ROUTE_TITLES["auto-comment"],
                         onClick=lambda rk="auto-comment": self.stack_set(rk), position=NavigationItemPosition.TOP)
        self.nav.addItem("auto-repost", icon=FIF.SHARE, text=self.ROUTE_TITLES["auto-repost"],
                         onClick=lambda rk="auto-repost": self.stack_set(rk), position=NavigationItemPosition.TOP)
        self.nav.addItem("auto-like", icon=FIF.HEART, text=self.ROUTE_TITLES["auto-like"],
                         onClick=lambda rk="auto-like": self.stack_set(rk), position=NavigationItemPosition.TOP)
        self.nav.addItem("auto-scan", icon=FIF.ZOOM, text=self.ROUTE_TITLES["auto-scan"],
                         onClick=lambda rk="auto-scan": self.stack_set(rk), position=NavigationItemPosition.TOP)

        # bottom
        self.nav.addItem("about", icon=FIF.INFO, text=self.ROUTE_TITLES["about"],
                         onClick=lambda rk="about": self.stack_set(rk), position=NavigationItemPosition.BOTTOM)

        # Right side
        right = QWidget()
        rightLay = QVBoxLayout(right)
        rightLay.setContentsMargins(0, 0, 0, 0)
        rightLay.setSpacing(0)

        # Top bar
        topBar = QFrame()
        topBar.setFixedHeight(64)
        topLay = QHBoxLayout(topBar)
        topLay.setContentsMargins(16, 8, 16, 8)
        topLay.setSpacing(12)

        self.titleLabel = QLabel(self.ROUTE_TITLES["auto-comment"])
        self.titleLabel.setProperty("cssClass", "h5")
        topLay.addWidget(self.titleLabel)
        topLay.addStretch(1)

        self.searchEdit = LineEdit()
        self.searchEdit.setPlaceholderText("Tìm kiếm…")
        self.searchEdit.setFixedWidth(280)
        topLay.addWidget(self.searchEdit)

        # Avatar + menu
        self.userBtn = QToolButton()
        self.userBtn.setIcon(FIF.PEOPLE.icon())
        self.userBtn.setIconSize(QSize(28, 28))
        self.userBtn.setPopupMode(QToolButton.InstantPopup)
        userMenu = QMenu(self.userBtn)
        userMenu.addAction(FIF.PEOPLE.icon(), "Profile")
        userMenu.addAction(FIF.SETTING.icon(), "Settings")
        actLogout = QAction(FIF.POWER_BUTTON.icon(), "Logout", self)
        userMenu.addAction(actLogout)
        self.userBtn.setMenu(userMenu)
        topLay.addWidget(self.userBtn)

        rightLay.addWidget(topBar)

        # Stack
        self.stack = QFrame()
        self.stackLay = QVBoxLayout(self.stack)
        self.stackLay.setContentsMargins(0, 0, 0, 0)
        self.autoCommentPage = AutoCommentPage()
        self.stackLay.addWidget(self.autoCommentPage)
        rightLay.addWidget(self.stack, 1)

        splitter.addWidget(self.nav)
        splitter.addWidget(right)
        splitter.setSizes([240, 1040])

        # Hooks
        actLogout.triggered.connect(self._logout)
        self.searchEdit.textChanged.connect(self._debouncedSearchText)

        # chọn mặc định
        self.nav.setCurrentItem("auto-comment")
        self.stack_set("auto-comment")

    def _logout(self):
        InfoBar.info(
            title="Logout",
            content="Bạn đã đăng xuất (fake).",
            orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=2500, parent=self
        )

    def _debouncedSearchText(self, text: str):
        if not text:
            return
        InfoBar.success(
            title="Tìm kiếm",
            content=f"Từ khóa: “{text}” (fake)",
            orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=1200, parent=self
        )

    def stack_set(self, route_key: str):
        """Chuyển trang theo route_key. Demo: luôn hiển thị AutoCommentPage."""
        # đặt tiêu đề theo route_key
        self.titleLabel.setText(self.ROUTE_TITLES.get(route_key, route_key))

        # Nếu bạn có nhiều trang, bạn có thể if/elif theo route_key ở đây.
        # Demo: luôn render autoCommentPage để giữ gọn.
        while self.stackLay.count():
            w = self.stackLay.takeAt(0).widget()
            if w:
                w.setParent(None)
        self.stackLay.addWidget(self.autoCommentPage)


# -------------------------------
# Run app
# -------------------------------

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
