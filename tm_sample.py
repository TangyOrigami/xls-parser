import asyncio

from PyQt6.QtCore import QObject, pyqtSignal

from util.async_db import AsyncDBInterface
from structs.result import Result
from util.logger import CLogger

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class TaskManager(QObject):

    # Started Signals
    started = pyqtSignal(str)

    # TODO:
    # Implement all signals
    # Result Signals
    db_dates = pyqtSignal(object)
    db_groups = pyqtSignal(object)
    db_names = pyqtSignal(object)
    db_work_entry = pyqtSignal(object)
    db_comment = pyqtSignal(object)

    # Utility Signals
    done = pyqtSignal(str)
    refresh = pyqtSignal(str)

    # Error Signals
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self._task = None

    async def start_combo_box_query(self):
        if self._task is None or self._task.done():

            self._task = await asyncio.create_task(
                self.combo_box_query_db()
            )

    async def combo_box_query_db(self):
        try:
            async with AsyncDBInterface() as db:
                dates_result = await db.read_dates()

                if dates_result == ERROR or dates_result is None:
                    raise Exception("Dates not found.")
                log.info("dates: %s", dates_result)
                self.db_dates.emit(dates_result)

                groups_result = await db.read_groups()

                if groups_result == ERROR or groups_result is None:
                    raise Exception("Groups not found.")
                log.info("groups: %s", groups_result)
                self.db_groups.emit(groups_result)

        except Exception as e:
            self.error.emit(str(e))
            log.error("Failed to process file: %s", str(e))
