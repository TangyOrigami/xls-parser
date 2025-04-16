from util.db import DBInterface
from datetime import datetime
from util.logger import CLogger
from structs.time_type import TimeType

log = CLogger().get_logger()


class WorkEntry:
    def __init__(self, pay_period_id: int, work_date: datetime,
                 hours: float, time_type: TimeType, BUILD: str, DB: str):

        db = DBInterface(DB)

        args = (pay_period_id, work_date, hours, time_type)

        self.__save_work_entry(BUILD=BUILD, db=db, args=args)

        self.work_entry_id = self.__get_work_entry_id(
            BUILD=BUILD, db=db, args=args)

        self.pay_period_id = pay_period_id
        self.work_date = work_date
        self.hours = hours
        self.time_type = time_type

    def __save_work_entry(self, BUILD: str, db: str, args: tuple):
        log.error("Not Yet Implemented")
        raise

    def __get_work_entry_id(self, BUILD: str, db: str, args: tuple):
        log.error("Not Yet Implemented")
        raise
