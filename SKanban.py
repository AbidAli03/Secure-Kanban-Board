import os
import sys
import csv
import xml.etree.ElementTree as ET
import xml.dom.minidom  

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QDialog,
    QLineEdit, QTextEdit, QFormLayout, QFrame, QScrollArea, QHBoxLayout, QMessageBox,
    QListWidget, QGridLayout, QSizePolicy, QSpinBox, QDateEdit, QFileDialog
)
from PyQt6.QtGui import QFont, QMouseEvent, QRegion, QPainterPath
from PyQt6.QtCore import Qt, QPoint, QTime, QTimer, QRectF, QPropertyAnimation, QEasingCurve, QDate, QRect
from xml.etree.ElementTree import Element, SubElement

import json
import bcrypt  # For secure password hashing

# File to store admin usernames and hashed passwords
ADMINS_FILE = "admin_users.json"

# Load admin data from JSON file
def load_admins():
    if not os.path.exists(ADMINS_FILE):
        return {}  # Return empty dict if file doesn't exist
    with open(ADMINS_FILE, "r") as f:
        return json.load(f)

# Save admin data back to JSON file
def save_admins(admins):
    with open(ADMINS_FILE, "w") as f:
        json.dump(admins, f)

# Register a new admin with hashed password
def register_admin(username, password):
    admins = load_admins()
    if username in admins:
        return False  # Cannot register duplicate usernames

    # Hash the password using bcrypt with a salt
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    admins[username] = hashed.decode("utf-8")  # Store as string
    save_admins(admins)
    return True

# Verify login credentials using bcrypt
def verify_admin(username, password):
    admins = load_admins()
    if username not in admins:
        return False
    # Check if password matches the stored hash
    return bcrypt.checkpw(password.encode("utf-8"), admins[username].encode("utf-8"))

# Check if any admin exists (for first-time setup)
def any_admin_exists():
    admins = load_admins()
    return len(admins) > 0


#pyqt login window
class AdminLoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin Login")
        self.setFixedSize(300, 220)

        #set background color
        self.setStyleSheet("QDialog { background-color: #f5f5f5; }")

        layout = QVBoxLayout(self)

        # Username input
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        layout.addWidget(self.username)

        # Password input (hidden characters)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Password")
        layout.addWidget(self.password)

        # Buttons layout
        button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.try_login)  # Connect login function
        button_layout.addWidget(self.login_button)

        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.try_register)  # Connect register function
        button_layout.addWidget(self.register_button)

        layout.addLayout(button_layout)

        # First-time setup: prompt user to register if no admins exist
        if not any_admin_exists():
            QMessageBox.information(self, "First Time Setup", "No admins exist. Please register one.")

    # Attempt login
    def try_login(self):
        user = self.username.text().strip()
        pw = self.password.text()
        if not verify_admin(user, pw):
            # Show warning if credentials invalid
            QMessageBox.warning(self, "Login Failed", "Invalid credentials")
        else:
            # Close dialog and accept login
            self.accept()

    # Attempt to register a new admin
    def try_register(self):
        user = self.username.text().strip()
        pw = self.password.text()
        if len(user) < 3 or len(pw) < 4:
            QMessageBox.warning(self, "Error", "Username or password too short")
            return

        if register_admin(user, pw):
            # Registration successful
            QMessageBox.information(self, "Success", f"Admin '{user}' registered.")
        else:
            # Username already exists
            QMessageBox.warning(self, "Error", "Username already exists")


class TaskDetailsPopup(QDialog):
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(350, 350)

        container = QWidget(self)
        container.setObjectName("container")
        container.setGeometry(0, 0, 350, 350)

        self.setStyleSheet("""
            #container {
                background-color: #6b21a8;
                border-radius: 15px;
            }
            QLineEdit, QTextEdit {
                background-color: #7c3aed;
                color: #ffffff;
                border: 1px solid #a855f7;
                border-radius: 4px;
                padding: 5px;
            }
            QLabel {
                color: white;
                background-color: transparent;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #c084fc;
            }
            QPushButton {
                background-color: #7e22ce;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #9333ea;
            }
            QCalendarWidget {
                background-color: white;
                color: #7c3aed;
            }
            QCalendarWidget QAbstractItemView {
                background-color: white;
                color: #7c3aed;
                selection-background-color: #7c3aed;
                selection-color: white;
            }
            QCalendarWidget QToolButton {
                background-color: white;
                color: #7c3aed;
                border: none;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #f3e8ff;
            }
            QCalendarWidget QWidget#qt_calendar_prevmonth,
            QCalendarWidget QWidget#qt_calendar_nextmonth {
                background-color: #7c3aed;
                color: white;
                border-radius: 15px;
                min-width: 30px;
                max-width: 30px;
                min-height: 30px;
                max-height: 30px;
            }
        """)

        self.task = task
        layout = QFormLayout()

        self.title_input = QLineEdit(self.task.title, self)
        self.assignee_input = QLineEdit(self.task.assignee, self)

        self.start_date_input = QDateEdit(self)
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(self.task.start_date if self.task.start_date else QDate.currentDate())

        self.end_date_input = QDateEdit(self)
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(self.task.end_date if self.task.end_date else QDate.currentDate())

        self.description_input = QTextEdit(self.task.description, self)

        layout.addRow("Title:", self.title_input)
        layout.addRow("Assignee:", self.assignee_input)
        layout.addRow("Start Date:", self.start_date_input)
        layout.addRow("End Date:", self.end_date_input)
        layout.addRow("Description:", self.description_input)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_task_details)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_task_details(self):
        changes = []

        if self.task.title != self.title_input.text():
            changes.append("Title")
        if self.task.assignee != self.assignee_input.text():
            changes.append("Assignee")
        if self.task.start_date != self.start_date_input.date():
            changes.append("Start Date")
        if self.task.end_date != self.end_date_input.date():
            changes.append("End Date")
        if self.task.description != self.description_input.toPlainText():
            changes.append("Description")

        self.task.title = self.title_input.text()
        self.task.assignee = self.assignee_input.text()
        self.task.start_date = self.start_date_input.date()
        self.task.end_date = self.end_date_input.date()
        self.task.description = self.description_input.toPlainText()

        self.task.setText(self.task.title)
        self.task.update_tooltip()

        if changes:
            if hasattr(self.task.kanban_window, "append_log_entry"):
                self.task.kanban_window.append_log_entry(
                    "Task Edited",
                    f"'{self.task.title}' fields changed: {', '.join(changes)}"
                )

        self.accept()


