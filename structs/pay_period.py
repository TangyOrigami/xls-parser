from datetime import datetime
from util.db import DBInterface
from util.logger import CLogger

logger = CLogger().get_logger()


class PayPeriod:
    def __init__(self,
                 employee_id: int,
                 start_date: datetime,
                 end_date: datetime,
                 BUILD: str,
                 DB: str):

        db = DBInterface(DB)

        args = (employee_id, start_date, end_date)

        self.__save_pay_period(BUILD=BUILD, db=db, args=args)

        self.pay_period_id = self.__get_pay_period_id(
            BUILD=BUILD, db=db, args=args)

        self.employee_id = employee_id
        self.start_date = start_date
        self.end_date = end_date

    def __save_pay_period(self, BUILD: str, db: DBInterface, args: tuple):
        db.save_pay_period(BUILD=BUILD, args=(args))

    def __get_pay_period_id(self, BUILD: str, db: DBInterface, args: tuple):
        result = db._read_pay_period_id(BUILD=BUILD, args=(args))[0][0]

        return result
