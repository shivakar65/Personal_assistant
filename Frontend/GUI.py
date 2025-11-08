# -*- coding: utf-8 -*-
"""
Jervis Desktop GUI (PyQt5)
- Uses your existing assets and file I/O scheme:
    - .env -> Assistantname
    - Graphics directory for icons/gif
    - Files directory for Mic.data, Status.data, Responses.data
- Pages:
    1) Welcome (GIF + mic toggle + status)
    2) Chat (read-only chat stream + input box + send)
    3) Console (shows raw file contents for quick debug)
    4) Settings (very light app options)
- TopBar (frameless window controls) + Left Sidebar (navigation + mic)
- Carefully scales Jervis.gif within a fixed box (no fullscreen stretch)
- Clean separation of helpers, state, and widgets
"""

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget, QSplitter,
    QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame,
    QTextEdit, QLineEdit, QSizePolicy, QScrollArea, QSpacerItem, QCheckBox,
    QComboBox, QMessageBox, QFileDialog
)
from PyQt5.QtGui import (
    QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap,
    QTextBlockFormat, QCursor
)
from PyQt5.QtCore import Qt, QSize, QTimer, QRect
from dotenv import dotenv_values
import sys, os, datetime

# =========================
#   ENV + GLOBAL PATHS
# =========================

env_vars = dotenv_values(r"c:\Users\user\Desktop\jervisai\.env")
AssistantName = env_vars.get("Assistantname", "Jervis")

current_dir = os.getcwd()
TempDirPath = rf"{current_dir}\Frontend\Files"
GraphicsDirPath = rf"{current_dir}\Frontend\Graphics"

def GraphicsDirectoryPath(fname: str) -> str:
    return rf"{GraphicsDirPath}\{fname}"

def TempDirectoryPath(fname: str) -> str:
    return rf"{TempDirPath}\{fname}"

# Guard folders
os.makedirs(TempDirPath, exist_ok=True)
os.makedirs(GraphicsDirPath, exist_ok=True)

# =========================
#   FILE I/O HELPERS
# =========================

def set_text(filepath: str, text: str) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

