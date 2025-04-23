from datetime import datetime
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QFileDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QComboBox, QHBoxLayout, QPushButton
)

from util.logger import CLogger
from util.db import DBInterface
from util.controller import Controller
from util.processor import Processor

log = CLogger().get_logger()


class TableWidget(QWidget):
    '''
        PyQt6 Widget that handles the file upload and displays
        the data into a table.
    '''

    def __init__(self, BUILD: str, DB: str):
        super().__init__()
        self.setAcceptDrops(True)  # Enable drag and drop

        if BUILD == "DEBUG":
            log.info("Table Widget: %s", BUILD)

        self.DB = DB
        self.BUILD = BUILD

        # Title Label
        self.title_label = QLabel("Pay Period", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 20px; padding: 10px;")

        # Combobox Widget for Pay Period Info
        self.pp_id = QComboBox()
        self.pp_id_filler()
        self.pp_id.currentTextChanged.connect(self.pp_id_choice)

        self.ppd = QComboBox()
        self.ppd_filler()
        self.ppd.currentTextChanged.connect(self.ppd_choice)

        self.refresh = QPushButton(text="Refresh")
        self.refresh.clicked.connect(self.refresh_choice)

        # Info Widget
        self.info_section = QHBoxLayout()
        self.info_section.addWidget(self.pp_id)
        self.info_section.addWidget(self.ppd)
        self.info_section.addWidget(self.refresh)

        # Table Widget for Displaying Data
        self.main_table = QTableWidget()
        self.main_table.setColumnCount(0)  # Will be set after parsing
        self.main_table.setStyleSheet("border: 1px solid gray;")
        self.main_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_layout = QVBoxLayout()
        top_layout.addWidget(self.title_label)
        top_layout.addLayout(self.info_section)

        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(self.main_table)
        bottom_layout.addWidget(self.status_label)

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def open_file_dialog(self):
        """
            We are stuck having this parse the file.
        """

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xls)")

        if file_path:
            self.process_file(file_path, self.BUILD)

    def refresh_choice(self):
        self.ppd.clear()
        self.pp_id.clear()

        self.ppd_filler()
        self.pp_id_filler()

        self.update()

    def ppd_filler(self):
        db = DBInterface(self.DB)
        dates = db._read_pay_period_dates(self.BUILD)

        if dates is not None:
            for d in dates:
                self.ppd.addItem(d[0])

    def ppd_choice(self, s):
        log.info("Text Changed: %s", s)

    def pp_id_filler(self):
        db = DBInterface(self.DB)
        ids = db._read_pay_period_ids(self.BUILD)

        if ids is not None:
            for i in ids:
                self.pp_id.addItem(str(i[0]))

    def pp_id_choice(self, s: str):
        log.info("Text Changed: %s", s)
        self.new_populate_main(DB=self.DB, BUILD=self.BUILD, pp_id=str(s))

    def process_file(self, file_path, BUILD):

        if BUILD == "DEBUG":
            p = Processor(BUILD, self.DB)
            users = p.extract_data(file_path, BUILD)

        if BUILD == "PROD":
            c = Controller(BUILD, self.DB)
            users = c.extract_data(file_path, BUILD)
            self.old_populate_main(users, BUILD)

        now = datetime.now().time()

        self.status_label.setText(
            f"File successfully processed {now.strftime('%I:%M:%S')}")

    def old_populate_main(self, users, BUILD):

        if not users:
            self.status_label.setText("No data found in file.")
            return

        pay_period = users[0].pay_period_dates()
        pay_period = [str(i) for i in pay_period]
        headers = ["employee_name", "employee_group"] + pay_period

        self.main_table.setColumnCount(len(headers))
        self.main_table.setHorizontalHeaderLabels(headers)
        self.main_table.setRowCount(len(users))

        self.__populate_table_iterator(
            users, headers, BUILD)

    def new_populate_main(self, DB: str, BUILD: str, pp_id: str):
        db = DBInterface(DB)
        entries = db._read_work_entries(BUILD=BUILD, args=(pp_id))
        log.info(entries)

    def __add_cell_value(self, row_id, col_id, value, BUILD):
        try:
            item = QTableWidgetItem(
                str(value))
            self.main_table.setItem(
                row_id, col_id, item)
        except Exception as e:
            log.error(e)
            assert e.with_traceback

    def __populate_table_iterator(self, users, headers,
                                  BUILD):
        try:
            headers = [str(i) for i in headers]

            for row_id in range(0, len(users)):
                user = users[row_id]
                user_info = {"employee_name": user.name,
                             "employee_group": user.group}
                hours = self.__format_hrs(user.get_hrs_wrked(), BUILD)
                user_data = {**user_info, **hours}

                for col_id in range(len(headers)):
                    if headers[col_id] in user_data.keys():
                        value = str(user_data[headers[col_id]])

                        self.__add_cell_value(
                            row_id, col_id,
                            value, BUILD)

        except Exception as e:
            log.error(e)
            assert e.with_traceback()

    def __format_hrs(self, user_hrs: dict, BUILD):
        formatted = list()

        try:
            unformatted, hours = list(user_hrs.keys()), list(user_hrs.values())

            for i in unformatted:
                formatted.append(str(i))

            formatted = dict(zip(formatted, hours))

        except Exception as e:
            log.error(e)

        return formatted
