import os
import asyncio
import sys

from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from qasync import QEventLoop, asyncSlot
from PyQt6.QtCore import QCommandLineOption, QCommandLineParser, pyqtSignal, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog

from structs.result import Result
from ui.table import TableWidget
from ui.main_component import MainComponent
from util.logger import CLogger
from util.task_manager import TaskManager

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
    button_clicked = pyqtSignal()

    def __init__(self, BUILD: str, manager: TaskManager, DB: str = "app.db"):
        super().__init__()

        self.manager = manager

        if BUILD == "DEBUG":
            log.info("Main Window: %s", BUILD)

        self.setWindowTitle("Time Sheet App")

        self.new_table_widget = TableWidget()
        self.main_component = MainComponent(self.manager)

        open_button = QAction("Open File", self)
        open_button.setStatusTip("Open a report and save it to the database.")
        open_button_connect = open_button.triggered.connect
        open_button_connect(self.open_file_dialog)

        open_multiple_button = QAction("Open Files", self)
        open_multiple_button.setStatusTip(
            "Open multiple reports and save it to the database.")
        open_multiple_button_connect = open_multiple_button.triggered.connect
        open_multiple_button_connect(self.open_files_dialog)

        export_button = QAction("Export", self)
        export_button.setStatusTip(
            "Export database into a compressed dump file.")
        export_button_connect = export_button.triggered.connect
        export_button_connect(self.main_component.export_button_action)

        import_button = QAction("Import", self)
        import_button.setStatusTip(
            "Import compressed dump file to use as database. Note: This will hotswap the current database, meaning that the current database will be overwritten.")
        import_button_connect = import_button.triggered.connect
        import_button_connect(self.main_component.import_button_action)

        close_button = QAction("Exit", self)
        close_button.setStatusTip("Gracefully close application.")
        close_button.triggered.connect(self.close_gracefully)

        menu = self.menuBar()

        file_menu = menu.addMenu("&File")

        file_menu.addAction(open_button)
        file_menu.addAction(open_multiple_button)
        file_menu.addSeparator()
        file_menu.addAction(export_button)
        file_menu.addAction(import_button)
        file_menu.addSeparator()

        file_menu.addAction(close_button)

        QTimer.singleShot(0, self.safe_async_startup)

        self.setCentralWidget(self.main_component)

    def now(self) -> str:
        return datetime.now().strftime("%I:%M:%S")

    @asyncSlot()
    async def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "", "Excel Files (*.xls)"
        )

        await self.single(file_path)

    @asyncSlot()
    async def open_files_dialog(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_names, _ = file_dialog.getOpenFileNames(
            self, "Open files", "", "Excel Files (*.xls)")

        await self.multiple(file_names)

    async def single(self, file_path: str):

        if file_path:
            QApplication.processEvents()

            await self.manager.start_processing(file_path=file_path)

    async def multiple(self, file_names: list[str]):

        if file_names:

            for file_path in file_names:

                QApplication.processEvents()

                await self.manager.start_processing(
                    file_path=file_path
                )

    @asyncSlot()
    async def close_gracefully(self):
        """
        Closes application gracefully once backup is generated.
        """

        try:
            log.info("Creating backup...")

            await self.manager.close_db_gracefully()

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

    @asyncSlot()
    async def safe_async_startup(self):
        result = await self.manager.db_init()

        if result == ERROR:
            log.critical("Failed to initialize DB. Exiting.")
            QApplication.quit()
            return


def main():
    args = sys.argv
    app = QApplication(args)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    app.setApplicationName("Timesheet Analyzer")
    app.setApplicationVersion("0.0.9")

    BUILD, DB = args_parser(app)
    manager = TaskManager()

    # Start main window after loop is running
    window = MainWindow(BUILD, manager, DB)
    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
