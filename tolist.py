import json
import os
import sys

from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QLabel, QPushButton, QListWidget,
                               QListWidgetItem, QLineEdit, QCheckBox, QGraphicsDropShadowEffect,
                               QComboBox, QMenu)

# ==========================================
# 🎨 样式表 (QSS) - Mac 风格 & Glassmorphism 模拟
# ==========================================
STYLESHEET = """
QMainWindow {
    background-color: transparent;
}
QWidget#CentralWidget {
    background-color: rgba(255, 255, 255, 240);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 100);
}
/* 侧边栏 */
QWidget#Sidebar {
    background-color: rgba(245, 245, 247, 200);
    border-top-left-radius: 12px;
    border-bottom-left-radius: 12px;
    border-right: 1px solid rgba(0, 0, 0, 15);
}
QPushButton#MenuButton {
    text-align: left;
    padding: 6px 10px;
    border-radius: 5px;
    color: #4a4a4a;
    background-color: transparent;
    font-size: 12px;
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
    border-top-right-radius: 12px;
    border-bottom-right-radius: 12px;
}
QLineEdit {
    border: 1px solid rgba(0, 0, 0, 20);
    border-radius: 6px;
    padding: 6px 10px;
    background-color: rgba(255, 255, 255, 180);
    font-size: 13px;
    color: #333;
}
QLineEdit:focus {
    border: 1px solid #007AFF;
    background-color: #fff;
}
/* 优先级下拉框 */
QComboBox {
    border: 1px solid rgba(0, 0, 0, 20);
    border-radius: 6px;
    padding: 5px 8px;
    background-color: rgba(255, 255, 255, 180);
    font-size: 12px;
    color: #333;
    min-width: 80px;
}
QComboBox:focus {
    border: 1px solid #007AFF;
    background-color: #fff;
}
QComboBox::drop-down {
    border: none;
    width: 18px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 3px solid transparent;
    border-right: 3px solid transparent;
    border-top: 4px solid #666;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    border: 1px solid rgba(0, 0, 0, 20);
    border-radius: 6px;
    background-color: white;
    selection-background-color: #007AFF;
    outline: none;
    padding: 3px;
}
/* 优先级旗帜按钮 */
QPushButton#FlagButton {
    border: none;
    border-radius: 3px;
    padding: 2px;
    font-size: 14px;
    background-color: transparent;
}
QPushButton#FlagButton:hover {
    background-color: rgba(0, 0, 0, 0.05);
}
/* 任务列表 */
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    background-color: rgba(255, 255, 255, 150);
    border-radius: 6px;
    margin-bottom: 4px;
    border: 1px solid rgba(255, 255, 255, 100);
    padding: 2px;
}
QListWidget::item:hover {
    background-color: rgba(255, 255, 255, 220);
}
QListWidget::item:selected {
    background-color: rgba(255, 255, 255, 255);
    border: 1px solid rgba(0, 0, 0, 10);
}
/* 滚动条 */
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 5px;
    margin: 0px; 
}
QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 0.1);
    min-height: 15px;
    border-radius: 2px;
}
/* 右键菜单 */
QMenu {
    background-color: white;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 6px;
    padding: 3px;
}
QMenu::item {
    padding: 5px 16px;
    border-radius: 3px;
}
QMenu::item:selected {
    background-color: #007AFF;
    color: white;
}
"""

# 优先级配置 - 使用旗帜图标
PRIORITY_CONFIG = {
    "high": {"label": "🚩 高优先级", "flag": "🚩", "color": "#FF3B30"},
    "medium": {"label": "🏳️ 中优先级", "flag": "🏳️", "color": "#FF9500"},
    "low": {"label": "🏴 低优先级", "flag": "🏴", "color": "#34C759"},
    "none": {"label": "⚐ 无优先级", "flag": "⚐", "color": "#CCCCCC"}
}


class DataManager:
    """简单的 JSON 数据管理"""
    FILE_NAME = "todos.json"

    @staticmethod
    def load_todos():
        if not os.path.exists(DataManager.FILE_NAME):
            return []
        try:
            with open(DataManager.FILE_NAME, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for i, task in enumerate(data):
                    if "priority" not in task:
                        task["priority"] = "none"
                    if "order" not in task:
                        task["order"] = i
                return data
        except:
            return []

    @staticmethod
    def save_todos(todos):
        with open(DataManager.FILE_NAME, 'w', encoding='utf-8') as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)


