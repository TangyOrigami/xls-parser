from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
)

from structs.result import Result
from util.logger import CLogger
from util.task_manager import TaskManager

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class TopComponent(QWidget):
    def __init__(self, manager: TaskManager):
        super().__init__()
        self.title_label = QLabel("Pay Period", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; padding: 10px;")

        # TODO:
        # Float left
        # Chatbox
        # Scrollable
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.top_layout = QVBoxLayout()
        self.top_layout.addWidget(self.title_label)
        self.top_layout.addWidget(self.status_label)

        self.setLayout(self.top_layout)

        manager.started.connect(
            lambda message: self.status_label.setText(f"{message}"))
        manager.done.connect(
            lambda message: self.status_label.setText(f"{message}"))
        manager.error.connect(
            lambda err: self.status_label.setText(f"Error: {err}"))