class Task(QLabel):
    def __init__(self, text, kanban_window, parent=None):
        super().__init__(text, parent)
        self.kanban_window = kanban_window
        self.setStyleSheet("""
            QLabel {
                background-color: #7c3aed;
                border: 2px solid #a855f7;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-family: "Segoe UI", "Roboto", sans-serif;
                color: #ffffff;
                transition: all 0.3s ease-in-out;
            }
            QLabel:hover {
                background-color: #9333ea;
                border-color: #c084fc;
            }
        """)
        self.setMinimumHeight(50)
        self.setMaximumHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.title = text
        self.assignee = ""
        self.start_date = QDate.currentDate()
        self.end_date = QDate.currentDate()
        self.description = ""
        self.update_tooltip()

        self.dragging = False
        self.offset = QPoint()
        self.click_start_time = None
        self.click_position = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.click_start_time = QTime.currentTime()
            self.click_position = event.pos()
            self.offset = event.pos()
            self.grabMouse()
        elif event.button() == Qt.MouseButton.RightButton:
            self.delete_task()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.open_details_popup()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.click_start_time is not None:
            if not self.dragging:
                if (event.pos() - self.click_position).manhattanLength() > 5:
                    self.dragging = True
                    self.original_parent = self.parent()

                    global_pos = self.mapToGlobal(QPoint(0, 0))
                    main_window_pos = self.kanban_window.mapFromGlobal(global_pos)

                    self.setParent(self.kanban_window)
                    self.move(main_window_pos)
                    self.show()

            if self.dragging:
                new_position = self.mapToParent(event.pos() - self.offset)
                self.move(new_position)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.click_start_time is not None:
                if self.dragging:
                    self.kanban_window.snap_to_column(self)
                self.dragging = False
                self.releaseMouse()
                self.click_start_time = None
                self.click_position = None

    def open_details_popup(self):
        popup = TaskDetailsPopup(self, self.kanban_window)
        popup.exec()

    def update_tooltip(self):
        days_remaining = ""
        if self.end_date and isinstance(self.end_date, QDate):
            today = QDate.currentDate()
            days_left = today.daysTo(self.end_date)
            if days_left >= 0:
                days_remaining = f"\nDays Remaining: {days_left} days"
            else:
                days_remaining = f"\nTask overdue by {-days_left} days!"

        self.setToolTip(
            f"Title: {self.title}\n"
            f"Assignee: {self.assignee}\n"
            f"Start Date: {self.start_date.toString('yyyy-MM-dd') if self.start_date else ''}\n"
            f"End Date: {self.end_date.toString('yyyy-MM-dd') if self.end_date else ''}"
            f"{days_remaining}\n"
            f"Description: {self.description}"
        )

    def delete_task(self):
        try:
            parent_widget = self.parent()
            self.kanban_window.append_log_entry("Task Deleted", f"'{self.title}' deleted")

            parent_layout = parent_widget.layout()
            if parent_layout:
                parent_layout.removeWidget(self)
                self.setParent(None)

                if hasattr(parent_widget, 'tasks'):
                    parent_widget.tasks.remove(self)

            column_widget = self
            while column_widget and not isinstance(column_widget, QFrame):
                column_widget = column_widget.parent()

            if column_widget and hasattr(column_widget, 'update_wip_display'):
                column_widget.update_wip_display()

            self.kanban_window.decrement_task_counter()
            self.deleteLater()

        except Exception as e:
            print(f"Error deleting task: {e}")

    def to_xml(self):
        task_element = Element("task")
        SubElement(task_element, "title").text = self.title
        SubElement(task_element, "assignee").text = self.assignee
        SubElement(task_element, "start_date").text = self.start_date.toString("yyyy-MM-dd")
        SubElement(task_element, "end_date").text = self.end_date.toString("yyyy-MM-dd")
        SubElement(task_element, "description").text = self.description
        return task_element

    @classmethod
    def from_xml(cls, xml_element, kanban_window, parent=None):
        title = xml_element.find("title").text
        task = cls(title, kanban_window, parent)
        task.assignee = xml_element.find("assignee").text
        start_date_str = xml_element.find("start_date").text
        if start_date_str:
            task.start_date = QDate.fromString(start_date_str, "yyyy-MM-dd")
        end_date_element = xml_element.find("end_date")
        if end_date_element is not None and end_date_element.text:
            task.end_date = QDate.fromString(end_date_element.text, "yyyy-MM-dd")
        task.description = xml_element.find("description").text
        task.update_tooltip()
        return task


