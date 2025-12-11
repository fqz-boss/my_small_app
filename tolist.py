import json
import os
import sys

from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QListWidget,
                               QListWidgetItem, QLineEdit, QCheckBox, QGraphicsDropShadowEffect)

# ==========================================
# 🎨 样式表 (QSS) - Mac 风格 & Glassmorphism 模拟
# ==========================================
STYLESHEET = """
QMainWindow {
    background-color: transparent;
}
QWidget#CentralWidget {
    background-color: rgba(255, 255, 255, 240);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 100);
}
/* 侧边栏 */
QWidget#Sidebar {
    background-color: rgba(245, 245, 247, 200);
    border-top-left-radius: 16px;
    border-bottom-left-radius: 16px;
    border-right: 1px solid rgba(0, 0, 0, 15);
}
QPushButton#MenuButton {
    text-align: left;
    padding: 8px 12px;
    border-radius: 6px;
    color: #4a4a4a;
    background-color: transparent;
    font-size: 13px;
    border: none;
}
QPushButton#MenuButton:hover {
    background-color: rgba(0, 0, 0, 10);
}
QPushButton#MenuButton:checked {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid rgba(0,0,0,5);
}
/* 主内容区 */
QWidget#ContentArea {
    background-color: transparent;
    border-top-right-radius: 16px;
    border-bottom-right-radius: 16px;
}
QLineEdit {
    border: 1px solid rgba(0, 0, 0, 20);
    border-radius: 8px;
    padding: 8px 12px;
    background-color: rgba(255, 255, 255, 180);
    font-size: 14px;
    color: #333;
}
QLineEdit:focus {
    border: 1px solid #007AFF;
    background-color: #fff;
}
/* 任务列表 */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    background-color: rgba(255, 255, 255, 150);
    border-radius: 8px;
    margin-bottom: 6px;
    border: 1px solid rgba(255, 255, 255, 100);
    padding: 4px;
}
QListWidget::item:hover {
    background-color: rgba(255, 255, 255, 220);
}
QListWidget::item:selected {
    background-color: rgba(255, 255, 255, 255);
    border: 1px solid rgba(0, 0, 0, 10);
}
/* 滚动条隐藏 */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 6px;
    margin: 0px; 
}
QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 0.1);
    min-height: 20px;
    border-radius: 3px;
}
"""


