from qasync import asyncSlot
from PyQt6.QtCore import QSortFilterProxyModel, QStringListModel, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QCompleter,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from structs.result import Result
from util.logger import CLogger
from util.task_manager import TaskManager

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class BottomComponent(QWidget):
    def __init__(self, manager: TaskManager):
        super().__init__()

        self.manager = manager

        # TODO:
        # Add comments to the right of the entry table
        # Chatbox
        # Scrollable
        self.entry_table = QTableWidget()
        self.entry_table.setColumnCount(3)
        self.entry_table.setRowCount(14)
        self.entry_table.setHorizontalHeaderLabels(
            ["Date", "Total Hours", "Over Time"])
        self.entry_table.setStyleSheet("border: 1px solid gray;")
        self.entry_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)

        self.title_1 = QLabel("Week 1", self)
        self.title_1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_1.setStyleSheet("font-size: 20px; padding: 10px;")

        # TODO:
        # 1. Make this it's own component
        # 2. Change the use of tables and just use labels.

        self.summary_1 = QTableWidget()
        self.summary_1.setColumnCount(2)
        self.summary_1.setRowCount(2)
        self.__add_cell_value(0, 0, "Sum of Hours", self.summary_1)
        self.__add_cell_value(1, 0, "Sum of OT", self.summary_1)
        self.summary_1.setStyleSheet("border: 1px solid gray;")
        self.summary_1.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)

        self.week_1 = QVBoxLayout()
        self.week_1.addWidget(self.title_1)
        self.week_1.addWidget(self.summary_1)

        self.title_2 = QLabel("Week 2", self)
        self.title_2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_2.setStyleSheet("font-size: 20px; padding: 10px;")

        # TODO:
        # 1. Make this it's own component
        # 2. Change the use of tables and just use labels.

        self.summary_2 = QTableWidget()
        self.summary_2.setColumnCount(2)
        self.summary_2.setRowCount(2)
        self.__add_cell_value(0, 0, "Sum of Hours", self.summary_2)
        self.__add_cell_value(1, 0, "Sum of OT", self.summary_2)
        self.summary_2.setStyleSheet("border: 1px solid gray;")
        self.summary_2.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)

        self.week_2 = QVBoxLayout()
        self.week_2.addWidget(self.title_2)
        self.week_2.addWidget(self.summary_2)

        self.summaries = QHBoxLayout()
        self.summaries.addLayout(self.week_1)
        self.summaries.addLayout(self.week_2)

        self.bottom_layout = QVBoxLayout()
        self.bottom_layout.addWidget(self.entry_table)
        self.bottom_layout.addLayout(self.summaries)

        self.setLayout(self.bottom_layout)

        self.manager.db_result.connect(
            lambda data: self.populate_table(data))
        self.manager.refresh.connect(self.refresh_table)

    @asyncSlot()
    async def populate_table(self, s):
        log.info("Populated Table: %s", s)

    def refresh_table(self):
        self.entry_table.update()
        self.summary_1.update()
        self.summary_2.update()

    def __add_cell_value(self, row: int, col: int, value: object, table: QTableWidget):
        try:
            item = QTableWidgetItem(str(value))
            table.setItem(row, col, item)

        except Exception as e:
            log.error("Failed to set cell (%d, %d): %s", row, col, str(e))