class Column(QFrame):
    def __init__(self, title, parent_board):
        super().__init__()
        self.parent_board = parent_board
        self.title = title
        self.wip_limit = 0

        self.setStyleSheet("""
            QFrame {
                background-color: #581c87;
                border: 2px solid #6b21a8;
                border-radius: 8px;
                padding: 4px;
            }
            QFrame:hover {
                border: 2px solid #7e22ce;
            }
            QLabel {
                color: #E0E0E0;
            }
            QScrollBar:vertical {
                background: #f1f1f1;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #bdc3c7;
                min-height: 20px;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #6b21a8;
                color: #E0E0E0;
                border: 2px outset #7e22ce;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7e22ce;
                border: 2px inset #9333ea;
            }
            #wip-label {
                background-color: #581c87;
                color: #E0E0E0;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 4px;
            }
            QLineEdit {
                background-color: #6b21a8;
                color: #E0E0E0;
                border: 1px solid #7e22ce;
                border-radius: 4px;
                padding: 5px;
            }
            QTextEdit {
                background-color: #6b21a8;
                color: #E0E0E0;
                border: 1px solid #7e22ce;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(10)

        self.header_layout = QHBoxLayout()
        self.label = QLabel(title, self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            font-family: "Segoe UI", "Tahoma", sans-serif;
            padding: 5px;
            color: #E0E0E0;
        """)
        self.header_layout.addWidget(self.label)
        self.label.mouseDoubleClickEvent = self.label_double_clicked

        self.control_layout = QHBoxLayout()
        self.control_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.move_left_button = QPushButton("⇦")
        self.move_left_button.setFixedSize(40, 30)
        self.move_left_button.clicked.connect(self.move_left)
        self.control_layout.addWidget(self.move_left_button)

        self.move_right_button = QPushButton("⇨")
        self.move_right_button.setFixedSize(40, 30)
        self.move_right_button.clicked.connect(self.move_right)
        self.control_layout.addWidget(self.move_right_button)

        self.wip_label = QLabel("", self)
        self.wip_label.setObjectName("wip-label")
        self.control_layout.addWidget(self.wip_label)

        self.wip_button = QPushButton("WIP")
        self.wip_button.setFixedSize(40, 30)
        self.wip_button.clicked.connect(self.set_wip_limit)
        self.wip_button.setToolTip("Set WIP Limit")
        self.control_layout.addWidget(self.wip_button)

        if self.parent_board.is_Admin:
            self.delete_button = QPushButton("🗑")
            self.delete_button.setFixedSize(40, 30)
            self.delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #D32F2F;
                    border: 2px outset #F44336;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #F44336;
                    border: 2px inset #D32F2F;
                }
            """)
            self.delete_button.clicked.connect(self.delete_column)
            self.control_layout.addWidget(self.delete_button)

        self.layout.addLayout(self.header_layout)
        self.layout.addLayout(self.control_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")

        self.task_container = QWidget()
        self.task_container.setLayout(QVBoxLayout())
        self.task_container.layout().setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_container.layout().setSpacing(8)
        self.task_container.layout().setContentsMargins(5, 5, 5, 5)

        self.scroll_area.setWidget(self.task_container)
        self.layout.addWidget(self.scroll_area)

        if self.title == "To Do":
            self.move_left_button.setEnabled(False)
            self.move_right_button.setEnabled(False)

        self.update_wip_display()

    def set_wip_limit(self):
        if not self.parent_board.is_Admin:
            return

        dialog = QDialog(self)
        dialog.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        layout = QVBoxLayout(dialog)

        label = QLabel(f"Enter WIP limit for {self.title} column (0 = no limit):", dialog)
        layout.addWidget(label)

        spin_box = QSpinBox(dialog)
        spin_box.setValue(self.wip_limit)
        spin_box.setMinimum(0)
        spin_box.setMaximum(50)
        layout.addWidget(spin_box)

        ok_button = QPushButton("OK", dialog)
        layout.addWidget(ok_button)

        def on_ok():
            previous_limit = self.wip_limit
            self.wip_limit = spin_box.value()
            self.update_wip_display()
            if previous_limit == 0 and self.wip_limit > 0:
                self.parent_board.append_log_entry("WIP Limit Set",
                    f"WIP limit for '{self.title}' set to {self.wip_limit}")
            elif previous_limit != self.wip_limit:
                self.parent_board.append_log_entry("WIP Limit Changed",
                    f"WIP limit for '{self.title}' changed from {previous_limit} to {self.wip_limit}")
            dialog.accept()

        ok_button.clicked.connect(on_ok)
        dialog.exec()

    def update_wip_display(self):
        task_count = self.get_task_count()
        if self.parent_board.is_Admin:
            self.wip_label.hide()
            if self.wip_limit > 0:
                self.wip_button.setToolTip(f"WIP Limit: {self.wip_limit}")
            else:
                self.wip_button.setToolTip("Set WIP Limit")
        else:
            if self.wip_limit > 0:
                self.wip_label.show()
                self.wip_label.setText(f"{task_count}/{self.wip_limit}")
                color = "red" if task_count >= self.wip_limit else "#E0E0E0"
                self.wip_label.setStyleSheet(f"""
                    font-weight: bold;
                    font-size: 14px;
                    color: {color};
                    padding: 2px 6px;
                    background-color: #333;
                    border-radius: 4px;
                """)
            else:
                self.wip_label.hide()

    def get_task_count(self):
        count = 0
        for i in range(self.task_container.layout().count()):
            widget = self.task_container.layout().itemAt(i).widget()
            if isinstance(widget, Task):
                count += 1
        return count

    def remove_task(self, task):
            layout = self.task_container.layout()
            if layout.indexOf(task) != -1:
                layout.removeWidget(task)
                task.setParent(None)
                task.column = None
                layout.update()
                self.task_container.update()
                self.update()
                QApplication.processEvents()

            self.update_wip_display()

    def label_double_clicked(self, event):
        if self.title == "To Do":
            return
        self.edit_line = QLineEdit(self.label.text())
        self.edit_line.setStyleSheet("font-size: 16px; color: #E0E0E0;")
        self.layout.replaceWidget(self.label, self.edit_line)
        self.edit_line.setFocus()
        self.edit_line.editingFinished.connect(self.finish_edit_title)

    def finish_edit_title(self):
        old_title = self.title
        new_title = self.edit_line.text().strip()
        if new_title and new_title != old_title:
            if new_title.lower() == "to do":
                for col in self.parent_board.columns:
                    if col is not self and col.title.lower() == "to do":
                        QMessageBox.warning(
                            self,
                            "Cannot Rename",
                            "A 'To Do' column already exists. You cannot rename another column to 'To Do'."
                        )
                        self.layout.replaceWidget(self.edit_line, self.label)
                        self.edit_line.deleteLater()
                        return

            self.label.setText(new_title)
            self.title = new_title
            if hasattr(self.parent_board, "append_log_entry"):
                self.parent_board.append_log_entry(
                    "Column Renamed",
                    f"'{old_title}' renamed to '{new_title}'"
                )

        self.layout.replaceWidget(self.edit_line, self.label)
        self.edit_line.deleteLater()

    def move_left(self):
        current_idx = self.parent_board.columns.index(self)
        if current_idx > 1:
            self.parent_board.columns[current_idx], self.parent_board.columns[current_idx - 1] = \
                self.parent_board.columns[current_idx - 1], self.parent_board.columns[current_idx]
            self.parent_board.rearrange_columns()
            self.parent_board.append_log_entry("Column Moved", f"'{self.title}' moved left")

    def move_right(self):
        current_idx = self.parent_board.columns.index(self)
        if current_idx < len(self.parent_board.columns) - 1 and current_idx != 0:
            self.parent_board.columns[current_idx], self.parent_board.columns[current_idx + 1] = \
                self.parent_board.columns[current_idx + 1], self.parent_board.columns[current_idx]
            self.parent_board.rearrange_columns()
            self.parent_board.append_log_entry("Column Moved", f"'{self.title}' moved right")

    def delete_column(self):
        if not self.parent_board.is_Admin:
            QMessageBox.warning(self, "Permission Denied", "Only admins can delete columns.")
            return

        if self.title == "To Do":
            QMessageBox.warning(self, "Cannot Delete", "The 'To Do' column cannot be deleted.")
            return

        confirm = QMessageBox.question(
            self,
            "Delete Column",
            f"Are you sure you want to delete '{self.title}' column?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.parent_board.remove_column(self)
            self.parent_board.append_log_entry("Column Deleted", f"'{self.title}' column deleted")

    def add_task(self, task):
        if self.wip_limit > 0 and self.get_task_count() >= self.wip_limit:
            return False

        self.task_container.layout().addWidget(task)
        task.setParent(self.task_container)
        task.column = self
        self.update_wip_display()
        return True

    def get_task_position(self, task):
        for i in range(self.task_container.layout().count()):
            if self.task_container.layout().itemAt(i).widget() == task:
                return i
        return -1


class KanbanWindow(QMainWindow):
    def __init__(self, user_name="", is_Admin=False):
        super().__init__()
        self.setWindowTitle("Kanban Board")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(1200, 700)
        self.round_window()

        self.user_name = user_name
        self.is_Admin = is_Admin
        self.filename = f"{self.user_name}.xml"
        self.task_counter = 0
        self.max_tasks = 50
        self.columns = []

        self.button_style = """
            QPushButton {
                background-color: #6b21a8;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 8px 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7e22ce;
            }
            QPushButton:pressed {
                background-color: #581c87;
            }
        """

        self.main_layout = QVBoxLayout()
        self.add_column_button = QPushButton("Add Column")
        self.add_column_button.setVisible(self.is_Admin)
        self.add_column_button.clicked.connect(self.add_column)
        self.add_column_button.setStyleSheet(self.button_style)
        self.main_layout.addWidget(self.add_column_button)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.board_container = QWidget()
        self.board_layout = QGridLayout(self.board_container)
        self.board_layout.setSpacing(10)
        self.board_container.setLayout(self.board_layout)
        self.scroll_area.setWidget(self.board_container)
        self.main_layout.addWidget(self.scroll_area)

        bottom_layout = QHBoxLayout()

        if self.is_Admin:
            self.add_task_button = QPushButton("Add Task", self)
            self.add_task_button.setFont(QFont("Arial", 16))
            self.add_task_button.clicked.connect(self.create_task)
            self.add_task_button.setStyleSheet(self.button_style)
            bottom_layout.addWidget(self.add_task_button)

        role = "Admin" if self.is_Admin else "User"
        self.user_label = QLabel(f"Role: {role}\nProject: {self.user_name}", self)
        self.user_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        bottom_layout.addWidget(self.user_label)

        bottom_layout.addStretch()

        self.task_counter_label = QLabel("Tasks: 0/50", self)
        self.task_counter_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        bottom_layout.addWidget(self.task_counter_label)

        bottom_layout.addStretch()

        self.main_menu_button = QPushButton("Home", self)
        self.main_menu_button.setFont(QFont("Arial", 16))
        self.main_menu_button.clicked.connect(self.open_main_menu)
        self.main_menu_button.setStyleSheet(self.button_style)
        bottom_layout.addWidget(self.main_menu_button)

        self.save_button = QPushButton("Save", self)
        self.save_button.setFont(QFont("Arial", 16))
        self.save_button.clicked.connect(self.save_and_close)
        self.save_button.setStyleSheet(self.button_style)
        bottom_layout.addWidget(self.save_button)

        self.main_layout.addLayout(bottom_layout)

        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)
        self.setStyleSheet("background-color: white;")

        self.load_from_xml()

    def round_window(self, radius=20):
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.width(), self.height()), radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def showEvent(self, event):
        super().showEvent(event)
        self.center_window()

    def center_window(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y)

    def decrement_task_counter(self):
        self.task_counter -= 1
        self.task_counter_label.setText(f"Tasks: {self.task_counter}/50")

    def append_log_entry(self, action, details):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_folder = "Project Files"
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        log_path = os.path.join(log_folder, f"Log_{self.user_name}.csv")
        is_new_file = not os.path.exists(log_path)

        with open(log_path, "a", encoding="utf-8") as f:
            if is_new_file:
                f.write("timestamp,action,details\n")
            f.write(f"{timestamp},{action},{details}\n")

    def add_column(self, title=None):
        if not title or not isinstance(title, str):
            title = f"Column {len(self.columns) + 1}"
        if len(self.columns) >= 10:
            return

        column = Column(title, self)
        column.wip_button.setVisible(self.is_Admin)
        self.columns.append(column)
        self.rearrange_columns()
        self.append_log_entry("Column Created", f"'{title}' column added")

    def remove_column(self, column):
        task_layout = column.task_container.layout()
        task_count = sum(1 for i in range(task_layout.count())
                         if isinstance(task_layout.itemAt(i).widget(), Task))
        self.task_counter -= task_count
        self.task_counter_label.setText(f"Tasks: {self.task_counter}/50")
        self.columns.remove(column)
        column.setParent(None)
        self.rearrange_columns()
        self.append_log_entry("Column Removed", f"'{column.title}' column removed")

    def rearrange_columns(self):
        for i in reversed(range(self.board_layout.count())):
            self.board_layout.itemAt(i).widget().setParent(None)
        for index, column in enumerate(self.columns):
            row = index // 5
            col = index % 5
            self.board_layout.addWidget(column, row, col)
        self.adjust_column_sizes()

    def adjust_column_sizes(self):
        available_width = self.width() - 20
        column_count = len(self.columns)
        base_width = min(220, available_width // 5)
        extra_width = (5 - column_count) * 50 if column_count < 5 else 0
        column_width = min(300, base_width + extra_width)
        column_height = 540 if self.is_Admin else 600
        if len(self.columns) > 5:
            column_height = 275 if self.is_Admin else 300
        for column in self.columns:
            column.setFixedSize(column_width, column_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_column_sizes()

    def create_task(self):
        if self.task_counter >= self.max_tasks:
            return
        to_do_column = next((col for col in self.columns if col.title == "To Do"), None)
        if to_do_column:
            task = Task(f"Task {self.task_counter + 1}", self, to_do_column.task_container)
            self.append_log_entry("Task Created", f"'{task.title}' in column '{to_do_column.title}'")
            to_do_column.add_task(task)
            self.task_counter += 1
            self.task_counter_label.setText(f"Tasks: {self.task_counter}/50")
            to_do_column.update_wip_display()

    def snap_to_column(self, task):
            original_column = task.column
            original_index = -1
            if original_column:
                layout = original_column.task_container.layout()
                for i in range(layout.count()):
                  if layout.itemAt(i).widget() == task:
                     original_index = i
                     break

            closest_column = None
            task_rect = QRect(task.mapToGlobal(QPoint(0, 0)), task.size())
            for column in self.columns:
                column_rect = QRect(column.mapToGlobal(QPoint(0, 0)), column.size())
                if column_rect.intersects(task_rect):
                    closest_column = column
                    break

            if closest_column and closest_column != original_column:
                if original_column:
                    original_column.remove_task(task)

                if closest_column.add_task(task):
                    self.append_log_entry("Task Moved", f"'{task.title}' moved to '{closest_column.title}'")
                    return True
                else:
                    if original_column:
                       original_column.task_container.layout().insertWidget(original_index, task)
                       task.setParent(original_column.task_container)
                       task.column = original_column
                       task.show()
                       original_column.update_wip_display()
                    return False

            if original_column:
                original_column.task_container.layout().insertWidget(original_index, task)
                task.setParent(original_column.task_container)
                task.column = original_column
                task.show()
                original_column.update_wip_display()

            return False

    def save_to_xml(self):
        if not self.user_name:
            return
        folder_path = "Project Files"
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{self.user_name}.xml")
        root = ET.Element("kanban_board")
        for column in self.columns:
            column_element = ET.SubElement(root, "column", name=column.title, wip_limit=str(column.wip_limit))
            for i in range(column.task_container.layout().count()):
                task_widget = column.task_container.layout().itemAt(i).widget()
                if isinstance(task_widget, Task):
                    column_element.append(task_widget.to_xml())
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = xml.dom.minidom.parseString(rough_string)
        pretty_xml_as_string = reparsed.toprettyxml(indent="  ")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml_as_string)

    def load_from_xml(self):
        try:
            for column in self.columns[:]:
                self.remove_column(column)
            folder_path = "Project Files"
            file_path = os.path.join(folder_path, self.filename)
            tree = ET.parse(file_path)
            root = tree.getroot()
            for column_element in root.findall("column"):
                column_name = column_element.get("name")
                self.add_column(column_name)
                column = self.columns[-1]
                wip_limit_str = column_element.get("wip_limit", "0")
                try:
                    column.wip_limit = int(wip_limit_str)
                    column.update_wip_display()
                except ValueError:
                    column.wip_limit = 0
                column.wip_button.setVisible(self.is_Admin)
                for task_element in column_element.findall("task"):
                    task = Task.from_xml(task_element, self, column.task_container)
                    column.add_task(task)
                    self.task_counter += 1
            self.task_counter_label.setText(f"Tasks: {self.task_counter}/50")
        except FileNotFoundError:
            self.add_column("To Do")
            for column in self.columns:
                column.wip_button.setVisible(self.is_Admin)
        except ET.ParseError as e:
            QMessageBox.critical(self, "XML Error", f"Error parsing XML file: {e}")

    def save_and_close(self):
        self.save_to_xml()
        self.close()

    def open_main_menu(self):
        self.save_to_xml()
        self.close()
        self.main_menu = MainMenu()
        self.main_menu.show()


class LoadingScreen(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading...")
        self.setFixedSize(500, 300)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.container = QFrame(self)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #6b21a8;
                border-radius: 20px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
        """)
        self.container.setGeometry(0, 0, 500, 300)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(40, 40, 40, 40)

        self.label = QLabel("", self)
        self.label.setFont(QFont("Poppins", 36, QFont.Weight.Bold))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                color: white;
                padding: 10px;
            }
        """)
        layout.addWidget(self.label)

        self.text_to_display = "KANBAN"
        self.current_index = 0

        self.typing_timer = QTimer(self)
        self.typing_timer.timeout.connect(self.show_next_letter)
        self.typing_timer.start(150)

        self.animation = QPropertyAnimation(self.container, b"geometry")
        self.animation.setDuration(1000)
        self.animation.setStartValue(self.container.geometry())
        self.animation.setEndValue(self.container.geometry().adjusted(-5, -5, 5, 5))
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.setLoopCount(-1)
        self.animation.start()

    def show_next_letter(self):
        if self.current_index < len(self.text_to_display):
            self.label.setText(self.label.text() + self.text_to_display[self.current_index])
            self.current_index += 1
        else:
            self.typing_timer.stop()
            self.fade_out()

    def fade_out(self):
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(self.go_to_main_menu)
        self.fade_animation.start()

    def go_to_main_menu(self):
        self.close()
        self.main_menu = MainMenu()
        self.main_menu.show()


class MainMenu(QWidget):
    def __init__(self, saved_user_name=""):
        super().__init__()
        self.setWindowTitle("Kanban Board")
        self.setFixedSize(600, 400)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.user_name = saved_user_name
        self.saved_boards = self.load_saved_boards()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.container = QWidget(self)
        self.container.setGeometry(0, 0, 600, 400)
        self.container.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 20px;
                border: 2px solid rgba(107, 33, 168, 0.3);
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)

        button_style = """
            QPushButton {
                background-color: #6b21a8;
                color: white;
                border-radius: 15px;
                font-weight: bold;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background-color: #7e22ce;
                border: 2px solid rgba(255, 255, 255, 0.6);
            }
            QPushButton:pressed {
                background-color: #581c87;
            }
        """

        self.user_button = QPushButton("USER")
        self.user_button.setFont(QFont("Poppins", 18, QFont.Weight.Bold))
        self.user_button.setFixedSize(200, 60)
        self.user_button.setStyleSheet(button_style)
        self.user_button.clicked.connect(lambda: self.open_kanban("User"))
        layout.addWidget(self.user_button)

        self.admin_button = QPushButton("ADMIN")
        self.admin_button.setFont(QFont("Poppins", 18, QFont.Weight.Bold))
        self.admin_button.setFixedSize(200, 60)
        self.admin_button.setStyleSheet(button_style)
        self.admin_button.clicked.connect(lambda: self.open_kanban("Admin"))
        layout.addWidget(self.admin_button)

        self.animate_button(self.user_button)
        self.animate_button(self.admin_button)

    def animate_button(self, button):
        animation = QPropertyAnimation(button, b"geometry")
        animation.setDuration(1500)
        animation.setStartValue(button.geometry())
        animation.setEndValue(button.geometry().adjusted(-2, -2, 2, 2))
        animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        animation.setLoopCount(-1)
        animation.start()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def load_saved_boards(self):
        saved_boards = []
        folder_path = "Project Files"
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith(".xml"):
                    saved_boards.append(filename[:-4])
        saved_boards.sort()
        return saved_boards

    def open_kanban(self, user_type):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Select {'or Enter' if user_type == 'Admin' else ''} Name")
        dialog.setFixedSize(400, 300)
        dialog.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        container = QFrame(dialog)
        container.setStyleSheet("""
            QFrame {
                background-color: #6b21a8;
                border-radius: 20px;
                border: 2px solid rgba(255, 255, 255, 0.2);
            }
        """)
        container.setGeometry(0, 0, 400, 300)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        name_list = QListWidget(container)
        name_list.addItems(self.saved_boards)
        name_list.setStyleSheet("""
            QListWidget {
                background-color: #7c3aed;
                color: white;
                border: 1px solid white;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        layout.addWidget(name_list)

        name_input = None
        if user_type == "Admin":
            login_dialog = AdminLoginDialog(self)
            if login_dialog.exec() != QDialog.DialogCode.Accepted:
                return

            name_input = QLineEdit(container)
            name_input.setPlaceholderText("Enter project name here")
            name_input.setStyleSheet("""
                QLineEdit {
                    background-color: #7c3aed;
                    color: white;
                    border: 1px solid white;
                    border-radius: 10px;
                    padding: 6px;
                }
            """)
            layout.addWidget(name_input)

            delete_button = QPushButton("Delete Selected Project", container)
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #e11d48;
                    color: white;
                    border-radius: 8px;
                    padding: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #be123c;
                }
            """)
            delete_button.clicked.connect(lambda: self.delete_project(name_list))
            layout.addWidget(delete_button)

            downloads_layout = QHBoxLayout()

            download_button = QPushButton("Download Project", container)
            download_button.setStyleSheet("""
                QPushButton {
                    background-color: #22c55e;
                    color: white;
                    border-radius: 8px;
                    padding: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #16a34a;
                }
            """)
            download_button.clicked.connect(lambda: self.handle_download_project(name_list))
            downloads_layout.addWidget(download_button, stretch=1)

            downloads_layout.addStretch()

            log_download_button = QPushButton("Download Logs", container)
            log_download_button.setStyleSheet("""
                QPushButton {
                    background-color: #38bdf8;
                    color: white;
                    border-radius: 8px;
                    padding: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0ea5e9;
                }
            """)
            log_download_button.clicked.connect(lambda: self.handle_download_log(name_list))
            downloads_layout.addWidget(log_download_button, stretch=1)

            layout.addLayout(downloads_layout)

        ok_button = QPushButton("OK", container)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #a855f7;
                color: white;
                border: 2px solid white;
                border-radius: 8px;
                padding: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9333ea;
            }
        """)
        layout.addWidget(ok_button)

        if user_type == "Admin":
            ok_button.clicked.connect(lambda: self.handle_ok(dialog, name_list, user_type, name_input))
        else:
            ok_button.clicked.connect(lambda: self.handle_ok(dialog, name_list, user_type))

        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(container)
        dialog.setLayout(dialog_layout)

        parent_rect = self.frameGeometry()
        dialog_rect = dialog.frameGeometry()
        dialog_rect.moveCenter(parent_rect.center())
        dialog.move(dialog_rect.topLeft())

        dialog.exec()

    def handle_ok(self, dialog, name_list, user_type, name_input=None):
        selected_item = name_list.currentItem()
        entered_name = name_input.text().strip() if name_input else ""

        if user_type == "Admin":
            if entered_name:
                self.user_name = entered_name
                if entered_name not in self.saved_boards:
                    self.saved_boards.append(entered_name)
            elif selected_item:
                self.user_name = selected_item.text()
            else:
                self.show_message("Error", "Please enter or select a project name.", QMessageBox.Icon.Warning)
                return
        else:
            if selected_item:
                self.user_name = selected_item.text()
            else:
                self.show_message("Error", "Please select a project.", QMessageBox.Icon.Warning)
                return

        dialog.accept()
        current_pos = self.pos()
        self.close()
        is_Admin = user_type == "Admin"
        self.kanban_window = KanbanWindow(self.user_name, is_Admin)
        self.kanban_window.move(current_pos)
        self.kanban_window.show()

    def handle_download_project(self, name_list):
        selected_item = name_list.currentItem()
        if selected_item:
            self.download_project_file(selected_item.text())
        else:
            self.show_message("Error", "Please select a project to download.", QMessageBox.Icon.Warning)

    def handle_download_log(self, name_list):
        selected_item = name_list.currentItem()
        if selected_item:
            self.download_log_file(selected_item.text())
        else:
            self.show_message("Error", "Please select a project to download logs.", QMessageBox.Icon.Warning)

    def download_project_file(self, project_name):
        folder_path = os.path.abspath("Project Files")
        file_path = os.path.join(folder_path, f"{project_name}.xml")

        if not os.path.exists(file_path):
            self.show_message("Error", f"The file '{project_name}.xml' does not exist.", QMessageBox.Icon.Warning)
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Project As", f"{project_name}.xml",
                                                   "XML Files (*.xml);;All Files (*)")
        if save_path:
            try:
                import shutil
                shutil.copy(file_path, save_path)
                self.show_message("Success", f"Project saved as:\n{save_path}", QMessageBox.Icon.Information)
            except Exception as e:
                self.show_message("Error", f"Failed to save file: {e}", QMessageBox.Icon.Critical)

    def download_log_file(self, project_name):
        folder_path = os.path.abspath("Project Files")
        file_path = os.path.join(folder_path, f"Log_{project_name}.csv")

        if not os.path.exists(file_path):
            self.show_message("Error", f"The log file for '{project_name}' does not exist.", QMessageBox.Icon.Warning)
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Log As", f"Log_{project_name}.csv",
                                                   "CSV Files (*.csv);;All Files (*)")
        if save_path:
            try:
                import shutil
                shutil.copy(file_path, save_path)
                self.show_message("Success", f"Log saved as:\n{save_path}", QMessageBox.Icon.Information)
            except Exception as e:
                self.show_message("Error", f"Failed to save log file: {e}", QMessageBox.Icon.Critical)

    def delete_project(self, name_list):
        selected_item = name_list.currentItem()
        if selected_item:
            project_name = selected_item.text()
            folder_path = "Project Files"
            file_path = os.path.join(folder_path, f"{project_name}.xml")
            log_file_path = os.path.join(folder_path, f"Log_{project_name}.csv")

            confirm = QMessageBox.question(
                self,
                "Delete Confirmation",
                f"Are you sure you want to delete '{project_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)

                        from datetime import datetime
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        if os.path.exists(log_file_path):
                            with open(log_file_path, "a", encoding="utf-8") as log_file:
                                log_file.write(f"{timestamp},Project Deleted,Project '{project_name}' XML deleted\n")
                        else:
                            with open(log_file_path, "w", encoding="utf-8") as log_file:
                                log_file.write("timestamp,action,details\n")
                                log_file.write(f"{timestamp},Project Deleted,Project '{project_name}' XML deleted\n")

                    self.saved_boards.remove(project_name)
                    name_list.takeItem(name_list.row(selected_item))
                    self.show_message("Success", f"Deleted '{project_name}' (XML only, logs preserved)",
                                      QMessageBox.Icon.Information)
                except Exception as e:
                    self.show_message("Error", f"Deletion failed: {e}", QMessageBox.Icon.Critical)
        else:
            self.show_message("Error", "Please select a project to delete", QMessageBox.Icon.Warning)

    def show_message(self, title, message, icon):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #6b21a8;
                border-radius: 30px;
                padding: 10px;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
            }
            QMessageBox QPushButton {
                background-color: #a855f7;
                color: white;
                border-radius: 6px;
                padding: 5px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #9333ea;
            }
        """)
        msg.exec()


class KanbanApp(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.loading_screen = LoadingScreen()
        self.loading_screen.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMessageBox {
            background-color: #6b21a8;
            color: white;
            font-family: Poppins;
            font-size: 12px;
        }
        QMessageBox QPushButton {
            background-color: white;
            color: #6b21a8;
            border-radius: 8px;
            padding: 6px 10px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #eee;
        }
    """)
    kanban_app = KanbanApp(sys.argv)
    sys.exit(app.exec())