class DataManager:
    """简单的 JSON 数据管理"""
    FILE_NAME = "todos.json"

    @staticmethod
    def load_todos():
        if not os.path.exists(DataManager.FILE_NAME):
            return []
        try:
            with open(DataManager.FILE_NAME, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    @staticmethod
    def save_todos(todos):
        with open(DataManager.FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)


class TaskItemWidget(QWidget):
    """自定义的任务列表项 UI"""

    def __init__(self, text, is_completed, on_toggle, on_delete):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_completed)
        self.checkbox.stateChanged.connect(on_toggle)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 5px; border: 1px solid #ccc; background: white; }
            QCheckBox::indicator:checked { background-color: #007AFF; border-color: #007AFF; image: url(none); }
        """)

        # Label
        self.label = QLabel(text)
        font = QFont("Segoe UI", 10)
        self.label.setFont(font)
        self.update_style(is_completed)

        # Delete Button (Hidden by default, shown on hover conceptually)
        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(24, 24)
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setStyleSheet("""
            QPushButton { border-radius: 4px; color: #aaa; background: transparent; font-weight: bold; }
            QPushButton:hover { color: #ff3b30; background: rgba(255, 59, 48, 0.1); }
        """)
        self.del_btn.clicked.connect(on_delete)

        layout.addWidget(self.checkbox)
        layout.addWidget(self.label, 1)  # 1 = stretch
        layout.addWidget(self.del_btn)

    def update_style(self, completed):
        if completed:
            self.label.setStyleSheet("color: #aaa; text-decoration: line-through;")
        else:
            self.label.setStyleSheet("color: #333; text-decoration: none;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZenDo")
        self.resize(900, 650)

        # 无边框窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 数据初始化
        self.todos = DataManager.load_todos()
        self.current_filter = "all"  # all, today, flagged, completed

        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        # 主容器
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        self.central_widget.setGraphicsEffect(shadow)

        # 主布局
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- 侧边栏 ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(16, 20, 16, 20)

        # 窗口控制按钮 (红绿灯)
        self.controls_layout = QHBoxLayout()
        self.controls_layout.setSpacing(8)
        self.controls_layout.setAlignment(Qt.AlignLeft)
        for color, callback in [("#FF5F56", self.close), ("#FFBD2E", self.showMinimized),
                                ("#27C93F", self.showMaximized)]:
            btn = QPushButton()
            btn.setFixedSize(12, 12)
            btn.setStyleSheet(f"background-color: {color}; border-radius: 6px; border: none;")
            if callback == self.close:
                btn.clicked.connect(self.close)
            elif callback == self.showMinimized:
                btn.clicked.connect(self.showMinimized)
            self.controls_layout.addWidget(btn)

        self.sidebar_layout.addLayout(self.controls_layout)
        self.sidebar_layout.addSpacing(30)

        # 菜单按钮
        self.menu_buttons = {}
        menus = [("All Tasks", "all"), ("Today", "today"), ("Completed", "completed")]
        for label, key in menus:
            btn = QPushButton(label)
            btn.setObjectName("MenuButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self.change_view(k))
            self.sidebar_layout.addWidget(btn)
            self.menu_buttons[key] = btn

        self.menu_buttons["all"].setChecked(True)  # 默认选中
        self.sidebar_layout.addStretch()

        # 用户信息 (底部)
        user_label = QLabel("👤  John Doe")
        user_label.setStyleSheet("color: #888; font-size: 12px; font-weight: bold; padding-left: 5px;")
        self.sidebar_layout.addWidget(user_label)

        # --- 内容区 ---
        self.content = QWidget()
        self.content.setObjectName("ContentArea")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        self.title_label = QLabel("All Tasks")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 5px;")
        self.date_label = QLabel("Overview")
        self.date_label.setStyleSheet("font-size: 13px; color: #999; margin-bottom: 20px;")

        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setFocusPolicy(Qt.NoFocus)  # 去除选中虚线框

        # 输入框
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Add a task...")
        self.input_box.returnPressed.connect(self.add_task)

        self.content_layout.addWidget(self.title_label)
        self.content_layout.addWidget(self.date_label)
        self.content_layout.addWidget(self.list_widget)
        self.content_layout.addWidget(self.input_box)

        # 添加到主布局
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content)

        # 拖拽移动窗口支持
        self._drag_pos = QPoint()

    def change_view(self, view_key):
        self.current_filter = view_key
        # 更新按钮状态
        for k, btn in self.menu_buttons.items():
            btn.setChecked(k == view_key)

        # 更新标题
        titles = {"all": "All Tasks", "today": "Today", "completed": "Completed"}
        self.title_label.setText(titles.get(view_key, "Tasks"))
        self.refresh_list()

    def add_task(self):
        text = self.input_box.text().strip()
        if not text: return

        new_task = {
            "text": text,
            "completed": False,
            "category": "all"  # 简化处理
        }
        self.todos.append(new_task)
        DataManager.save_todos(self.todos)
        self.input_box.clear()
        self.refresh_list()

    def toggle_task(self, item_widget, task_data):
        task_data["completed"] = item_widget.checkbox.isChecked()
        item_widget.update_style(task_data["completed"])
        DataManager.save_todos(self.todos)
        # 如果在 Completed 视图或 All 视图，可能需要刷新，但为了动画流畅暂不强制刷新列表
        if self.current_filter == "completed" and not task_data["completed"]:
            self.refresh_list()

    def delete_task(self, task_data):
        if task_data in self.todos:
            self.todos.remove(task_data)
            DataManager.save_todos(self.todos)
            self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()

        filtered_data = []
        if self.current_filter == "all":
            filtered_data = [t for t in self.todos if not t["completed"]]
        elif self.current_filter == "completed":
            filtered_data = [t for t in self.todos if t["completed"]]
        elif self.current_filter == "today":
            filtered_data = [t for t in self.todos if not t["completed"]]  # 简化模拟

        for task in filtered_data:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 50))  # 设置行高

            # 创建自定义 Widget
            widget = TaskItemWidget(
                task["text"],
                task["completed"],
                lambda state, t=task: self.toggle_task_wrapper(state, t),  # 延迟绑定
                lambda t=task: self.delete_task(t)
            )
            # 修正闭包问题：我们需要重新绑定 widget 实例以便在 toggle 时调用
            widget.checkbox.stateChanged.disconnect()
            widget.checkbox.stateChanged.connect(lambda state, w=widget, t=task: self.toggle_task(w, t))

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    # --- 窗口拖拽逻辑 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))  # 设置全局字体
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
