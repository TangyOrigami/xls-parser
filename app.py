import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from PyQt6.QtCore import QCommandLineOption, QCommandLineParser
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow

from structs.result import Result as r
from ui.tabs import TabMenu
from util.db import DBInterface
from util.logger import CLogger

load_dotenv()
log = CLogger().get_logger()

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


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
        open_button.triggered.connect(self.tab_menu.table_widget.open_file_dialog)

        export_button = QAction("Export as", self)
        export_button.setStatusTip("Export database")
        export_button.triggered.connect(self.tab_menu.table_widget.export_button_action)

        import_button = QAction("Import", self)
        import_button.setStatusTip("Import database")
        import_button.triggered.connect(self.tab_menu.table_widget.import_button_action)

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

    def import_button_action(self, s):
        """
        Injests a dump file and re-creates the database.
        """
        print("import", s)

    def close_gracefully(self):
        """
        Closes gracefully application once backup is generated.
        """
        try:
            log.info("Creating backup...")
            project_root = Path(__file__).resolve().parent.parent
            target_db_path = project_root / "app.db"
            backup_db_path = project_root / "app_backup.db"

            result = DBInterface().create_backup(
                target_db_path=target_db_path, backup_db_path=backup_db_path
            )

            if result == r.ERROR:
                raise Exception("Failed to create backup")
        except Exception as e:
            log.error(
                "Couldn't close application gracefully: %s | %s",
                type(e).__name__,
                e.args,
            )
        finally:
            log.info("Backup Successfully Created")
            self.close()

    def app_setup(self, BUILD: str, DB: str):
        db = DBInterface(DB)

        db.initialize_db(BUILD)


if __name__ == "__main__":
    args = sys.argv
    app = QApplication(args)
    app.setApplicationName("Timesheet Analyzer")
    app.setApplicationVersion("0.0.5")
    BUILD, DB = args_parser(app)

    window = MainWindow(BUILD, DB)
    window.show()
    sys.exit(app.exec())
