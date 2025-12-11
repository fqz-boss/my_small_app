import os
import sys

import google.generativeai as genai
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontDatabase
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QLineEdit,
                               QListWidget, QFrame)

# --- 配置 ---
API_KEY = os.getenv("API_KEY") or ""
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 配色与样式 ---
COLORS = {
    "bg": "#0f172a",
    "surface": "#1e293b",
    "primary": "#e11d48",
    "primary_hover": "#be123c",
    "text_main": "#f8fafc",
    "text_dim": "#94a3b8",
    "border": "#334155",
    "accent": "#f43f5e"
}

STYLESHEET = f"""
QMainWindow {{ background-color: {COLORS['bg']}; }}
QWidget {{ color: {COLORS['text_main']}; font-family: 'Segoe UI', sans-serif; }}

/* 紧凑按钮样式 */
QPushButton {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px 12px;
    color: {COLORS['text_dim']};
    font-size: 12px;
}}
QPushButton:hover {{
    background-color: #334155;
    color: {COLORS['text_main']};
    border-color: {COLORS['text_dim']};
}}
QPushButton:checked {{
    background-color: {COLORS['primary']};
    color: white;
    border-color: {COLORS['primary']};
}}

QPushButton#PrimaryBtn {{
    background-color: {COLORS['primary']};
    border: none;
    color: white;
    font-weight: bold;
    padding: 8px 16px;
    font-size: 13px;
}}
QPushButton#PrimaryBtn:hover {{ background-color: {COLORS['primary_hover']}; }}

QPushButton#GhostBtn {{
    background-color: transparent;
    border: none;
    color: {COLORS['text_dim']};
    font-size: 11px;
}}
QPushButton#GhostBtn:hover {{ color: {COLORS['accent']}; }}

/* 输入框 */
QLineEdit {{
    background-color: #020617;
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px;
    color: white;
    font-size: 12px;
}}
QLineEdit:focus {{ border: 1px solid {COLORS['primary']}; }}

/* 列表 */
QListWidget {{
    background-color: rgba(30, 41, 59, 0.3);
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    outline: none;
    font-size: 13px;
}}
QListWidget::item {{ padding: 8px; border-bottom: 1px solid #1e293b; }}
QListWidget::item:selected {{ background-color: rgba(225, 29, 72, 0.15); color: {COLORS['accent']}; }}
"""


# --- AI 线程 ---
class AIWorker(QThread):
    finished = Signal(str)

    def __init__(self, task_name, mode="break"):
        super().__init__()
        self.task_name = task_name
        self.mode = mode

    def run(self):
        if not API_KEY:
            self.finished.emit("Tip: Configure API Key for AI suggestions.")
            return
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            if self.mode == "break":
                prompt = f"I finished: '{self.task_name}'. Suggest a 5-min break (under 15 words)."
            else:
                prompt = "One short, powerful focus tip (under 10 words)."
            response = model.generate_content(prompt)
            self.finished.emit(response.text.strip())
        except:
            self.finished.emit("Take a deep breath.")


# --- 圆形进度条 (紧凑版) ---
class ProgressRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 200)  # 缩小尺寸
        self.percentage = 1.0
        self.text = "25:00"
        self.status = "READY"
        self.is_active = False

    def update_progress(self, time_left, total_time, is_active):
        self.text = f"{time_left // 60:02d}:{time_left % 60:02d}"
        self.percentage = time_left / total_time if total_time > 0 else 0
        self.status = "RUNNING" if is_active else ("PAUSED" if time_left < total_time else "READY")
        self.is_active = is_active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        rect_size = 170  # 绘图区域缩小
        x, y = (w - rect_size) / 2, (h - rect_size) / 2

        # 背景
        pen_bg = QPen(QColor(COLORS['surface']))
        pen_bg.setWidth(8)  # 线条变细
        pen_bg.setCapStyle(Qt.RoundCap)
        painter.setPen(pen_bg)
        painter.drawEllipse(x, y, rect_size, rect_size)

        # 进度
        if self.percentage > 0:
            pen_fg = QPen(QColor(COLORS['primary']))
            pen_fg.setWidth(8)
            pen_fg.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_fg)
            painter.drawArc(x, y, rect_size, rect_size, 90 * 16, -self.percentage * 360 * 16)

        # 文字
        painter.setPen(QColor(COLORS['text_main']))
        painter.setFont(QFont("Consolas", 36, QFont.Bold))  # 字体缩小
        painter.drawText(self.rect(), Qt.AlignCenter, self.text)

        # 状态小字
        painter.setPen(QColor(COLORS['text_dim']))
        f_status = QFont("Segoe UI", 9, QFont.Bold)
        f_status.setLetterSpacing(QFont.AbsoluteSpacing, 1)
        painter.setFont(f_status)
        painter.drawText(QRect(0, y + 110, w, 30), Qt.AlignCenter, self.status)


