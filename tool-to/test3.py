# -*- coding: utf-8 -*-
# Full demo: PySide6 + qfluentwidgets (fixed icons)
# pip install PySide6 qfluentwidgets

from PySide6.QtCore import Qt, QRect, QAbstractTableModel, QModelIndex, QSize, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QHBoxLayout, QVBoxLayout, QGridLayout,
    QSplitter, QFrame, QLabel, QTableView, QHeaderView,
    QStyledItemDelegate, QStyleOptionButton, QStyle, QStyleOptionViewItem,
    QAbstractItemView, QToolButton, QSpinBox, QTextEdit, QMenu, QFileDialog
)

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, FluentIcon as FIF,
    setTheme, Theme, LineEdit, PrimaryPushButton, PushButton,
    InfoBar, InfoBarPosition, setThemeColor,
    CardWidget, TitleLabel, SubtitleLabel, BodyLabel, ComboBox
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
        if self.rowCount() > 0:
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
# Pages (AutoComment + DropArea)
# -------------------------------

class DropArea(QFrame):
    """Ô kéo-thả + click chọn file, hiệu ứng Fluent 'màu mè'."""
    clicked = Signal()

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("DropArea")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 20, 16, 20)
        lay.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(8)
        ic = QLabel()
        ic.setPixmap(FIF.PHOTO.icon().pixmap(24, 24))
        ic.setFixedSize(28, 28)
        top.addWidget(ic)

        ttl = SubtitleLabel("Tệp phương tiện")
        ttl.setStyleSheet("SubtitleLabel{font-weight:600;}")
        top.addWidget(ttl)
        top.addStretch(1)

        lay.addLayout(top)

        self.label = BodyLabel(text)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setStyleSheet("BodyLabel{opacity:0.9;}")
        lay.addWidget(self.label)

        self.tip = BodyLabel("Hỗ trợ: PNG • JPG • GIF • MP4 • MOV")
        self.tip.setAlignment(Qt.AlignCenter)
        self.tip.setStyleSheet("BodyLabel{color:rgba(0,0,0,0.55);}")
        lay.addWidget(self.tip)

        # Fluent-ish style
        self.setProperty("cssClass", "card")
        self.setStyleSheet("""
        QFrame#DropArea {
            border-radius: 14px;
            border: 1.6px dashed rgba(59,130,246,0.55);
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 rgba(59,130,246,0.05),
                        stop:1 rgba(99,102,241,0.05));
        }
        QFrame#DropArea:hover{
            border: 1.6px dashed rgba(59,130,246,0.95);
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 rgba(59,130,246,0.10),
                        stop:1 rgba(99,102,241,0.10));
        }
        """)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()