def get_text(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def SetMicrophoneStatus(value: str) -> None:
    set_text(TempDirectoryPath("Mic.data"), value)

def GetMicrophoneStatus() -> str:
    return get_text(TempDirectoryPath("Mic.data"))

def SetAssistantStatus(value: str) -> None:
    set_text(TempDirectoryPath("Status.data"), value)

def GetAssistantStatus() -> str:
    return get_text(TempDirectoryPath("Status.data"))

def ShowTextToScreen(value: str) -> None:
    set_text(TempDirectoryPath("Responses.data"), value)

def AppendToResponses(line: str) -> None:
    path = TempDirectoryPath("Responses.data")
    old = get_text(path)
    if old and not old.endswith("\n"):
        old += "\n"
    set_text(path, (old or "") + line)

def MicButtonInitialed():
    # Note: original used "False" when mic icon shows "on"
    SetMicrophoneStatus("False")

def MicButtonClosed():
    # Note: original used "True" when mic icon shows "off"
    SetMicrophoneStatus("True")

# =========================
#   TEXT HELPERS
# =========================

def AnswerModifier(text: str) -> str:
    # remove empty lines
    return "\n".join([ln for ln in text.splitlines() if ln.strip()])

def QueryModifier(query: str) -> str:
    q = query.lower().strip()
    if not q:
        return ""
    question_words = ["how", "what", "who", "where", "when", "why", "which",
                      "whose", "whom", "can you", "what's", "where's", "how's"]
    words = q.split()
    if any(w + " " in q for w in question_words):
        # treat as question
        last = words[-1][-1]
        if last in [".", "?", "!"]:
            return q[:-1] + "?"
        return q + "?"
    else:
        last = words[-1][-1]
        if last in [".", "?", "!"]:
            return q[:-1] + "."
        return q + "."

# =========================
#   SMALL UTILS
# =========================

def readable_timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def icon_or_blank(name: str) -> QIcon:
    path = GraphicsDirectoryPath(name)
    if os.path.exists(path):
        return QIcon(path)
    return QIcon()  # blank if not found

# =========================
#   COMMON UI BUILDERS
# =========================

def make_hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet("color: #333;")
    return line

def set_smooth_button(b: QPushButton, height=36, flat_bg=True):
    if flat_bg:
        b.setStyleSheet("""
            QPushButton {
                background: #f7f7f7;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 6px 10px;
            }
            QPushButton:hover { background: #f0f0f0; }
            QPushButton:pressed { background: #eaeaea; }
        """)
    b.setFixedHeight(height)
    b.setCursor(QCursor(Qt.PointingHandCursor))

def label(text, size=14, bold=False, color="#111", align=Qt.AlignLeft):
    lb = QLabel(text)
    lb.setAlignment(align | Qt.AlignVCenter)
    lb.setStyleSheet(f"color:{color}; font-size:{size}px; font-weight:{'600' if bold else '400'};")
    return lb

def make_section_title(txt: str) -> QLabel:
    return label(txt, size=18, bold=True, color="#111", align=Qt.AlignLeft)

def make_note(txt: str) -> QLabel:
    return label(txt, size=12, bold=False, color="#666", align=Qt.AlignLeft)

# =========================
#   TOP BAR (FRAMELESS)
# =========================

class TopBar(QWidget):
    def __init__(self, parent, pages: QStackedWidget):
        super().__init__(parent)
        self.pages = pages
        self.setFixedHeight(52)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 4, 10, 4)
        lay.setSpacing(10)

        self.title = label(f"{AssistantName.capitalize()} AI", size=16, bold=True)
        self.title.setStyleSheet("color:#000; font-size:16px;")
        lay.addWidget(self.title)
        lay.addStretch(1)

        # ✅ FIXED: icon first, text second
        self.home_btn = QPushButton(icon_or_blank("Home.png"), " Home")
        self.chat_btn = QPushButton(icon_or_blank("Chats.png"), " Chat")
        for b in (self.home_btn, self.chat_btn):
            set_smooth_button(b)
            lay.addWidget(b)

        lay.addStretch(1)

        # ✅ FIXED: icon first, text second (empty text)
        self.min_btn = QPushButton(icon_or_blank("Minimize2.png"), "")
        self.max_btn = QPushButton(icon_or_blank("Maximize.png"), "")
        self.close_btn = QPushButton(icon_or_blank("Close.png"), "")

        for b in (self.min_btn, self.max_btn, self.close_btn):
            set_smooth_button(b, height=32)
            b.setFixedWidth(44)
            lay.addWidget(b)

        self.home_btn.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.chat_btn.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.min_btn.clicked.connect(self.window_minimize)
        self.max_btn.clicked.connect(self.window_max_restore)
        self.close_btn.clicked.connect(self.window_close)

        self._is_max = False

    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.white)

    def window_minimize(self):
        self.parent().showMinimized()

    def window_close(self):
        self.parent().close()

    def window_max_restore(self):
        parent = self.parent()
        if parent.isMaximized():
            parent.showNormal()
            self.max_btn.setIcon(icon_or_blank("Maximize.png"))
        else:
            parent.showMaximized()
            self.max_btn.setIcon(icon_or_blank("Minimize.png"))

# =========================
#   LEFT SIDEBAR
# =========================

