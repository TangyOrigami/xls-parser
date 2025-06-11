from datetime import datetime, timedelta

from qasync import asyncSlot
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from structs.exceptions import NoWorkEntries
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

        self.week_1_title = QLabel("Week 1", self)
        self.week_1_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.week_1_title.setStyleSheet("font-size: 20px; padding: 10px;")

        # TODO:
        # 1. Make this it's own component
        # 2. Change the use of tables and just use labels.

        self.value_1 = QLabel("")
        self.week_1_total = QHBoxLayout()
        self.week_1_total.addWidget(QLabel("Sum of Hours:"))
        self.week_1_total.addWidget(self.value_1)

        self.value_2 = QLabel("")
        self.week_1_ot_total = QHBoxLayout()
        self.week_1_ot_total.addWidget(QLabel("Sum of OT:"))
        self.week_1_ot_total.addWidget(self.value_2)

        self.week_1 = QVBoxLayout()
        self.week_1.addWidget(self.week_1_title)
        self.week_1.addLayout(self.week_1_total)
        self.week_1.addLayout(self.week_1_ot_total)

        self.week_2_title = QLabel("Week 2", self)
        self.week_2_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.week_2_title.setStyleSheet("font-size: 20px; padding: 10px;")

        # TODO:
        # 1. Make this it's own component
        # 2. Change the use of tables and just use labels.

        self.value_3 = QLabel("")
        self.week_2_total = QHBoxLayout()
        self.week_2_total.addWidget(QLabel("Sum of Hours:"))
        self.week_2_total.addWidget(self.value_3)

        self.value_4 = QLabel("")
        self.week_2_ot_total = QHBoxLayout()
        self.week_2_ot_total.addWidget(QLabel("Sum of OT:"))
        self.week_2_ot_total.addWidget(self.value_4)

        self.week_2 = QVBoxLayout()
        self.week_2.addWidget(self.week_2_title)
        self.week_2.addLayout(self.week_2_total)
        self.week_2.addLayout(self.week_2_ot_total)

        self.summaries = QHBoxLayout()
        self.summaries.addLayout(self.week_1)
        self.summaries.addLayout(self.week_2)

        self.entry_table = QTableWidget()
        self.entry_table.setColumnCount(3)
        self.entry_table.setRowCount(14)
        self.entry_table.setHorizontalHeaderLabels(
            ["Date", "Total Hours", "Over Time"])
        self.entry_table.setStyleSheet("border: 1px solid gray;")
        self.entry_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)

        self.comment_table = QTableWidget()
        self.comment_table.setColumnCount(4)
        self.comment_table.setRowCount(14)
        self.comment_table.setHorizontalHeaderLabels(
            ["Date", "Punch In", "Punch Out", "Special Pay"])
        self.comment_table.setStyleSheet("border: 1px solid gray;")
        self.comment_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)

        self.main_tables = QHBoxLayout()
        self.main_tables.addWidget(self.entry_table)
        self.main_tables.addWidget(self.comment_table)

        self.bottom_layout = QVBoxLayout()
        self.bottom_layout.addLayout(self.summaries)
        self.bottom_layout.addLayout(self.main_tables)

        self.setLayout(self.bottom_layout)

        self.manager.db_work_entry.connect(
            lambda data: self.populate_table(data))
        self.manager.init_summary.connect(self.populate_summaries)

    @asyncSlot()
    async def populate_table(self, data: list[list[tuple, ...], str]):
        work_entries = data[0]
        self.entry_table.clearContents()

        for row in range(len(work_entries)):
            self.__add_cell_value(
                row=row,
                col=0,
                value=work_entries[row][0],
                table=self.entry_table
            )

            self.__add_cell_value(
                row=row,
                col=1,
                value=work_entries[row][1],
                table=self.entry_table
            )

        try:
            date_obj = datetime.strptime(data[1], "%Y-%m-%d").date()

            dates = {}

            if not work_entries:
                raise NoWorkEntries()

            # Fill in Dates in Pay Period

            for i in range(14):
                curr_date = date_obj + timedelta(i)

                self.__add_cell_value(
                    row=i,
                    col=0,
                    value=curr_date,
                    table=self.entry_table
                )

                dates.update({i: str(curr_date)})

            # Fill Work Entries and Overtime Earned

            for entry in work_entries:
                if entry[0] in dates.values():
                    date_key = self.__get_key_from_value(
                        dictionary=dates, value=entry[0])[0]

                    self.__add_cell_value(
                        row=date_key,
                        col=1,
                        value=float(entry[1]),
                        table=self.entry_table
                    )

                    self.__add_cell_value(
                        row=date_key,
                        col=2,
                        value=entry[1]-8,
                        table=self.entry_table
                    )

                del dates[date_key]

            # Fill Empty Work Entries

            for key, value in dates.items():
                self.__add_cell_value(
                    row=key,
                    col=1,
                    value=0.0,
                    table=self.entry_table
                )

                self.__add_cell_value(
                    row=key,
                    col=2,
                    value=0.0,
                    table=self.entry_table
                )

        except NoWorkEntries:
            for i in range(14):
                curr_date = date_obj + timedelta(i)
                self.__add_cell_value(
                    row=i,
                    col=0,
                    value=curr_date,
                    table=self.entry_table)

                self.__add_cell_value(
                    row=i,
                    col=1,
                    value=0.0,
                    table=self.entry_table
                )

                self.__add_cell_value(
                    row=i,
                    col=2,
                    value=0.0,
                    table=self.entry_table
                )

        except Exception as e:
            log.error("Failed to populate table: %s", str(e))

        except KeyError as e:
            log.error("KeyError: %s", str(e))

        finally:
            self.manager.start_init_summary()

    def populate_summaries(self):
        rows = self.entry_table.rowCount()

        total_1 = 0
        total_ot_1 = 0
        total_2 = 0
        total_ot_2 = 0

        for row in range(rows):
            if row <= 6:
                item = self.entry_table.item(row, 1)
                if item:
                    total_1 += float(item.text())

                item = self.entry_table.item(row, 2)
                if item:
                    total_ot_1 += float(item.text())
            else:
                item = self.entry_table.item(row, 1)
                if item:
                    total_2 += float(item.text())

                item = self.entry_table.item(row, 2)
                if item:
                    total_ot_2 += float(item.text())

        self.value_1.setText(str(total_1))
        self.value_2.setText(str(total_ot_1))
        self.value_3.setText(str(total_2))
        self.value_4.setText(str(total_ot_2))

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

    @staticmethod
    def __get_key_from_value(dictionary: dict, value: any):
        return [key for key, val in dictionary.items() if val == value]
