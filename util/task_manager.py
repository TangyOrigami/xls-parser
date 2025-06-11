import asyncio

from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime

from typing import Union
from util.async_db import AsyncDBInterface
from structs.result import Result
from util.logger import CLogger
from util.processor import Processor

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class TaskManager(QObject):

    # Coroutine Starters
    started = pyqtSignal(str)

    # TODO:
    # Implement all signals
    # Coroutine Results
    db_result = pyqtSignal(object)
    db_dates = pyqtSignal(object)
    db_groups = pyqtSignal(object)
    db_names = pyqtSignal(object)
    db_work_entry = pyqtSignal(object)
    db_comment = pyqtSignal(object)
    action_result = pyqtSignal(str)
    init_summary = pyqtSignal()
    init_result = pyqtSignal(object)
    init_finished = pyqtSignal()

    # Coroutine Finished
    done = pyqtSignal(str)

    # Refresh
    refresh = pyqtSignal(str)

    # Error Handling
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self._task = None

    async def db_init(self):
        self.started.emit(f"[{self.now()}] Starting DB...")

        try:
            async with AsyncDBInterface() as db:
                result = await db.initialize_db()

                if result is None or result == ERROR:
                    raise Exception(f"Error starting DB: {result}")

            self.done.emit(f"[{self.now()}] Successfully Started DB!")
            self.init_finished.emit()

        except Exception as e:
            self.error.emit(f"[{self.now()}] {str(e)}")
            log.error("Failed to initialize DB: %s", str(e))

    async def start_close_db(self):
        if self._task is None or self._task.done():

            self._task = await asyncio.create_task(
                self.close_db_gracefully()
            )

    async def close_db_gracefully(self):
        self.started.emit(f"[{self.now()}] Closing Application...")

        try:
            async with AsyncDBInterface() as db:

                result = await db.dump_db_and_zip()
                if result == ERROR or None:
                    raise Exception("Failed to backup DB")

                result = await db.close()
                if result == ERROR or None:
                    raise Exception("Error closing DB")

            self.started.emit(f"[{self.now()}] Closed DB.")

        except Exception as e:
            self.error.emit(str(e))
            log.error("Failed to close DB: %s", str(e))

    async def start_query(self, method_name: str, args: Union[tuple, str] = None):
        if self._task is None or self._task.done():

            if args is None:
                self._task = await asyncio.create_task(
                    self.query_db(method_name=method_name)
                )

            else:
                self._task = await asyncio.create_task(
                    self.query_db(method_name=method_name, args=args)
                )

    async def query_db(self,
                       method_name: str,
                       args: Union[tuple, str] = None
                       ):
        self.started.emit(f"[{self.now()}] Querying DB...")

        try:
            async with AsyncDBInterface() as db:
                method = getattr(db, method_name)

                if args is None:
                    data = await method()
                    if data == ERROR or data is None:
                        raise Exception(
                            f"Failed to Query Data: {method_name}")

                else:
                    data = await method(args)
                    if data == ERROR or data is None:
                        raise Exception(
                            f"{method_name} with args {args} failed")

            self.db_result.emit(data)
            self.done.emit(f"[{self.now()}] Successfully Queried DB!")

        except Exception as e:
            self.error.emit(str(e))
            log.error("Failed to process file: %s", str(e))

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
                self.db_dates.emit(dates_result)

                groups_result = await db.read_groups()

                if groups_result == ERROR or groups_result is None:
                    raise Exception("Groups not found.")
                self.db_groups.emit(groups_result)

        except Exception as e:
            self.error.emit(str(e))
            log.error("Failed to process file: %s", str(e))

    async def start_employee_combo_box_query(self, args: str):
        if self._task is None or self._task.done():

            self._task = await asyncio.create_task(
                self.employee_combo_box_query(args=args)
            )

    async def employee_combo_box_query(self, args: str):
        try:
            async with AsyncDBInterface() as db:
                names = await db.read_names(args=(args, ))

                if names == ERROR or names is None:
                    raise Exception("Employee names not found.")
                self.db_names.emit(names)

        except Exception as e:
            self.error.emit(str(e))
            log.error("Failed to process file: %s", str(e))

    async def start_work_entry_query(self, args: tuple, start_date: str):
        if self._task is None or self._task.done():

            self._task = await asyncio.create_task(
                self.work_entry_query(name=args, start_date=start_date)
            )

    async def work_entry_query(self, name: tuple, start_date: str):
        self.started.emit(
            f"[{self.now()}] Querying for: {' '.join(' '.join(name).split())}")

        try:
            async with AsyncDBInterface() as db:
                employee_id = await db._read_employee_id(args=name)

                if employee_id == ERROR or employee_id is None:
                    raise Exception("employee_id not found.")

                pp_id = await db._read_pay_period_id(
                    args=(employee_id[0][0], start_date)
                )

                if pp_id == ERROR or pp_id is None:
                    raise Exception("pay_period_id not found.")

                work_entries = await db._read_work_entries(args=(pp_id[0][0], ))

                if work_entries == ERROR or work_entries is None:
                    raise Exception("pay_period_id not found.")

                self.db_work_entry.emit([work_entries, start_date])

        except Exception as e:
            self.error.emit(str(e))
            log.error("Failed to process file: %s", str(e))

    def start_init_summary(self):
        self.init_summary.emit()

    async def start_processing(self, file_path: str = None):
        if self._task is None or self._task.done():
            self._task = await asyncio.create_task(
                self.process_file(file_path=file_path)
            )

    async def process_file(self, file_path: str = None):
        self.started.emit(
            f"[{self.now()}] Started Processing File: {file_path}"
        )

        try:
            result = await Processor().extract_data(file_path=file_path)
            if result == ERROR or result is None:
                raise Exception(
                    f"{result}")

            self.action_result.emit(f"Finished processing {file_path}")
            self.done.emit(f"[{self.now()}] Finished Processing")

        except Exception as e:
            self.error.emit(str(e))
            log.error("Failed to process file: %s", str(e))

    def refresh_call(self):
        self.refresh.emit(f"[{self.now()}] App Refreshed")

    def now(self) -> str:
        return datetime.now().strftime("%I:%M:%S %p")