class SideBar(QWidget):
    def __init__(self, stacked: QStackedWidget):
        super().__init__()
        self.pages = stacked
        self.setFixedWidth(220)

        self.setStyleSheet("""
            QWidget#SideBar {
                background:#0b0b0b;
            }
        """)
        self.setObjectName("SideBar")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(12)

        # Logo/title
        head = QHBoxLayout()
        logo = QLabel()
        logo.setFixedSize(28, 28)
        pix = QPixmap(GraphicsDirectoryPath("voice.png"))
        if pix.isNull():
            pix = QPixmap(28, 28)
            pix.fill(Qt.gray)
        logo.setPixmap(pix.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        head.addWidget(logo)
        head.addWidget(self._itxt("Jervis", bold=True))
        head.addStretch(1)
        lay.addLayout(head)

        lay.addWidget(self._sep())

        # Nav buttons
        # ✅ FIXED: icon first, text second
        self.btn_home = self._nav_btn("Welcome", "Home.png")
        self.btn_chat = self._nav_btn("Chat", "Chats.png")
        self.btn_console = self._nav_btn("Console", "Minimize2.png")
        self.btn_settings = self._nav_btn("Settings", "Maximize.png")

        lay.addWidget(self.btn_home)
        lay.addWidget(self.btn_chat)
        lay.addWidget(self.btn_console)
        lay.addWidget(self.btn_settings)

        lay.addStretch(1)
        lay.addWidget(self._sep())

        # Mic toggle
        self.mic_label = self._itxt("Mic: Off", color="#999")
        self.mic_icon = QLabel()
        self.mic_icon.setAlignment(Qt.AlignCenter)
        self.mic_icon.setFixedSize(72, 72)
        self._set_mic_icon(False)

        self.mic_button = QPushButton("Toggle Mic")
        set_smooth_button(self.mic_button)
        self.mic_button.clicked.connect(self.toggle_mic)

        lay.addWidget(self.mic_icon, alignment=Qt.AlignCenter)
        lay.addWidget(self.mic_label, alignment=Qt.AlignCenter)
        lay.addWidget(self.mic_button)

        # Connections
        self.btn_home.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_chat.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        self.btn_console.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        self.btn_settings.clicked.connect(lambda: self.pages.setCurrentIndex(3))

        # Initialize mic status visual from file
        mic_is_off = (GetMicrophoneStatus().strip() == "True")
        self._set_mic_icon(not mic_is_off)
        self.mic_label.setText(f"Mic: {'On' if not mic_is_off else 'Off'}")

    def _sep(self):
        s = QFrame()
        s.setFrameShape(QFrame.HLine)
        s.setStyleSheet("color:#2b2b2b;")
        return s

    def _itxt(self, text, bold=False, color="#eaeaea"):
        return label(text, size=14, bold=bold, color=color)

    def _nav_btn(self, text, icon):
        # ✅ FIXED constructor order here as well
        b = QPushButton(icon_or_blank(icon), f"  {text}")
        b.setCursor(QCursor(Qt.PointingHandCursor))
        b.setStyleSheet("""
            QPushButton {
                background: #121212; color:#dcdcdc;
                border: 1px solid #1e1e1e;
                border-radius: 10px; height: 38px; text-align: left;
                padding-left: 10px;
            }
            QPushButton:hover { background:#181818; }
            QPushButton:pressed { background:#101010; }
        """)
        return b

    def _set_mic_icon(self, is_on: bool):
        img = "Mic_on.png" if is_on else "Mic_off.png"
        pix = QPixmap(GraphicsDirectoryPath(img))
        if pix.isNull():
            pix = QPixmap(72, 72)
            pix.fill(Qt.darkGray)
        self.mic_icon.setPixmap(pix.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def toggle_mic(self):
        # File scheme from your project:
        # "False" -> mic ON (initialed) ; "True" -> mic closed/off
        current = GetMicrophoneStatus().strip()
        is_off = (current == "True")
        if is_off:
            MicButtonInitialed()  # set "False"
            self._set_mic_icon(True)
            self.mic_label.setText("Mic: On")
        else:
            MicButtonClosed()     # set "True"
            self._set_mic_icon(False)
            self.mic_label.setText("Mic: Off")

# =========================
#   PAGE: WELCOME
# =========================

class WelcomePage(QWidget):
    def __init__(self):
        super().__init__()
        base = QVBoxLayout(self)
        base.setContentsMargins(24, 24, 24, 24)
        base.setSpacing(14)

        base.addWidget(make_section_title("Welcome"))
        base.addWidget(make_note("Animated Jervis + Assistant status preview"))

        # GIF box
        self.gif_box = QLabel()
        self.gif_box.setMinimumSize(800, 450)
        self.gif_box.setMaximumSize(800, 450)
        self.gif_box.setAlignment(Qt.AlignCenter)
        self.gif_box.setStyleSheet("border: 1px solid #333; background:#000; border-radius: 12px;")
        base.addWidget(self.gif_box, alignment=Qt.AlignLeft)

        # Jervis.gif
        self.movie = QMovie(GraphicsDirectoryPath("Jervis.gif"))
        self.movie.setScaledSize(QSize(800, 450))
        self.gif_box.setMovie(self.movie)
        self.movie.start()

        base.addSpacing(6)
        base.addWidget(make_hline())

        # Assistant status row
        st = QHBoxLayout()
        st.addWidget(label("Assistant Status:", size=14, bold=True))
        self.status_label = label(GetAssistantStatus() or "Idle", size=14, color="#444")
        st.addWidget(self.status_label)
        st.addStretch(1)

        refresh_btn = QPushButton("Refresh Status")
        set_smooth_button(refresh_btn)
        refresh_btn.clicked.connect(self.refresh_status)
        st.addWidget(refresh_btn)

        base.addLayout(st)
        base.addStretch(1)

        # small timer to keep the movie alive if needed
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: None)
        self.timer.start(2000)

    def refresh_status(self):
        self.status_label.setText(GetAssistantStatus() or "Idle")

# =========================
#   PAGE: CHAT
# =========================

class ChatPage(QWidget):
    def __init__(self):
        super().__init__()
        base = QVBoxLayout(self)
        base.setContentsMargins(24, 24, 24, 24)
        base.setSpacing(12)

        base.addWidget(make_section_title("Chat"))
        base.addWidget(make_note("Stream from Frontend/Files/Responses.data"))

        # Chat text area
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setStyleSheet("""
            QTextEdit {
                background:#0e0e0e; color:#f1f1f1; border:1px solid #2d2d2d; border-radius: 12px;
                padding: 12px;
            }
        """)
        font = QFont(); font.setPointSize(12)
        self.chat.setFont(font)
        base.addWidget(self.chat)

        # GIF inline (smaller)
        self.gif_inline = QLabel()
        self.gif_inline.setFixedSize(480, 270)
        self.gif_inline.setAlignment(Qt.AlignCenter)
        self.gif_inline.setStyleSheet("background:#000; border:1px solid #333; border-radius: 12px;")
        self.movie_small = QMovie(GraphicsDirectoryPath("Jervis.gif"))
        self.movie_small.setScaledSize(QSize(480, 270))
        self.gif_inline.setMovie(self.movie_small)
        self.movie_small.start()

        # Bottom row
        bottom = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Type your message...")
        self.input.setStyleSheet("""
            QLineEdit {
                background:#151515; color:#eaeaea; border:1px solid #2d2d2d;
                border-radius: 10px; height: 42px; padding: 0 12px;
            }
        """)
        send_btn = QPushButton("Send")
        set_smooth_button(send_btn, height=42)
        clear_btn = QPushButton("Clear")
        set_smooth_button(clear_btn, height=42)

        bottom.addWidget(self.input, 4)
        bottom.addWidget(send_btn, 1)
        bottom.addWidget(clear_btn, 1)
        bottom.addSpacing(10)
        bottom.addWidget(self.gif_inline, 0)

        base.addLayout(bottom)

        # Timer to load messages
        self.old = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.load_messages)
        self.timer.start(300)

        # Buttons
        send_btn.clicked.connect(self.handle_send)
        clear_btn.clicked.connect(self.clear_chat)

    def load_messages(self):
        path = TempDirectoryPath("Responses.data")
        txt = get_text(path)
        if txt != self.old:
            self.chat.setPlainText(txt)
            self.chat.moveCursor(self.chat.textCursor().End)
            self.old = txt

    def handle_send(self):
        raw = self.input.text().strip()
        if not raw:
            return
        q = QueryModifier(raw)
        AppendToResponses(f"[{readable_timestamp()}] You: {q}")
        # In your pipeline, your backend would write the assistant response.
        # Here we just append a placeholder to show the flow.
        ans = AnswerModifier(f"[{readable_timestamp()}] {AssistantName}: I received your message.")
        AppendToResponses(ans)
        self.input.clear()

    def clear_chat(self):
        ShowTextToScreen("")
        self.chat.clear()
        self.old = ""

