from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QFileDialog, QPushButton,
    QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
)

from util.logger import CLogger
from util.controller import Controller

logger = CLogger().get_logger()


class TableWidget(QWidget):
    '''
        PyQt6 Widget that handles the file upload and displays
        the data into a table.
    '''

    def __init__(self, log_level):
        super().__init__()
        self.setAcceptDrops(True)  # Enable drag and drop
        self.log_level = log_level

        # Title Label
        self.title_label = QLabel("Table", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 20px; padding: 10px;")

        # Test Button
        self.count = 0
        self.button = QPushButton(f"Click Count: {self.count}", self)
        self.button.clicked.connect(self.count_clicks)

        # Table Widget for Displaying Data
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(0)  # Will be set after parsing
        self.table_widget.setStyleSheet("border: 1px solid gray;")
        self.table_widget.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        middle_layout = QVBoxLayout()
        middle_layout.addWidget(self.title_label)
        middle_layout.addWidget(self.button)

        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(self.table_widget)
        bottom_layout.addWidget(self.status_label)

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xls)")
        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path):
        self.status_label.setText("Processing file...")

        try:
            c = Controller(log_level=self.log_level)
            users = c.extract_data(file_path=file_path)
            self.populate_table(users)
            self.status_label.setText("File successfully processed!")
        except Exception as e:
            logger.error(e)
            self.status_label.setText(f"Error processing file: {e}")

    def populate_table(self, users):

        if not users:
            self.status_label.setText("No data found in file.")
            return

        try:

            pay_period = users[0].pay_period_dates()
            pay_period = [str(i) for i in pay_period]
            headers = ["employee_name", "employee_group"] + pay_period

            self.table_widget.setColumnCount(len(headers))
            self.table_widget.setHorizontalHeaderLabels(headers)
            self.table_widget.setRowCount(len(users))

            self.__populate_table_iterator(users, headers)
        except Exception as e:
            logger.error(e)

    def count_clicks(self):
        self.count += 1
        self.button.setText(f"Click Count: {self.count}")

    def __add_cell_value(self, row_id, col_id, value):
        try:
            item = QTableWidgetItem(
                str(value))
            self.table_widget.setItem(
                row_id, col_id, item)
        except Exception as e:
            logger.error(e)

    def __populate_table_iterator(self, users, headers):
        try:
            headers = [str(i) for i in headers]

            for row_id in range(0, len(users)):
                user = users[row_id]
                user_info = {"employee_name": user.name,
                             "employee_group": user.group}
                hours = self.__format_hrs(user.get_hrs_wrked())
                user_data = {**user_info, **hours}

                for col_id in range(len(headers)):
                    if headers[col_id] in user_data.keys():
                        value = str(user_data[headers[col_id]])

                        self.__add_cell_value(
                            row_id=row_id, col_id=col_id, value=value)

        except Exception as e:
            logger.error(e)

    def __format_hrs(self, user_hrs: dict):
        formatted = list()

        try:
            unformatted, hours = list(user_hrs.keys()), list(user_hrs.values())

            for i in unformatted:
                formatted.append(str(i))

            formatted = dict(zip(formatted, hours))

        except Exception as e:
            logger.error(e)

        return formatted
