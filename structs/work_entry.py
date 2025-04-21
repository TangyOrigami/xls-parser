from util.db import DBInterface
from datetime import datetime
from util.logger import CLogger

log = CLogger().get_logger()


class WorkEntry:
    def __init__(self, pay_period_id: int, work_date: datetime,
                 hours: float, BUILD: str, DB: str):

        db = DBInterface(DB)

        args = (pay_period_id, work_date, hours)

        self.__save_work_entry(BUILD=BUILD, db=db, args=args)

        self.work_entry_id = self.__get_work_entry_id(
            BUILD=BUILD, db=db, args=args)

        self.pay_period_id = pay_period_id
        self.work_date = work_date
        self.hours = hours

    def __save_work_entry(self, BUILD: str, db: DBInterface, args: tuple):
        db.save_work_entry(BUILD=BUILD, args=args)

    def __get_work_entry_id(self, BUILD: str, db: str, args: tuple):
        result = int(db._read_work_entry_id(BUILD=BUILD, args=args)[0][0])

        return result
