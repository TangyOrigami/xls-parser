import sys

from PyQt6.QtWidgets import (
    QApplication, QMainWindow
)

from PyQt6.QtGui import QAction
from ui.tabs import TabMenu
from util.db import DBInterface


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Time Sheet App")

        self.tab_menu = TabMenu()

        # Menu
        open_button = QAction("Open", self)
        open_button.setStatusTip("Open a file")
        open_button.triggered.connect(
            self.tab_menu.file_upload_widget.open_file_dialog)

        save_button = QAction("Save", self)
        save_button.setStatusTip("Save current view")
        save_button.triggered.connect(self.save_button_action)

        save_as_button = QAction("Save as", self)
        save_as_button.setStatusTip("Save current view as")
        save_as_button.triggered.connect(self.save_as_button_action)

        close_button = QAction("Close", self)
        close_button.setStatusTip("Close current view")
        close_button.triggered.connect(self.close)

        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        file_submenu = file_menu.addMenu("Save")
        file_submenu.addAction(save_button)
        file_submenu.addSeparator()
        file_submenu.addAction(save_as_button)
        file_menu.addSeparator()

        file_menu.addAction(open_button)
        file_menu.addSeparator()

        file_menu.addAction(close_button)

        self.app_setup()

        self.setCentralWidget(self.tab_menu)

    def save_button_action(self, s):
        print("save", s)

    def save_as_button_action(self, s):
        print("save as", s)

    def app_setup(self):
        db = DBInterface("app.db")

        db.initialize_db(verbose=True)


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
