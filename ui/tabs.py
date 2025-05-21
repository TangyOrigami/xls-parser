from PyQt6.QtWidgets import QTabWidget

from ui.dashboard import Dashboard
from ui.table import TableWidget
from util.logger import CLogger

log = CLogger().get_logger()


class TabMenu(QTabWidget):
    """
    PyQt6 Widget that scaffolds the structure of the app
    as a tab menu on the left handside of the window.
    """

    def __init__(self, BUILD):
        super().__init__()
        if BUILD == "DEBUG":
            log.info("Tab Menu: %s", BUILD)

        self.setTabPosition(QTabWidget.TabPosition.West)

        self.table_widget = TableWidget(BUILD)
        self.dashboard_widget = Dashboard(BUILD)

        # Table
        table_widget = self.table_widget

        # Dashboard
        dashboard_widget = self.dashboard_widget

        self.addTab(table_widget, "Table")
        self.addTab(dashboard_widget, "Dashboard")
