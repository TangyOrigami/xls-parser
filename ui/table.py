import os
import re
from datetime import datetime, timedelta

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

from structs.exceptions import NoWorkEntries
from structs.result import Result
from util.async_db import AsyncDBInterface
from util.logger import CLogger
from util.pay_period_manager import PayPeriodManager

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class TableWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.pp_manager = PayPeriodManager()

        self.title_label = QLabel("Pay Period", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; padding: 10px;")

        self.ppd = QComboBox()
        self.ppd.setEditable(True)
        self.ppd.currentTextChanged.connect(self.ppd_choice)

        self.employee = QComboBox()
        self.employee.setEditable(True)
        self.employee.currentTextChanged.connect(self.employee_choice)

        self.refresh = QPushButton("Refresh")
        self.refresh.clicked.connect(self.refresh_choice)

        self.info_section = QHBoxLayout()
        self.info_section.addWidget(self.ppd)
        self.info_section.addWidget(self.employee)
        self.info_section.addWidget(self.refresh)

        self.main_table = QTableWidget()
        self.main_table.setColumnCount(3)
        self.main_table.setRowCount(14)
        self.main_table.setHorizontalHeaderLabels(
            ["Date", "Total Hours", "Over Time"])
        self.main_table.setStyleSheet("border: 1px solid gray;")
        self.main_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)

        self.middle_widgets = QHBoxLayout()
        self.middle_widgets.addWidget(self.main_table)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_layout = QVBoxLayout()
        top_layout.addWidget(self.title_label)
        top_layout.addLayout(self.info_section)

        middle_layout = QVBoxLayout()
        middle_layout.addLayout(self.middle_widgets)
        middle_layout.addWidget(self.status_label)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_layout)
        main_layout.addLayout(middle_layout)
        self.setLayout(main_layout)

    @asyncSlot()
    async def export_button_action(self):
        """
        Creates zipped dump file of the database that can be imported
        in another instance of the application to re-create the database
        with it's data.
        """

        try:
            file_path = QFileDialog.getExistingDirectory(
                self, "Select Directory", os.getcwd()
            )

            if file_path:
                async with AsyncDBInterface() as db:
                    result = await db.dump_db_and_zip(output_dir=file_path)

                if result == ERROR:
                    raise Exception("Failed to create dump file and zip it.")

                self.status_label.setText(
                    "Exported backup to " + result)

            else:
                raise Exception("Invalid file path")

        except Exception as e:
            log.error(
                "Error during dump and compression: %s | %s",
                type(e).__name__,
                e.args,
            )

    @asyncSlot()
    async def import_button_action(self):
        """
        Creates zipped dump file of the database that can be imported
        in another instance of the application to re-create the database.
        """
        try:
            file_path = QFileDialog.getOpenFileName(
                self, "Select compressed dump file", "", "*.zip"
            )

            if file_path:
                async with AsyncDBInterface() as db:
                    result = await db.initialize_db_from_zip(output_dir=file_path[0])

                if result == SUCCESS:
                    self.status_label.setText("File Successfully Imported")

                else:
                    self.status_label.setText("Something went wrong")

            else:
                raise "Invalid file path"

        except Exception as e:
            log.error(
                "Error during dump and compression: %s | %s",
                type(e).__name__,
                e.args,
            )

    def make_combo_searchable(self, combo: QComboBox):
        model = QStringListModel([combo.itemText(i)
                                 for i in range(combo.count())])
        proxy_model = QSortFilterProxyModel(combo)
        proxy_model.setSourceModel(model)

        completer = QCompleter(proxy_model, combo)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        combo.setCompleter(completer)

    @asyncSlot()
    async def refresh_choice(self):
        self.ppd.clear()
        self.employee.clear()
        await self.ppd_filler()
        self.update()

    async def ppd_filler(self):
        try:
            dates = await self.pp_manager.get_pay_period_dates()

            if dates != ERROR:
                for d in dates:
                    self.ppd.addItem(d)

                self.make_combo_searchable(self.ppd)

            else:
                self.status_label.setText("No Pay Periods found")

        except Exception as e:
            log.error("Failed to load pay period dates: %s", str(e))
            self.status_label.setText(str(e))

    @asyncSlot()
    async def ppd_choice(self, date: str):
        self.selected_date = date
        self.employee.clear()
        await self.employee_filler(date)
        self.selected_employee = self.employee.currentText()

    @asyncSlot()
    async def employee_filler(self, date: str):
        if date == "" or date is None:
            date = self.pp_manager.get_default_date()

        try:
            names = await self.pp_manager.get_employee_names_by_date(date)
            for name in names:
                self.employee.addItem(name)

            self.employee.update()
            self.make_combo_searchable(self.employee)

        except Exception as e:
            log.error("Failed to load employees: %s", str(e))
            self.status_label.setText("Failed to load employee list.")

    @asyncSlot()
    async def employee_choice(self, employee: str):
        if employee == "" or employee is None:
            employee = await self.pp_manager.get_default_employee()

            await self.populate_main(
                employee=employee, selected_date=self.selected_date
            )

        else:
            sanitized = TableWidget.__sanitize_name_for_db(employee)

            await self.populate_main(
                employee=sanitized, selected_date=self.selected_date
            )

    @asyncSlot()
    async def populate_main(self, employee: tuple, selected_date: str):
        if not selected_date:
            selected_date = self.pp_manager.get_default_date()

        try:
            emp_id = await self.pp_manager.get_employee_id(employee)
            pp_id = await self.pp_manager.get_pay_period_id(emp_id, selected_date)
            work_entries = await self.pp_manager.get_work_entries(pp_id)

            self.main_table.clearContents()

            date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()

            dates = {}

            if not work_entries:
                raise NoWorkEntries()

            # Fill in Dates in Pay Period

            for i in range(14):
                curr_date = date_obj + timedelta(i)

                self.__add_cell_value(i, 0, curr_date)

                dates.update({i: str(curr_date)})

            # Fill Work Entries and Overtime Earned

            for entry in work_entries:
                if entry[0] in dates.values():
                    date_key = TableWidget.__get_key_from_value(
                        dictionary=dates, value=entry[0])[0]

                    self.__add_cell_value(
                        row=date_key,
                        col=1,
                        value=float(entry[1]),
                    )

                    self.__add_cell_value(
                        row=date_key,
                        col=2,
                        value=entry[1]-8,
                    )

                del dates[date_key]

            # Fill Empty Work Entries

            for key, value in dates.items():
                self.__add_cell_value(
                    row=key, col=1, value=0.0)

                self.__add_cell_value(
                    row=key, col=2, value=0.0)

        except NoWorkEntries:
            for i in range(14):
                curr_date = date_obj + timedelta(i)
                self.__add_cell_value(i, 0, curr_date)

                self.__add_cell_value(row=i, col=1, value=0.0)

                self.__add_cell_value(row=i, col=2, value=0.0)

        except Exception as e:
            log.error("Failed to populate table: %s", str(e))
            self.status_label.setText("Error populating timesheet data.")

        except KeyError as e:
            log.error("KeyError: %s", str(e))

    def __add_cell_value(self, row: int, col: int, value):
        try:
            item = QTableWidgetItem(str(value))
            self.main_table.setItem(row, col, item)

        except Exception as e:
            log.error("Failed to set cell (%d, %d): %s", row, col, str(e))

    @staticmethod
    def __get_key_from_value(dictionary: dict, value: any):
        return [key for key, val in dictionary.items() if val == value]

    @staticmethod
    def __sanitize_name_for_db(employee: str):
        name = employee.split(" ")

        if len(name) < 3:
            name.insert(1, "")

        if len(name) > 3:
            name = [name[0], name[1], name[2] + " " + name[3]]

        if len(name[1]) >= 3 or re.search(pattern="JR(.|)", string=name[2]):
            if len(name[1]) > 1:
                name = [name[0], name[1] + " " + name[2]]

        if len(name) < 3:
            name.insert(1, "")

        return name
