import os
import re
from datetime import datetime, timedelta

import pyqtgraph as pg
from PyQt6.QtCore import QSortFilterProxyModel, QStringListModel, Qt
from PyQt6.QtWidgets import (
    QApplication,
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
from util.db import DBInterface
from util.logger import CLogger
from util.pay_period_manager import PayPeriodManager
from util.processor import Processor

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class TableWidget(QWidget):
    def __init__(self, BUILD: str):
        super().__init__()
        self.setAcceptDrops(True)

        self.BUILD = BUILD
        self.pp_manager = PayPeriodManager(BUILD)

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
        self.main_table.setColumnCount(2)
        self.main_table.setRowCount(14)
        self.main_table.setHorizontalHeaderLabels(["Date", "Hours"])
        self.main_table.setStyleSheet("border: 1px solid gray;")
        self.main_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.plot_widget = pg.PlotWidget()

        self.middle_widgets = QHBoxLayout()
        self.middle_widgets.addWidget(self.main_table)
        self.middle_widgets.addWidget(self.plot_widget)

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

        self.ppd_filler()

    def export_button_action(self):
        """
        Creates zipped dump file of the database that can be imported
        in another instance of the application to re-create the database.
        """
        try:
            file_path = QFileDialog.getExistingDirectory(
                self, "Select Directory", os.getcwd()
            )

            if file_path:
                db = DBInterface()
                result = db.dump_db_and_compress(output_dir=file_path)
                if isinstance(result, list):
                    self.status_label.setText("Exported backup to " + result[0])
            else:
                raise Exception("Invalid file path")

        except Exception as e:
            log.error(
                "Error during dump and compression: %s | %s",
                type(e).__name__,
                e.args,
            )

    def import_button_action(self):
        """
        Creates zipped dump file of the database that can be imported
        in another instance of the application to re-create the database.
        """
        try:
            file_path = QFileDialog.getOpenFileName(
                self, "Select compressed dump file", "", "*.sql.gz"
            )

            if file_path:
                db = DBInterface()
                result = db.initialize_db_from_dump_file(output_path=file_path[0])

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
        model = QStringListModel([combo.itemText(i) for i in range(combo.count())])
        proxy_model = QSortFilterProxyModel(combo)
        proxy_model.setSourceModel(model)

        completer = QCompleter(proxy_model, combo)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        combo.setCompleter(completer)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xls)"
        )
        if file_path:
            now = datetime.now().strftime("%I:%M:%S")
            processing = f"Started processing file at {now}"

            self.status_label.setText(processing)
            QApplication.processEvents()

            self.process_file(file_path)

    def refresh_choice(self):
        self.ppd.clear()
        self.employee.clear()
        self.ppd_filler()
        self.update()

    def ppd_filler(self):
        try:
            dates = self.pp_manager.get_pay_period_dates()
            if dates != ERROR:
                for d in dates:
                    self.ppd.addItem(d)
                self.make_combo_searchable(self.ppd)
            else:
                self.status_label.setText("No Pay Periods found")

        except Exception as e:
            log.error("Failed to load pay period dates: %s", str(e))
            self.status_label.setText(str(e))

    def ppd_choice(self, date: str):
        self.selected_date = date
        self.employee.clear()
        self.employee_filler(date)
        self.selected_employee = self.employee.currentText()

    def employee_filler(self, date: str):
        if date == "" or date is None:
            date = self.pp_manager.get_default_date()

        try:
            names = self.pp_manager.get_employee_names_by_date(date)
            for name in names:
                self.employee.addItem(name)
            self.employee.update()
            self.make_combo_searchable(self.employee)
        except Exception as e:
            log.error("Failed to load employees: %s", str(e))
            self.status_label.setText("Failed to load employee list.")

    def employee_choice(self, employee: str):
        if employee == "" or employee is None:
            employee = self.pp_manager.get_default_employee()
            if self.selected_date:
                self.populate_main(employee=employee, date=self.selected_date)
        else:
            sanitized = self.__sanitize_name_for_db(employee)
            if self.selected_date:
                self.populate_main(employee=sanitized, date=self.selected_date)

    def process_file(self, file_path):
        try:
            Processor().extract_data(file_path, self.BUILD)

            now = datetime.now().strftime("%I:%M:%S")
            processed = f"File successfully processed at {now}"

            self.status_label.setText(processed)

        except Exception as e:
            log.error("Failed to process file: %s", str(e))
            self.status_label.setText("Failed to process file.")

    def populate_main(self, employee: tuple, date: str):
        try:
            emp_id = self.pp_manager.get_employee_id(employee)
            pp_id = self.pp_manager.get_pay_period_id(emp_id, date)
            work_entries = self.pp_manager.get_work_entries(pp_id)

            self.main_table.clearContents()

            if not date:
                date = self.pp_manager.get_default_date()
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()

            dates = []
            hours = []

            for i in range(14):
                curr_date = date_obj + timedelta(i)
                self.__add_cell_value(i, 0, curr_date)
                dates.append(str(curr_date))

                for x, entry in enumerate(work_entries):
                    if self.main_table.item(i, 0).text() == entry[0]:
                        hours.append(entry[1])
                        self.__add_cell_value(i, 1, entry[1])
                        work_entries.pop(x)
                        break
                    else:
                        self.__add_cell_value(i, 1, 0)
                        hours.append(0)
                        break

            x = [i for i in range(1, len(hours) + 1)]
            ticks = list(zip(x, dates))
            self.populate_graph(x=x, y=hours, ticks=ticks)

        except Exception as e:
            log.error("Failed to populate table: %s", str(e))
            self.status_label.setText("Error populating timesheet data.")

    def populate_graph(self, x: list, y: list, ticks: tuple):
        self.plot_widget.clear()
        self.plot_widget.plot(x, y, pen="r")

    def __add_cell_value(self, row: int, col: int, value):
        try:
            item = QTableWidgetItem(str(value))
            self.main_table.setItem(row, col, item)
        except Exception as e:
            log.error("Failed to set cell (%d, %d): %s", row, col, str(e))

    def __sanitize_name_for_db(self, employee: str):
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
