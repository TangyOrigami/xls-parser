import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PyQt6.QtCore import QCommandLineOption, QCommandLineParser
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow

from structs.result import Result
from ui.tabs import TabMenu
from util.db import DBInterface
from util.logger import CLogger

load_dotenv()
log = CLogger().get_logger()

project_root = Path(__file__).resolve().parent.parent
ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


def args_parser(app) -> [str, str]:
    """
    Helper function to parse CLI args.
    Default environment variables will be set in the .env file.
    """
    parser = QCommandLineParser()
    parser.addHelpOption()
    parser.addVersionOption()

    debug_option = QCommandLineOption(["d", "debug"], "Set logging to debug.")
    parser.addOption(debug_option)

    parser.process(app)

    parser.isSet(debug_option)

    if parser.isSet(debug_option):
        BUILD = "DEBUG"
        DB = os.environ.get("DB")
        log.info("BUILD: " + BUILD)
    else:
        BUILD = os.environ.get("BUILD")
        log.info("BUILD: " + BUILD)
        DB = os.environ.get("DB")

    return [BUILD, DB]


class MainWindow(QMainWindow):
    def __init__(self, BUILD, DB):
        super().__init__()

        if BUILD == "DEBUG":
            log.info("Main Window: %s", BUILD)

        self.setWindowTitle("Time Sheet App")

        self.tab_menu = TabMenu(BUILD)

        # Menu
        open_button = QAction("Open", self)
        open_button.setStatusTip("Open a file")
        open_button_connect = open_button.triggered.connect
        open_button_connect(self.tab_menu.table_widget.open_file_dialog)

        export_button = QAction("Export", self)
        export_button.setStatusTip(
            "Export database into a compressed dump file")
        export_button_connect = export_button.triggered.connect
        export_button_connect(self.tab_menu.table_widget.export_button_action)

        import_button = QAction("Import", self)
        import_button.setStatusTip(
            "Import compressed dump file to use as database")
        import_button_connect = import_button.triggered.connect
        import_button_connect(self.tab_menu.table_widget.import_button_action)

        close_button = QAction("Close", self)
        close_button.setStatusTip("Close current view")
        close_button.triggered.connect(self.close_gracefully)

        menu = self.menuBar()

        file_menu = menu.addMenu("&File")

        file_menu.addAction(export_button)
        file_menu.addSeparator()
        file_menu.addAction(import_button)
        file_menu.addSeparator()
        file_menu.addAction(open_button)
        file_menu.addSeparator()

        file_menu.addAction(close_button)

        self.app_setup(BUILD, DB)

        self.setCentralWidget(self.tab_menu)

    def close_gracefully(self):
        """
        Closes application gracefully once backup is generated.
        """
        try:
            log.info("Creating backup...")

            result = DBInterface().dump_db_and_zip()
            DBInterface().close()

            if result == ERROR:
                raise Exception("Failed to create backup")

            log.info("Backup Successfully Created")

        except Exception as e:
            log.error(
                "Couldn't close application gracefully: %s | %s",
                type(e).__name__,
                e.args,
            )

        finally:
            log.info("Application Closed")
            self.close()

    def app_setup(self, BUILD: str, DB: str):

        db = DBInterface()
        result = db.initialize_db()

        if result == ERROR:
            self.tab_menu.table_widget.status_label.setText(
                "App started with blank database.")

        if isinstance(result, list):
            self.tab_menu.table_widget.status_label.setText(
                "App started Successfully")


if __name__ == "__main__":
    args = sys.argv
    app = QApplication(args)
    app.setApplicationName("Timesheet Analyzer")
    app.setApplicationVersion("0.0.8")
    BUILD, DB = args_parser(app)

    window = MainWindow(BUILD, DB)
    window.show()
    sys.exit(app.exec())
