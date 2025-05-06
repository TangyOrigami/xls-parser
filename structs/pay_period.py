from datetime import datetime, timedelta

from util.db import DBInterface
from util.logger import CLogger

log = CLogger().get_logger()


class PayPeriod:
    def __init__(self, employee_id: int, date: datetime, BUILD: str):

        db = DBInterface()

        self.start_date = date
        self.end_date = date + timedelta(days=14)

        args = (employee_id, self.start_date, self.end_date)

        self.__save_pay_period(BUILD=BUILD, db=db, args=args)

        self.pay_period_id = self.__get_pay_period_id(BUILD=BUILD, db=db, args=args[:2])

        self.employee_id = employee_id

    def __save_pay_period(self, BUILD: str, db: DBInterface, args: tuple):
        db.save_pay_period(BUILD=BUILD, args=(args))

    def __get_pay_period_id(self, BUILD: str, db: DBInterface, args: tuple):
        result = db._read_pay_period_id(BUILD=BUILD, args=(args))[0][0]

        return result

    def _print_object_info(self):

        start_date = f"\nStart Date: \t{self.start_date}\n"
        end_date = f"End Date: \t{self.end_date}\n"
        pay_period_id = f"PPID: \t{self.pay_period_id}\n"
        employee_id = f"EID: \t{self.employee_id}\n"

        log.info(start_date + end_date + pay_period_id + employee_id)
