from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QLabel,
    QWidget,
    QVBoxLayout,
    QScrollArea,
    QSizePolicy
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
        self.manager = manager

        self.status_box = QScrollArea()
        self.status_box.setWidgetResizable(True)
        self.status_box.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self.status_box.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        self.status_box.setFixedHeight(100)

        status_container = QWidget()
        self.status_feed = QVBoxLayout(status_container)
        self.status_feed.setSpacing(5)
        self.status_feed.setContentsMargins(0, 0, 0, 0)
        self.status_feed.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.status_box.setWidget(status_container)

        self.top_layout = QVBoxLayout()
        self.top_layout.addWidget(self.status_box)
        self.top_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(0)

        self.setLayout(self.top_layout)

        manager.started.connect(
            lambda message: self.add_status(f"{message}"))
        manager.refresh.connect(
            lambda message: self.add_status(f"{message}"))
        manager.done.connect(
            lambda message: self.add_status(f"{message}"))
        manager.error.connect(
            lambda err: self.add_status(f"Error: {err}"))

    def add_status(self, status: str):
        status_label = QLabel(status)
        status_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_feed.addWidget(status_label)

        QTimer.singleShot(2, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        self.scrollbar = self.status_box.verticalScrollBar()
        self.scrollbar.setValue(self.scrollbar.maximum())
