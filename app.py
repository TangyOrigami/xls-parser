import sys
import os
from dotenv import load_dotenv

from PyQt6.QtWidgets import (
    QApplication, QMainWindow
)
from PyQt6.QtCore import QCommandLineOption, QCommandLineParser
from PyQt6.QtGui import QAction
from ui.tabs import TabMenu
from util.db import DBInterface
from util.logger import CLogger

load_dotenv()
logger = CLogger().get_logger()


def args_parser(app) -> [str, str]:
    '''
        Helper function to parse CLI args.
        Default environment variables will be set in the .env file.
    '''
    parser = QCommandLineParser()
    parser.addHelpOption()
    parser.addVersionOption()

    debug_option = QCommandLineOption(
        ["d", "debug"],
        "Set logging to debug."
    )
    parser.addOption(debug_option)

    parser.process(app)

    parser.isSet(debug_option)

    if parser.isSet(debug_option):
        BUILD = "DEBUG"
        DB = os.environ.get("DB")
        logger.info("BUILD: " + BUILD)
    else:
        BUILD = os.environ.get("BUILD")
        logger.info("BUILD: " + BUILD)
        DB = os.environ.get("DB")

    return [BUILD, DB]


class MainWindow(QMainWindow):
    def __init__(self, BUILD, DB):
        super().__init__()

        if BUILD == "DEBUG":
            logger.info("Main Window: %s", BUILD)

        self.setWindowTitle("Time Sheet App")

        self.tab_menu = TabMenu(BUILD, DB)

        # Menu
        open_button = QAction("Open", self)
        open_button.setStatusTip("Open a file")
        open_button.triggered.connect(
            self.tab_menu.table_widget.open_file_dialog)

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

        self.app_setup(BUILD, DB)

        self.setCentralWidget(self.tab_menu)

    def save_button_action(self, s):
        print("save", s)

    def save_as_button_action(self, s):
        print("save as", s)

    def app_setup(self, BUILD, DB):
        db = DBInterface(DB)

        db.initialize_db(BUILD)


if __name__ == '__main__':
    args = sys.argv
    app = QApplication(args)
    app.setApplicationName("Timesheet Analyzer")
    app.setApplicationVersion("0.0.2")
    BUILD, DB = args_parser(app)

    window = MainWindow(BUILD, DB)
    window.show()
    sys.exit(app.exec())
