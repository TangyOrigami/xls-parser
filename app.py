import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QFileDialog,
    QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QMainWindow, QMenu
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QAction
from util.controller import Controller as c


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.show()

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

    def contextMenuEvent(self, pos):
        context = QMenu(self)
        context.addAction(QAction("test 1", self))
        context.addAction(QAction("test 2", self))
        context.addAction(QAction("test 3", self))
        context.exec(self.mapToGlobal(pos))


class FileUploadWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)  # Enable drag and drop

        # Title Label
        self.title_label = QLabel("Excel File Parser", self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; padding: 10px;")

        # File Upload Button
        self.upload_button = QPushButton("Upload File")
        self.upload_button.clicked.connect(self.open_file_dialog)
        self.upload_button.setStyleSheet("padding: 8px; font-size: 14px;")

        # File Path Label
        self.file_path_label = QLabel(
            "Drag and drop a file here or use the button to upload.", self)
        self.file_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_path_label.setStyleSheet(
            "color: gray; font-style: italic; padding: 10px;")

        # Table Widget for Displaying Data
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(0)  # Will be set after parsing
        self.table_widget.setStyleSheet("border: 1px solid gray;")
        self.table_widget.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)

        # Status Label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Layouts
        top_layout = QVBoxLayout()
        top_layout.addWidget(self.title_label)

        middle_layout = QVBoxLayout()
        middle_layout.addWidget(self.upload_button)
        middle_layout.addWidget(self.file_path_label)

        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(self.table_widget)
        bottom_layout.addWidget(self.status_label)

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xls)")
        if file_path:
            self.process_file(file_path)

    def process_file(self, file_path):
        self.file_path_label.setText(f"Selected file: {file_path}")
        self.status_label.setText("Processing file...")

        try:
            users = c.extract_data(file_path)
            self.populate_table(users)
            self.status_label.setText("File successfully processed!")
        except Exception as e:
            self.status_label.setText(f"Error processing file: {e}")

    def populate_table(self, users):
        if not users:
            self.status_label.setText("No data found in file.")
            return

        pay_period = users[0].pay_period_dates()
        headers = ["Name", "Start Date"] + pay_period

        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setRowCount(len(users))
        self.table_widget.setHorizontalHeaderLabels(headers)

        for row_id in range(0, len(users)):
            user = users[row_id]
            user_info = {"Name": user.name, "Start Date": user.start_date}
            user_data = {**user_info, **user.get_hrs_wrked()}

            for col_id in range(len(headers)):
                if headers[col_id] in user_data.keys():
                    value = str(user_data[headers[col_id]])

                    self.__add_cell_value(
                        row_id=row_id, col_id=col_id, value=value)

    def __add_cell_value(self, row_id, col_id, value):
        item = QTableWidgetItem(
            str(value))
        self.table_widget.setItem(
            row_id, col_id, item)

    # Drag & Drop Events

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith((".xls")):
                self.process_file(file_path)
            else:
                self.status_label.setText(
                    "Invalid file type. Please select an Excel file.")


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
