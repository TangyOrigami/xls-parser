import asyncio

from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime

from typing import Union, Any
from util.async_db import AsyncDBInterface
from structs.result import Result
from structs.db_result import DBResult
from util.logger import CLogger
from util.processor import Processor

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class TaskManager(QObject):

    # Coroutine Starters
    started = pyqtSignal(str)

    # Coroutine Results
    db_result = pyqtSignal(object)
    action_result = pyqtSignal(str)

    # Coroutine Finished
    done = pyqtSignal(str)

    # Refresh
    refresh = pyqtSignal()

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

    async def start_signal(self, signal: str, data: list[tuple, ...]):
        if self._task is None or self._task.done():

            if data is None:
                self._task = await asyncio.create_task(
                    self.emit_signal(signal=signal)
                )

            else:
                self._task = await asyncio.create_task(
                    self.emit_signal(signal=signal, data=data)
                )

    async def emit_signal(self, signal: str, data: Any):
        try:
            if signal == "db_result":
                log.info("signal: %s | data: %s", signal, data)
                parsed = DBResult.parse(data)
                log.info("parsed result: %s", parsed.result)
                self.db_result.emit(parsed)

            elif signal == "action_result":
                self.action_result.emit(data)

        except Exception as e:
            self.error.emit(str(e))
            log.error("Emit failure: %s", e, exc_info=True)

    def refresh_call(self):
        self.refresh.emit()

    def now(self) -> str:
        return datetime.now().strftime("%I:%M:%S")
