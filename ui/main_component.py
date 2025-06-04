import os

from qasync import asyncSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QVBoxLayout,
    QWidget,
)

from structs.result import Result
from util.logger import CLogger
from util.task_manager import TaskManager
from ui.components.top_component import TopComponent
from ui.components.mid_component import MidComponent
from ui.components.bottom_component import BottomComponent

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class MainComponent(QWidget):
    def __init__(self, manager: TaskManager):
        super().__init__()
        self.manager = manager

        # Title and search handling
        self.top_component = TopComponent(manager)

        # Table for Work Entries and Summary of Pay Period
        self.mid_component = MidComponent(manager)

        # Status of current operation
        self.bottom_component = BottomComponent(manager)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.top_component)
        main_layout.addWidget(self.mid_component)
        main_layout.addWidget(self.bottom_component)

        self.setLayout(main_layout)

    @asyncSlot()
    async def export_button_action(self):
        """
        Creates zipped dump file of the database that can be imported
        in another instance of the application to re-create the database
        with it's data.
        """

        try:
            file_path = QFileDialog.getExistingDirectory(
                self, "Select directory to save backup to", os.getcwd()
            )

            if file_path:
                log.info("File Location: %s", file_path)
                await self.manager.start_query(method_name="dump_db_and_zip", args=file_path)

            else:
                raise Exception("Invalid file path")

        except Exception as e:
            log.error(
                "Error during dump and compression: %s | %s",
                type(e).__name__,
                e.args,
            )

    @asyncSlot()
    async def import_button_action(self):
        """
        Creates zipped dump file of the database that can be imported
        in another instance of the application to re-create the database.
        """
        try:
            file_path = QFileDialog.getOpenFileName(
                self, "Select compressed dump file", "", "*.zip"
            )

            if file_path:

                await self.manager.start_query(method_name="initialize_db_from_zip", args=file_path[0])

            else:
                raise "Invalid file path"

        except Exception as e:
            log.error(
                "Error during dump and compression: %s | %s",
                type(e).__name__,
                e.args,
            )

    def make_combo_searchable(self, combo: QComboBox):
        # TODO:
        # Make this a fuzz search
        log.info("clicked")

    @asyncSlot()
    async def refresh_choice(self):
        log.info("clicked")

    async def ppd_filler(self):
        log.info("clicked")

    @asyncSlot()
    async def ppd_choice(self, date: str):
        log.info("clicked")

    @asyncSlot()
    async def employee_filler(self, date: str):
        log.info("clicked")

    @asyncSlot()
    async def employee_choice(self, employee: str):
        log.info("clicked")

    @asyncSlot()
    async def populate_main(self, employee: tuple, selected_date: str):
        log.info("clicked")

    async def __add_cell_value(self, row: int, col: int, value):
        log.info("added cell")