class AutoCommentPage(QWidget):
    """Trang 'Bình luận tự động' – đẹp, chuẩn form, màu mè kiểu Fluent."""
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # =========================
        # 1) DANH SÁCH MỤC TIÊU
        # =========================
        cardTable = CardWidget()
        cLay = QVBoxLayout(cardTable)
        cLay.setContentsMargins(14, 14, 14, 14)
        cLay.setSpacing(10)

        headRow = QHBoxLayout()
        iconTbl = QLabel()
        # FIX: dùng DOCUMENT thay vì TASK_LIST_RTL
        iconTbl.setPixmap(FIF.DOCUMENT.icon().pixmap(22, 22))
        headRow.addWidget(iconTbl)

        titleTbl = TitleLabel("Danh sách mục tiêu")
        headRow.addWidget(titleTbl)
        headRow.addSpacing(8)

        self.badgeSelected = BodyLabel("")   # dynamic: x/y đã chọn
        self.badgeSelected.setStyleSheet("""
            BodyLabel{
                padding:2px 8px;border-radius:999px;
                background:rgba(59,130,246,0.12);
                color:rgb(30,58,138);font-weight:600;
            }""")
        headRow.addWidget(self.badgeSelected)
        headRow.addStretch(1)

        # quick actions (FIX icon names)
        self.actAll = PushButton("Chọn tất cả", icon=FIF.CHECKBOX)
        self.actNone = PushButton("Bỏ chọn", icon=FIF.CLOSE)
        for b in (self.actAll, self.actNone):
            b.setFixedHeight(28)
        headRow.addWidget(self.actAll)
        headRow.addWidget(self.actNone)
        cLay.addLayout(headRow)

        # Bảng
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setItemDelegateForColumn(0, CheckBoxDelegate(self.table))
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableView{
                background:transparent; 
                border-radius:8px;
            }
            QHeaderView::section{
                background:rgba(59,130,246,0.10);
                border:none;border-bottom:1px solid rgba(0,0,0,0.08);
                padding:8px 6px;font-weight:600;
            }
            QTableView::item:selected{
                background:rgba(99,102,241,0.18);
            }
        """)

        headers = ["", "STT", "Live", "Username", "Name", "UID"]
        rows = [
            [True,  1, "Live", "haianhnguyen396800019", "Nguyễn Hải Anh", "89283498014"],
            [False, 2, "Live", "maihoa_2103",          "Mai Hoa",        "1029384756"],
            [True,  3, "Live", "user_alpha",           "User Alpha",     "5566778899"],
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
            self.badgeSelected.setText(f"{checked} / {total} đã chọn")

        update_header_state()
        header.stateChanged.connect(lambda st: (self.model.set_all_checked(st == Qt.Checked), update_header_state()))
        self.model.dataChanged.connect(lambda *_: update_header_state())

        self.actAll.clicked.connect(lambda: (self.model.set_all_checked(True), update_header_state()))
        self.actNone.clicked.connect(lambda: (self.model.set_all_checked(False), update_header_state()))

        cLay.addWidget(self.table)

        # =========================
        # 2) KHU CẤU HÌNH & NỘI DUNG
        # =========================
        mid = QFrame()
        midLay = QGridLayout(mid)
        midLay.setContentsMargins(0, 0, 0, 0)
        midLay.setHorizontalSpacing(16)
        midLay.setVerticalSpacing(16)

        # --------- Cột trái: MODE + LINKS + PARAMS ----------
        leftCard = CardWidget()
        leftLay = QVBoxLayout(leftCard)
        leftLay.setContentsMargins(14, 14, 14, 14)
        leftLay.setSpacing(10)

        rowHdr = QHBoxLayout()
        iconMode = QLabel()
        # FIX: dùng SETTING thay vì BRANCH
        iconMode.setPixmap(FIF.SETTING.icon().pixmap(20, 20))
        rowHdr.addWidget(iconMode)
        rowHdr.addWidget(SubtitleLabel("Chọn chế độ bình luận"))
        rowHdr.addStretch(1)
        leftLay.addLayout(rowHdr)

        # mode line
        modeRow = QHBoxLayout()
        modeRow.setSpacing(10)
        modeLbl = BodyLabel("Chế độ:")
        modeLbl.setStyleSheet("BodyLabel{font-weight:600;}")
        modeRow.addWidget(modeLbl)

        self.modeCombo = ComboBox()
        self.modeCombo.addItems(["Bài viết", "Video", "Live"])
        self.modeCombo.setCurrentText("Bài viết")
        self.modeCombo.setFixedWidth(160)
        modeRow.addWidget(self.modeCombo)

        modeRow.addStretch(1)
        leftLay.addLayout(modeRow)

        hint1 = BodyLabel("Bạn đang chọn chế độ bài viết • Enter để xuống dòng cho mỗi link")
        hint1.setStyleSheet("BodyLabel{color:rgba(0,0,0,0.65);}")
        leftLay.addWidget(hint1)

        self.linksEdit = QTextEdit()
        self.linksEdit.setPlaceholderText("https://youtu.be/...\nhttps://www.youtube.com/watch?v=...")
        self.linksEdit.setFixedHeight(120)
        self.linksEdit.setText(
            "https://www.youtube.com/watch?v=5xlNfz4hSBw\n"
            "https://youtu.be/UagJheg3wx0?si=pSJedjtCRWx1VqH_"
        )
        mono = QFont("Cascadia Mono, Consolas, Menlo, monospace")
        mono.setStyleHint(QFont.Monospace)
        self.linksEdit.setFont(mono)
        self.linksEdit.setStyleSheet("QTextEdit{background:rgba(0,0,0,0.03); border-radius:8px;}")
        leftLay.addWidget(self.linksEdit)

        # params
        grid = QGridLayout()
        grid.setHorizontalSpacing(10); grid.setVerticalSpacing(8)

        labThreads = BodyLabel("Số luồng"); labAmount = BodyLabel("Số lượng")
        for lb in (labThreads, labAmount):
            lb.setStyleSheet("BodyLabel{font-weight:600;}")

        self.threadSpin = QSpinBox(); self.threadSpin.setRange(1, 64); self.threadSpin.setValue(1)
        self.threadSpin.setFixedWidth(90)
        self.amountSpin = QSpinBox(); self.amountSpin.setRange(1, 10000); self.amountSpin.setValue(50)
        self.amountSpin.setFixedWidth(100)

        labDelay = BodyLabel("Delay"); labTo = BodyLabel("đến"); labUnit = BodyLabel("giây")
        for lb in (labDelay, labTo, labUnit):
            lb.setStyleSheet("BodyLabel{font-weight:600;}")

        self.delayMin = QSpinBox(); self.delayMin.setRange(0, 3600); self.delayMin.setValue(10); self.delayMin.setFixedWidth(90)
        self.delayMax = QSpinBox(); self.delayMax.setRange(0, 3600); self.delayMax.setValue(15); self.delayMax.setFixedWidth(90)

        grid.addWidget(labThreads, 0, 0); grid.addWidget(self.threadSpin, 0, 1)
        grid.addWidget(labAmount, 0, 2);  grid.addWidget(self.amountSpin, 0, 3)
        grid.addWidget(labDelay, 1, 0);   grid.addWidget(self.delayMin, 1, 1)
        grid.addWidget(labTo,    1, 2);   grid.addWidget(self.delayMax, 1, 3)
        grid.addWidget(labUnit,  1, 4)
        leftLay.addLayout(grid)

        # buttons
        btnRow = QHBoxLayout()
        self.startBtn = PrimaryPushButton("Bắt đầu", icon=FIF.PLAY)
        self.stopBtn = PushButton("Dừng", icon=FIF.PAUSE)
        self.scheduleLabel = BodyLabel("Đặt lịch")
        self.scheduleLabel.setStyleSheet("""
            BodyLabel{
                padding:4px 10px;border-radius:999px;
                background:rgba(236,72,153,0.14);
                color:rgb(131,24,67);font-weight:700;
            }""")
        for b in (self.startBtn, self.stopBtn):
            b.setFixedHeight(36)
        btnRow.addWidget(self.startBtn); btnRow.addWidget(self.stopBtn); btnRow.addSpacing(6); btnRow.addWidget(self.scheduleLabel); btnRow.addStretch(1)
        leftLay.addLayout(btnRow)

        # --------- Cột phải: NỘI DUNG + MEDIA + LỊCH SỬ ----------
        rightCard = CardWidget()
        rightLay = QVBoxLayout(rightCard)
        rightLay.setContentsMargins(14, 14, 14, 14)
        rightLay.setSpacing(12)

        topC = QHBoxLayout()
        icC = QLabel(); icC.setPixmap(FIF.MESSAGE.icon().pixmap(20, 20))
        topC.addWidget(icC)
        topC.addWidget(SubtitleLabel("Nội dung"))
        topC.addStretch(1)
        self.aiBtn = PushButton("Sử dụng AI", icon=FIF.ROBOT)
        self.aiBtn.setFixedHeight(30)
        topC.addWidget(self.aiBtn)
        rightLay.addLayout(topC)

        self.contentEdit = QTextEdit()
        self.contentEdit.setPlaceholderText("<comment>Nội dung bình luận</comment>\n<comment>Nội dung khác</comment>")
        self.contentEdit.setFixedHeight(96)
        self.contentEdit.setText(
            "<comment>Truy cập link này nhé: https://www.youtube.com/watch?v=5xlNfz4hSBw</comment>\n"
            "<comment>Bạn chụp gửi lại mình nhé.</comment>"
        )
        self.contentEdit.setStyleSheet("QTextEdit{background:rgba(0,0,0,0.03); border-radius:8px;}")
        rightLay.addWidget(self.contentEdit)

        fmtHint = BodyLabel("Random nội dung theo format: <comment>nội dung bình luận</comment>")
        fmtHint.setStyleSheet("BodyLabel{color:rgba(0,0,0,0.65);}")
        rightLay.addWidget(fmtHint)

        mediaRow = QHBoxLayout()
        icM = QLabel(); icM.setPixmap(FIF.VIDEO.icon().pixmap(20, 20))
        mediaRow.addWidget(icM)
        mediaRow.addWidget(SubtitleLabel("Chọn ảnh/video"))
        mediaRow.addStretch(1)
        rightLay.addLayout(mediaRow)

        self.mediaDrop = DropArea("Kéo thả, hoặc nhấp để chọn file hình ảnh hoặc video")
        self.mediaDrop.clicked.connect(self.pick_files)
        rightLay.addWidget(self.mediaDrop)

        hRow = QHBoxLayout()
        icH = QLabel(); icH.setPixmap(FIF.HISTORY.icon().pixmap(20, 20))
        hRow.addWidget(icH)
        hRow.addWidget(SubtitleLabel("Lịch sử"))
        hRow.addStretch(1)
        rightLay.addLayout(hRow)

        self.history = QTextEdit()
        self.history.setReadOnly(True)
        self.history.setFixedHeight(96)
        self.history.setStyleSheet("""
            QTextEdit{
                background:rgba(17,24,39,0.04);
                border-radius:8px;
                font-family: 'Cascadia Mono','Consolas','Menlo',monospace;
                font-size:12px;
            }""")
        self.history.setText(
            "[14:31:44 09-10-2025][haianhnguyen396800019][OK] Trả lời bình luận thành công link comment <>\n"
            "[14:40:31 09-10-2025][haianhnguyen396800019][OK] Trả lời bình luận thành công link comment <>\n"
            "[14:43:12 09-10-2025][haianhnguyen396800019][OK] Trả lời bình luận thành công link comment <>\n"
            "[14:50:04 09-10-2025][haianhnguyen396800019][OK] Trả lời bình luận thành công link comment <>"
        )
        rightLay.addWidget(self.history)

        # đặt 2 card vào grid
        midLay.addWidget(leftCard, 0, 0, 1, 6)
        midLay.addWidget(rightCard, 0, 6, 1, 6)

        # add vào root
        root.addWidget(cardTable)
        root.addWidget(mid)

        # ---------------- events ----------------
        self.startBtn.clicked.connect(self._start)
        self.stopBtn.clicked.connect(self._stop)
        self.aiBtn.clicked.connect(self._ai_helper)

    # ===== handlers =====
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

    def _ai_helper(self):
        # demo: thêm 1 biến thể comment
        self.contentEdit.append("<comment>Tuyệt! Mình đã xem, cảm ơn nhé 😄</comment>")
        InfoBar.info(
            title="AI gợi ý",
            content="Đã chèn 1 biến thể bình luận (demo).",
            orient=Qt.Horizontal, isClosable=True, position=InfoBarPosition.TOP_RIGHT, duration=1800, parent=self
        )

    def pick_files(self):
        QFileDialog.getOpenFileNames(
            self, "Chọn ảnh/video", "",
            "Media (*.png *.jpg *.jpeg *.bmp *.gif *.mp4 *.mov)"
        )

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
        setTheme(Theme.AUTO)           # tự động theo OS (Light/Dark)
        setThemeColor("#3B82F6")       # accent xanh (Tailwind blue-500)

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
        # FIX: dùng SEARCH thay cho ZOOM (tùy phiên bản)
        self.nav.addItem("auto-scan", icon=FIF.SEARCH, text=self.ROUTE_TITLES["auto-scan"],
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

        # self.titleLabel = QLabel(self.ROUTE_TITLES["auto-comment"])
        self.titleLabel = TitleLabel(self.ROUTE_TITLES["auto-comment"])
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

        # Nếu có nhiều trang, xử lý if/elif theo route_key ở đây.
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
