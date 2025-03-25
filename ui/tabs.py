from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QLabel, QWidget

from ui.fileupload import FileUploadWidget


class TabMenu(QTabWidget):
    def __init__(self):
        super().__init__()

        self.setTabPosition(QTabWidget.TabPosition.West)

        self.file_upload_widget = FileUploadWidget()

        # Table
        table_widget = self.file_upload_widget

        # Dashboard
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        dashboard_label = QLabel("Dashboard Widget")
        dashboard_layout.addWidget(dashboard_label)
        dashboard_widget.setLayout(dashboard_layout)

        # Paystub
        paystub_widget = QWidget()
        paystub_layout = QVBoxLayout(paystub_widget)
        paystub_label = QLabel("Paystub Widget")
        paystub_layout.addWidget(paystub_label)
        paystub_widget.setLayout(paystub_layout)

        self.addTab(table_widget, "Table")
        self.addTab(dashboard_widget, "Dashboard")
        self.addTab(paystub_widget, "Paystub")
