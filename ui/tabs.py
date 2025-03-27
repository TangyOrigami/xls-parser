from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QLabel, QWidget

from ui.fileupload import FileUploadWidget
from ui.dashboard import Dashboard


class TabMenu(QTabWidget):
    def __init__(self):
        super().__init__()

        self.setTabPosition(QTabWidget.TabPosition.West)

        self.file_upload_widget = FileUploadWidget()
        self.dashboard_widget = Dashboard()

        # Table
        table_widget = self.file_upload_widget

        # Dashboard
        dashboard_widget = self.dashboard_widget

        # Paystub
        paystub_widget = QWidget()
        paystub_layout = QVBoxLayout(paystub_widget)
        paystub_label = QLabel("Paystub Widget")
        paystub_layout.addWidget(paystub_label)
        paystub_widget.setLayout(paystub_layout)

        self.addTab(table_widget, "Table")
        self.addTab(dashboard_widget, "Dashboard")
        self.addTab(paystub_widget, "Paystub")
