import re
from datetime import datetime, timedelta

from PyQt6.QtCore import QSortFilterProxyModel, QStringListModel, Qt
from PyQt6.QtWidgets import (QComboBox, QCompleter, QFileDialog, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from util.db import DBInterface
from util.logger import CLogger
from util.processor import Processor

log = CLogger().get_logger()


class TableWidget(QWidget):
    """
    PyQt6 Widget that handles the file upload and displays
    the data into a table.
    """

    def __init__(self, BUILD: str, DB: str):
        super().__init__()
        self.setAcceptDrops(True)

        if BUILD == "DEBUG":
            log.info("Table Widget: %s", BUILD)

        self.DB = DB
        self.BUILD = BUILD

        self.emp_id = None
        self.pp_id = None

        self.title_label = QLabel("Pay Period", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; padding: 10px;")

        self.ppd = QComboBox()
        self.ppd.setEditable(True)
        self.ppd.currentTextChanged.connect(self.ppd_choice)

        self.employee = QComboBox()
        self.employee.setEditable(True)
        self.employee.currentTextChanged.connect(self.employee_choice)

        self.refresh = QPushButton(text="Refresh")
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

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_layout = QVBoxLayout()
        top_layout.addWidget(self.title_label)
        top_layout.addLayout(self.info_section)

        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(self.main_table)
        bottom_layout.addWidget(self.status_label)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(top_layout)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

        self.ppd_filler()

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
            self.process_file(file_path, self.BUILD)

    def refresh_choice(self):
        self.ppd.clear()
        self.employee.clear()
        self.ppd_filler()
        self.update()

    def ppd_filler(self):
        db = DBInterface(self.DB)
        dates = db._read_pay_period_dates(self.BUILD)
        if dates is not None:
            for d in dates:
                self.ppd.addItem(d[0])
        self.make_combo_searchable(self.ppd)

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
                emp_ids.append(db._read_employee_ids(BUILD=self.BUILD, args=pp_id)[0])

        for emp_id in emp_ids:
            emp_name = db._read_employee_name(BUILD=self.BUILD, args=emp_id)[0]
            emp_name = " ".join(" ".join(emp_name).split())
            self.employee.addItem(emp_name)

        self.employee.update()
        self.make_combo_searchable(self.employee)

    def employee_choice(self, employee: str):
        valid_entries = [
            self.employee.itemText(i) for i in range(self.employee.count())
        ]
        if employee not in valid_entries:
            self.status_label.setText("Invalid employee name.")
            return

        sanitized_employee = self.__sanitize_name_for_db(employee)

        if self.selected_date != "":
            self.populate_main(
                DB=self.DB,
                BUILD=self.BUILD,
                employee=sanitized_employee,
                date=(self.selected_date,),
            )

    def process_file(self, file_path, BUILD):
        p = Processor(BUILD, self.DB)
        p.extract_data(file_path, BUILD)
        now = datetime.now().time()
        self.status_label.setText(
            f"File successfully processed {now.strftime('%I:%M:%S')}"
        )

    def populate_main(self, DB: str, BUILD: str, employee: tuple, date: tuple):
        db = DBInterface(DB)
        emp_id = db._read_employee_id(BUILD=BUILD, args=employee)
        log.error("emp_id: %s", emp_id)

        if not emp_id:
            pp_id = db._read_pay_period_id_by_date(BUILD=BUILD, args=date)[0]
            work_entries = db._read_work_entries(BUILD=BUILD, args=pp_id)
        else:
            pp_id = str(
                db._read_pay_period_id(BUILD=BUILD, args=emp_id[0] + date)[0][0]
            )
            work_entries = list(db._read_work_entries(BUILD=BUILD, args=pp_id))

        self.main_table.clearContents()

        if self.selected_date == "":
            self.selected_date = str(db._default_date(BUILD)[0][0])

        date = datetime.strptime(self.selected_date, "%Y-%m-%d").date()

        for i in range(14):
            curr_date = date + timedelta(i)
            self.__add_cell_value(BUILD=BUILD, row_id=i, col_id=0, value=curr_date)

            if work_entries:
                for x, j in enumerate(work_entries):
                    table_date = self.main_table.item(i, 0).text()
                    if table_date == j[0]:
                        self.__add_cell_value(
                            BUILD=BUILD, row_id=i, col_id=1, value=j[1]
                        )
                        work_entries.pop(x)
                        break

    def __add_cell_value(self, row_id, col_id, value, BUILD):
        try:
            item = QTableWidgetItem(str(value))
            self.main_table.setItem(row_id, col_id, item)
        except Exception as e:
            log.error(e)
            assert e.with_traceback

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