# =========================
#   PAGE: CONSOLE (RAW FILES)
# =========================

class ConsolePage(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)

        root.addWidget(make_section_title("Console"))
        root.addWidget(make_note("Quick view/edit of project text files."))

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        # File viewers
        self.paths = {
            "Mic": TempDirectoryPath("Mic.data"),
            "Status": TempDirectoryPath("Status.data"),
            "Responses": TempDirectoryPath("Responses.data")
        }
        self.edits = {}

        r = 0
        for name, path in self.paths.items():
            grid.addWidget(label(name, bold=True), r, 0)
            grid.addWidget(label(path, color="#666"), r, 1)
            open_btn = QPushButton("Open")
            set_smooth_button(open_btn)
            open_btn.clicked.connect(lambda _, p=path: self.open_in_folder(p))
            grid.addWidget(open_btn, r, 2)
            r += 1

            te = QTextEdit()
            te.setStyleSheet("background:#111; color:#eee; border:1px solid #333; border-radius: 8px;")
            te.setPlainText(get_text(path))
            self.edits[name] = te
            grid.addWidget(te, r, 0, 1, 3)
            r += 1

        root.addLayout(grid)

        # Controls
        ctrl = QHBoxLayout()
        save_btn = QPushButton("Save All")
        set_smooth_button(save_btn)
        reload_btn = QPushButton("Reload")
        set_smooth_button(reload_btn)
        ctrl.addStretch(1)
        ctrl.addWidget(reload_btn)
        ctrl.addWidget(save_btn)

        root.addLayout(ctrl)
        root.addStretch(1)

        reload_btn.clicked.connect(self.reload_all)
        save_btn.clicked.connect(self.save_all)

    def open_in_folder(self, path: str):
        if os.path.exists(path):
            folder = os.path.dirname(path)
            os.startfile(folder)
        else:
            QMessageBox.warning(self, "Not Found", f"File not found:\n{path}")

    def reload_all(self):
        for name, path in self.paths.items():
            self.edits[name].setPlainText(get_text(path))

    def save_all(self):
        for name, path in self.paths.items():
            set_text(path, self.edits[name].toPlainText())
        QMessageBox.information(self, "Saved", "All files saved.")

