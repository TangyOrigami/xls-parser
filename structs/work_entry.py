from datetime import datetime

from structs.result import Result
from util.async_db import AsyncDBInterface
from util.logger import CLogger

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class WorkEntry:
    def __init__(self, pay_period_id: int, work_date: datetime, hours: float, work_entry_id: int):

        self.pay_period_id = pay_period_id
        self.work_date = work_date
        self.hours = hours
        self.work_entry_id = work_entry_id

    @classmethod
    async def create(cls, pay_period_id: int, work_date: datetime, hours: float, BUILD: str
                     ):
        args = (pay_period_id, work_date, hours)

        async with AsyncDBInterface() as db:
            result = await db.save_work_entry(args)

            if result == ERROR:
                raise Exception("Failed to save work entry.")

            id_result = await db._read_work_entry_id(args=args)

            if id_result == ERROR or not id_result:
                raise Exception("Failed to fetch work entry ID.")

            work_entry_id = int(id_result[0][0])

        return cls(
            pay_period_id=pay_period_id,
            work_date=work_date,
            hours=hours,
            work_entry_id=work_entry_id
        )