class TaskItemWidget(QWidget):
    """自定义的任务列表项 UI"""

    def __init__(self, text, is_completed, priority, on_toggle, on_delete, on_priority_change):
        super().__init__()
        self.priority = priority
        self.on_priority_change = on_priority_change

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(8)

        # 拖拽手柄
        self.drag_handle = QLabel("⋮⋮")
        self.drag_handle.setStyleSheet("color: #ddd; font-size: 13px; font-weight: bold;")
        self.drag_handle.setFixedWidth(16)
        self.drag_handle.setCursor(Qt.OpenHandCursor)

        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_completed)
        self.checkbox.stateChanged.connect(on_toggle)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator { 
                width: 16px; 
                height: 16px; 
                border-radius: 4px; 
                border: 1px solid #ccc; 
                background: white; 
            }
            QCheckBox::indicator:checked { 
                background-color: #007AFF; 
                border-color: #007AFF; 
            }
        """)

        # Label
        self.label = QLabel(text)
        font = QFont("Segoe UI", 9)
        self.label.setFont(font)
        self.update_style(is_completed)

        # 优先级旗帜按钮（放在右侧）
        self.flag_btn = QPushButton(PRIORITY_CONFIG[priority]["flag"])
        self.flag_btn.setObjectName("FlagButton")
        self.flag_btn.setFixedSize(24, 24)
        self.flag_btn.setCursor(Qt.PointingHandCursor)
        self.flag_btn.setToolTip(PRIORITY_CONFIG[priority]["label"])
        self.flag_btn.clicked.connect(self.show_priority_menu)

        # Delete Button
        self.del_btn = QPushButton("✕")
        self.del_btn.setFixedSize(20, 20)
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setStyleSheet("""
            QPushButton { 
                border-radius: 3px; 
                color: #bbb; 
                background: transparent; 
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { 
                color: #ff3b30; 
                background: rgba(255, 59, 48, 0.1); 
            }
        """)
        self.del_btn.clicked.connect(on_delete)

        layout.addWidget(self.drag_handle)
        layout.addWidget(self.checkbox)
        layout.addWidget(self.label, 1)  # 让文字占据剩余空间
        layout.addWidget(self.flag_btn)
        layout.addWidget(self.del_btn)

    def show_priority_menu(self):
        """显示优先级选择菜单"""
        menu = QMenu(self)

        for key in ["high", "medium", "low", "none"]:
            action = menu.addAction(PRIORITY_CONFIG[key]["label"])
            action.triggered.connect(lambda checked=False, k=key: self.change_priority(k))

        # 在按钮下方显示菜单
        pos = self.flag_btn.mapToGlobal(QPoint(0, self.flag_btn.height()))
        menu.exec(pos)

    def change_priority(self, new_priority):
        """改变优先级"""
        self.priority = new_priority
        self.flag_btn.setText(PRIORITY_CONFIG[new_priority]["flag"])
        self.flag_btn.setToolTip(PRIORITY_CONFIG[new_priority]["label"])
        if self.on_priority_change:
            self.on_priority_change(new_priority)

    def update_style(self, completed):
        if completed:
            self.label.setStyleSheet("color: #aaa; text-decoration: line-through;")
        else:
            self.label.setStyleSheet("color: #333; text-decoration: none;")


class DraggableListWidget(QListWidget):
    """支持拖拽排序的列表控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def dropEvent(self, event):
        """处理拖放事件"""
        super().dropEvent(event)
        main_window = self.get_main_window()
        if main_window:
            main_window.update_task_order()

    def get_main_window(self):
        """获取主窗口引用"""
        widget = self.parent()
        while widget:
            if isinstance(widget, MainWindow):
                return widget
            widget = widget.parent()
        return None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ZenDo")
        self.resize(680, 480)
        self.setMinimumSize(500, 350)  # 设置最小尺寸

        # 无边框窗口设置
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 数据初始化
        self.todos = DataManager.load_todos()
        self.current_filter = "all"

        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        # 主容器
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)

        # 阴影效果
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        self.central_widget.setGraphicsEffect(shadow)

        # 主布局
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # --- 侧边栏 ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(160)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(12, 15, 12, 15)

        # 窗口控制按钮 (红绿灯)
        self.controls_layout = QHBoxLayout()
        self.controls_layout.setSpacing(6)
        self.controls_layout.setAlignment(Qt.AlignLeft)
        for color, callback in [("#FF5F56", self.close), ("#FFBD2E", self.showMinimized),
                                ("#27C93F", self.toggleMaximized)]:
            btn = QPushButton()
            btn.setFixedSize(10, 10)
            btn.setStyleSheet(f"background-color: {color}; border-radius: 5px; border: none;")
            btn.setCursor(Qt.PointingHandCursor)
            if callback == self.close:
                btn.clicked.connect(self.close)
            elif callback == self.showMinimized:
                btn.clicked.connect(self.showMinimized)
            else:
                btn.clicked.connect(callback)
            self.controls_layout.addWidget(btn)

        self.sidebar_layout.addLayout(self.controls_layout)
        self.sidebar_layout.addSpacing(20)

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

        self.menu_buttons["all"].setChecked(True)
        self.sidebar_layout.addStretch()

        # 用户信息 (底部)
        user_label = QLabel("👤  John Doe")
        user_label.setStyleSheet("color: #888; font-size: 11px; font-weight: bold; padding-left: 4px;")
        self.sidebar_layout.addWidget(user_label)

        # --- 内容区 ---
        self.content = QWidget()
        self.content.setObjectName("ContentArea")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        self.title_label = QLabel("All Tasks")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333; margin-bottom: 3px;")
        self.date_label = QLabel("Overview • Drag to reorder")
        self.date_label.setStyleSheet("font-size: 11px; color: #999; margin-bottom: 12px;")

        # 使用可拖拽的列表
        self.list_widget = DraggableListWidget(self.content)
        self.list_widget.setFocusPolicy(Qt.NoFocus)

        # 输入框和优先级选择
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Add a task...")
        self.input_box.returnPressed.connect(self.add_task)

        self.priority_input = QComboBox()
        for key in ["none", "low", "medium", "high"]:
            self.priority_input.addItem(PRIORITY_CONFIG[key]["flag"] + " " + key.capitalize(), key)
        self.priority_input.setCurrentIndex(0)

        input_layout.addWidget(self.input_box, 1)
        input_layout.addWidget(self.priority_input)

        self.content_layout.addWidget(self.title_label)
        self.content_layout.addWidget(self.date_label)
        self.content_layout.addWidget(self.list_widget)
        self.content_layout.addLayout(input_layout)

        # 添加到主布局
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content)

        # 拖拽移动窗口支持
        self._drag_pos = QPoint()
        self._is_maximized = False

    def toggleMaximized(self):
        """切换最大化状态"""
        if self._is_maximized:
            self.showNormal()
            self._is_maximized = False
        else:
            self.showMaximized()
            self._is_maximized = True

    def change_view(self, view_key):
        self.current_filter = view_key
        for k, btn in self.menu_buttons.items():
            btn.setChecked(k == view_key)

        titles = {"all": "All Tasks", "today": "Today", "completed": "Completed"}
        self.title_label.setText(titles.get(view_key, "Tasks"))
        self.refresh_list()

    def add_task(self):
        text = self.input_box.text().strip()
        if not text: return

        new_task = {
            "text": text,
            "completed": False,
            "category": "all",
            "priority": self.priority_input.currentData(),
            "order": len(self.todos)
        }
        self.todos.append(new_task)
        DataManager.save_todos(self.todos)
        self.input_box.clear()
        self.priority_input.setCurrentIndex(0)
        self.refresh_list()

    def toggle_task(self, item_widget, task_data):
        task_data["completed"] = item_widget.checkbox.isChecked()
        item_widget.update_style(task_data["completed"])
        DataManager.save_todos(self.todos)
        if self.current_filter == "completed" and not task_data["completed"]:
            self.refresh_list()

    def change_priority(self, task_data, new_priority):
        task_data["priority"] = new_priority
        DataManager.save_todos(self.todos)

    def delete_task(self, task_data):
        if task_data in self.todos:
            self.todos.remove(task_data)
            DataManager.save_todos(self.todos)
            self.refresh_list()

    def update_task_order(self):
        """更新任务顺序（拖拽后调用）"""
        task_map = {}
        for task in self.todos:
            key = (task["text"], task["completed"], task.get("priority", "none"))
            task_map[key] = task

        new_order = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                key = (widget.label.text(), widget.checkbox.isChecked(), widget.priority)
                if key in task_map:
                    task = task_map[key]
                    task["order"] = i
                    new_order.append(task)

        displayed_tasks = set(id(t) for t in new_order)
        for task in self.todos:
            if id(task) not in displayed_tasks:
                new_order.append(task)

        self.todos = new_order
        DataManager.save_todos(self.todos)

    def refresh_list(self):
        self.list_widget.clear()

        filtered_data = []
        if self.current_filter == "all":
            filtered_data = [t for t in self.todos if not t["completed"]]
        elif self.current_filter == "completed":
            filtered_data = [t for t in self.todos if t["completed"]]
        elif self.current_filter == "today":
            filtered_data = [t for t in self.todos if not t["completed"]]

        filtered_data.sort(key=lambda x: x.get("order", 0))

        for task in filtered_data:
            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(QSize(0, 38))

            widget = TaskItemWidget(
                task["text"],
                task["completed"],
                task.get("priority", "none"),
                lambda state, t=task: None,
                lambda t=task: self.delete_task(t),
                lambda priority, t=task: self.change_priority(t, priority)
            )

            widget.checkbox.stateChanged.disconnect()
            widget.checkbox.stateChanged.connect(lambda state, w=widget, t=task: self.toggle_task(w, t))

            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    # --- 窗口拖拽和调整大小逻辑 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._is_maximized:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())