# =========================
#   PAGE: SETTINGS
# =========================

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        base = QVBoxLayout(self)
        base.setContentsMargins(24, 24, 24, 24)
        base.setSpacing(12)

        base.addWidget(make_section_title("Settings"))
        base.addWidget(make_note("Basic visual preferences (local to UI)."))

        # Theme toggle (demo — not fully skinning the app)
        theme_row = QHBoxLayout()
        theme_row.addWidget(label("Theme:", bold=True))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch(1)

        apply_btn = QPushButton("Apply")
        set_smooth_button(apply_btn)
        theme_row.addWidget(apply_btn)
        base.addLayout(theme_row)

        base.addWidget(make_hline())

        # GIF size controls (apply to Welcome page)
        base.addWidget(label("Jervis GIF size (Welcome page):", bold=True))
        size_row = QHBoxLayout()
        self.size_combo = QComboBox()
        self.size_combo.addItems(["800x450", "640x360", "960x540"])
        size_row.addWidget(self.size_combo)
        save_size_btn = QPushButton("Apply Size")
        set_smooth_button(save_size_btn)
        size_row.addWidget(save_size_btn)
        size_row.addStretch(1)
        base.addLayout(size_row)

        base.addStretch(1)

        apply_btn.clicked.connect(self.apply_theme)
        save_size_btn.clicked.connect(self.apply_gif_size)

    def apply_theme(self):
        # Quick demo theme change: invert chat background palette
        mode = self.theme_combo.currentText()
        if mode == "Light":
            qApp.setStyleSheet("""
                QWidget { color:#111; }
                QTextEdit { background:#fff; color:#111; }
            """)
        else:
            qApp.setStyleSheet("")
        QMessageBox.information(self, "Theme", f"Applied: {mode}")

    def apply_gif_size(self):
        size_txt = self.size_combo.currentText()
        w, h = [int(x) for x in size_txt.split("x")]
        # broadcast via assistant status for demo; actual Welcome page listens on refresh
        SetAssistantStatus(f"GIF size preference set to {w}x{h} (reopen Welcome page)")

# =========================
#   CENTRAL AREA WRAPPER
# =========================

class CenterArea(QWidget):
    def __init__(self):
        super().__init__()
        self.stack = QStackedWidget()
        self.page_welcome = WelcomePage()
        self.page_chat = ChatPage()
        self.page_console = ConsolePage()
        self.page_settings = SettingsPage()

        self.stack.addWidget(self.page_welcome)  # 0
        self.stack.addWidget(self.page_chat)     # 1
        self.stack.addWidget(self.page_console)  # 2
        self.stack.addWidget(self.page_settings) # 3

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.stack)

# =========================
#   MAIN WINDOW
# =========================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMinimumSize(1100, 720)

        # Top bar + content
        self.center = CenterArea()
        self.top = TopBar(self, self.center.stack)
        self.sidebar = SideBar(self.center.stack)

        wrapper = QWidget()
        v = QVBoxLayout(wrapper)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        v.addWidget(self.top)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        body.addWidget(self.sidebar)
        body.addWidget(self.center, 1)
        v.addLayout(body)

        self.setCentralWidget(wrapper)
        self.showMaximized()

# =========================
#   ENTRY
# =========================

def GraphicalUserInterface():
    app = QApplication(sys.argv)
    # store QApplication reference globally if SettingsPage accesses it
    global qApp
    qApp = app
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    GraphicalUserInterface()