# --- 主窗口 ---
class FocusFlowWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FocusFlow")
        # 初始紧凑尺寸
        self.compact_width = 340
        self.expanded_width = 660
        self.height_size = 520
        self.resize(self.compact_width, self.height_size)

        self.total_time = 25 * 60
        self.time_left = self.total_time
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_tick)
        self.is_running = False
        self.active_task_index = -1

        self.setup_ui()
        self.setStyleSheet(STYLESHEET)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        self.main_layout = QHBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)  # 紧凑边距
        self.main_layout.setSpacing(20)

        # === 左侧：核心计时器 (始终显示) ===
        left_panel = QVBoxLayout()
        left_panel.setSpacing(15)  # 紧凑间距

        # 1. 顶部模式
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        self.btn_focus = QPushButton("Focus")
        self.btn_break = QPushButton("Break")
        self.btn_focus.setCheckable(True)
        self.btn_break.setCheckable(True)
        self.btn_focus.setChecked(True)
        self.btn_focus.clicked.connect(lambda: self.set_mode("FOCUS"))
        self.btn_break.clicked.connect(lambda: self.set_mode("BREAK"))

        mode_layout.addStretch()
        mode_layout.addWidget(self.btn_focus)
        mode_layout.addWidget(self.btn_break)
        mode_layout.addStretch()
        left_panel.addLayout(mode_layout)

        # 2. 进度环
        ring_layout = QHBoxLayout()
        ring_layout.addStretch()
        self.ring = ProgressRing()
        ring_layout.addWidget(self.ring)
        ring_layout.addStretch()
        left_panel.addLayout(ring_layout)

        # 3. 预设时间
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(6)
        for m in [10, 20, 25]:
            btn = QPushButton(f"{m}m")
            btn.clicked.connect(lambda _, x=m: self.set_duration(x))
            presets_layout.addWidget(btn)

        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Min")
        self.custom_input.setFixedWidth(40)
        self.custom_input.setAlignment(Qt.AlignCenter)
        self.custom_input.returnPressed.connect(self.set_custom_time)
        presets_layout.addWidget(self.custom_input)

        preset_container = QHBoxLayout()
        preset_container.addStretch()
        preset_container.addLayout(presets_layout)
        preset_container.addStretch()
        left_panel.addLayout(preset_container)

        # 4. 核心控制 + 扩展按钮
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(10)

        self.btn_toggle = QPushButton("Start")
        self.btn_toggle.setObjectName("PrimaryBtn")
        self.btn_toggle.setFixedWidth(80)
        self.btn_toggle.clicked.connect(self.toggle_timer)

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.setFixedWidth(60)
        self.btn_reset.clicked.connect(self.reset_timer)

        # 扩展按钮
        self.btn_tasks = QPushButton("Tasks")
        self.btn_tasks.setCheckable(True)  # 可切换状态
        self.btn_tasks.setFixedWidth(60)
        self.btn_tasks.clicked.connect(self.toggle_workflow_panel)

        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.btn_toggle)
        ctrl_layout.addWidget(self.btn_reset)
        ctrl_layout.addWidget(self.btn_tasks)
        ctrl_layout.addStretch()
        left_panel.addLayout(ctrl_layout)

        # 5. AI 文字
        self.lbl_ai = QLabel("Ready to flow?")
        self.lbl_ai.setAlignment(Qt.AlignCenter)
        self.lbl_ai.setWordWrap(True)
        self.lbl_ai.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
        self.lbl_ai.setFixedHeight(30)
        left_panel.addWidget(self.lbl_ai)

        self.btn_ai_tip = QPushButton("⚡ Boost Me")
        self.btn_ai_tip.setObjectName("GhostBtn")
        self.btn_ai_tip.setCursor(Qt.PointingHandCursor)
        self.btn_ai_tip.clicked.connect(self.request_motivation)
        left_panel.addWidget(self.btn_ai_tip)

        self.main_layout.addLayout(left_panel)

        # === 右侧：Workflow Panel (默认隐藏) ===
        self.right_widget = QWidget()
        self.right_widget.setVisible(False)  # 初始隐藏

        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)  # 左侧留一点空隙
        right_layout.setSpacing(10)

        # 分割线
        self.line = QFrame()
        self.line.setFrameShape(QFrame.VLine)
        self.line.setStyleSheet(f"background-color: {COLORS['border']};")
        self.line.setVisible(False)

        # 标题
        r_title = QLabel("WORKFLOW ANCHOR")
        r_title.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: bold; font-size: 11px; letter-spacing: 1px;")
        right_layout.addWidget(r_title)

        # 输入
        input_box = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Add anchor task...")
        self.task_input.returnPressed.connect(self.add_task)
        input_box.addWidget(self.task_input)

        btn_add = QPushButton("+")
        btn_add.setFixedWidth(30)
        btn_add.clicked.connect(self.add_task)
        input_box.addWidget(btn_add)
        right_layout.addLayout(input_box)

        # 列表
        self.task_list = QListWidget()
        self.task_list.itemDoubleClicked.connect(self.activate_task)
        right_layout.addWidget(self.task_list)

        r_hint = QLabel("Double-click to set active.")
        r_hint.setStyleSheet("color: #64748b; font-size: 10px;")
        right_layout.addWidget(r_hint)

        self.main_layout.addWidget(self.line)
        self.main_layout.addWidget(self.right_widget, stretch=1)

    # --- 逻辑功能 ---

    def toggle_workflow_panel(self):
        show = self.btn_tasks.isChecked()
        self.right_widget.setVisible(show)
        self.line.setVisible(show)

        if show:
            self.resize(self.expanded_width, self.height_size)
            self.btn_tasks.setText("Hide")
        else:
            self.resize(self.compact_width, self.height_size)
            self.btn_tasks.setText("Tasks")

    def set_mode(self, mode):
        self.btn_focus.setChecked(mode == "FOCUS")
        self.btn_break.setChecked(mode == "BREAK")
        self.set_duration(25 if mode == "FOCUS" else 5)

    def set_duration(self, minutes):
        self.timer.stop()
        self.is_running = False
        self.total_time = minutes * 60
        self.time_left = self.total_time
        self.btn_toggle.setText("Start")
        self.ring.update_progress(self.time_left, self.total_time, False)

    def set_custom_time(self):
        try:
            val = int(self.custom_input.text())
            if val > 0: self.set_duration(val)
            self.custom_input.clear()
        except:
            pass

    def toggle_timer(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.btn_toggle.setText("Resume")
        else:
            self.timer.start(1000)
            self.is_running = True
            self.btn_toggle.setText("Pause")
        self.ring.update_progress(self.time_left, self.total_time, self.is_running)

    def reset_timer(self):
        self.set_duration(self.total_time // 60)
        self.lbl_ai.setText("Ready to flow?")

    def on_tick(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.ring.update_progress(self.time_left, self.total_time, True)
        else:
            self.timer.stop()
            self.is_running = False
            self.btn_toggle.setText("Start")
            self.ring.update_progress(0, self.total_time, False)
            QApplication.beep()
            self.on_complete()

    # --- 任务与 AI ---

    def add_task(self):
        text = self.task_input.text().strip()
        if text:
            self.task_list.addItem(text)
            self.task_input.clear()
            if self.task_list.count() == 1:
                self.activate_task(self.task_list.item(0))

    def activate_task(self, item):
        self.active_task_index = self.task_list.row(item)
        for i in range(self.task_list.count()):
            it = self.task_list.item(i)
            it.setBackground(QColor(COLORS['surface']) if i != self.active_task_index else QColor(COLORS['primary']))
            it.setForeground(QColor(COLORS['text_dim']) if i != self.active_task_index else QColor('white'))

    def on_complete(self):
        self.activateWindow()
        self.lbl_ai.setText("Thinking...")
        task = "Work"
        if self.active_task_index >= 0:
            task = self.task_list.item(self.active_task_index).text()

        self.worker = AIWorker(task, "break")
        self.worker.finished.connect(lambda t: self.lbl_ai.setText(t))
        self.worker.start()

    def request_motivation(self):
        self.lbl_ai.setText("Connecting to AI...")
        self.worker = AIWorker("", "tip")
        self.worker.finished.connect(lambda t: self.lbl_ai.setText(t))
        self.worker.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font_id = QFontDatabase.addApplicationFont("")
    app.setFont(QFont("Segoe UI", 9))

    window = FocusFlowWindow()
    window.show()
    sys.exit(app.exec())
