from PyQt6.QtWidgets import QTabWidget, QVBoxLayout, QLabel, QWidget

from ui.table import TableWidget
from ui.dashboard import Dashboard
from util.logger import CLogger

log = CLogger().get_logger()


class TabMenu(QTabWidget):
    '''
        PyQt6 Widget that scaffolds the structure of the app
        as a tab menu on the left handside of the window.
    '''

    def __init__(self, BUILD, DB):
        super().__init__()
        if BUILD == "DEBUG":
            log.info("Tab Menu: %s", BUILD)

        self.setTabPosition(QTabWidget.TabPosition.West)

        self.table_widget = TableWidget(BUILD, DB)
        self.dashboard_widget = Dashboard(BUILD, DB)

        # Table
        table_widget = self.table_widget

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
