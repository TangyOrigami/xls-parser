import re
from datetime import datetime, timedelta
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

        # Config Varibles
        self.DB = DB
        self.BUILD = BUILD

        # Global Variables
        self.emp_id = None
        self.pp_id = None

        # Title Label
        self.title_label = QLabel("Pay Period", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 20px; padding: 10px;")

        # Combobox Widget for Pay Period Info
        self.ppd = QComboBox()
        self.ppd_filler()
        self.ppd.currentTextChanged.connect(self.ppd_choice)

        self.employee = QComboBox()
        self.employee.currentTextChanged.connect(self.employee_choice)

        self.refresh = QPushButton(text="Refresh")
        self.refresh.clicked.connect(self.refresh_choice)

        # Info Widget
        self.info_section = QHBoxLayout()
        self.info_section.addWidget(self.ppd)
        self.info_section.addWidget(self.employee)
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
        self.employee.clear()

        self.ppd_filler()

        self.update()

    def ppd_filler(self):
        self.selected_date = self.ppd.currentText()
        db = DBInterface(self.DB)
        dates = db._read_pay_period_dates(self.BUILD)

        if dates is not None:
            for d in dates:
                self.ppd.addItem(d[0])

    def ppd_choice(self, date: str):
        self.selected_date = date
        self.employee.clear()
        self.employee_filler(date)
        self.selected_employee = self.employee.currentText()

    def employee_filler(self, date: str):
        db = DBInterface(self.DB)
        pp_ids = db._read_pay_period_ids(BUILD=self.BUILD, args=date)
        emp_ids = []

        if pp_ids is not None:
            for pp_id in pp_ids:
                emp_ids.append(db._read_employee_ids(
                    BUILD=self.BUILD, args=pp_id)[0])

        for emp_id in emp_ids:
            emp_name = db._read_employee_name(BUILD=self.BUILD, args=emp_id)[0]
            emp_name = ' '.join(' '.join(emp_name).split())
            self.employee.addItem(emp_name)

        self.employee.update()

    def employee_choice(self, employee: str):
        db = DBInterface(self.DB)

        if employee == "":
            employee = str(db._default_employee(BUILD=self.BUILD)[0])

        employee = self.__sanitize_name_for_db(employee)

        self.new_populate_main(
            DB=self.DB, BUILD=self.BUILD,
            employee=employee,
            date=(self.selected_date,)
        )

    def __sanitize_name_for_db(self, employee: str):
        '''
        '''

        name = employee.split(' ')

        if len(name) < 3:
            name.insert(1, '')

        if len(name) > 3:
            name = [name[0], name[1], name[2] + ' ' + name[3]]

        if len(name[1]) >= 3 or re.search(pattern="JR(.|)", string=name[2]) and len(name[1]) > 1:
            name = [name[0], name[1] + ' ' + name[2]]

        if len(name) < 3:
            name.insert(1, '')

        return name

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

    def new_populate_main(self, DB: str, BUILD: str,
                          employee: tuple, date: tuple):
        db = DBInterface(DB)
        emp_id = db._read_employee_id(BUILD=BUILD, args=employee)

        if not emp_id:
            pp_id = db._read_pay_period_id_by_date(BUILD=BUILD, args=date)

            work_entries = db._read_work_entries(BUILD=BUILD, args=pp_id)
        else:
            pp_id = str(db._read_pay_period_id(
                BUILD=BUILD, args=emp_id[0]+date)[0][0])

            work_entries = db._read_work_entries(BUILD=BUILD, args=pp_id)

        log.info("Work Entries: %s", work_entries)

        self.main_table.setColumnCount(2)
        self.main_table.setRowCount(14)
        self.main_table.setHorizontalHeaderLabels(["Date", "Hours"])

        if self.selected_date == '':
            self.selected_date = str(db._default_date(BUILD)[0][0])

        date = datetime.strptime(self.selected_date, "%Y-%m-%d").date()

        for i in range(14):
            curr_date = date+timedelta(i)

            self.__add_cell_value(
                BUILD=BUILD,
                row_id=i,
                col_id=0,
                value=curr_date
            )

            if BUILD == "PROD":
                for j in work_entries:
                    if curr_date == j[0]:
                        self.__add_cell_value(
                            BUILD=BUILD,
                            row_id=i,
                            col_id=1,
                            value=j[1]
                        )

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
