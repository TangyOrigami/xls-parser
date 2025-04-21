from datetime import datetime
from util.db import DBInterface
from util.logger import CLogger

log = CLogger().get_logger()


class Comments:
    def __init__(self,
                 pay_period_id: int,
                 employee_id: int,
                 date: datetime,
                 punch_in_comment: str,
                 punch_out_comment: str,
                 special_pay_comment: str,
                 BUILD: str,
                 DB: str):

        db = DBInterface(DB)

        args = (
            pay_period_id,
            employee_id,
            date,
            punch_in_comment,
            punch_out_comment,
            special_pay_comment
        )

        self.__save_comment(BUILD=BUILD, db=db, args=args)

        self.comment_id = self.__get_comment_id(
            BUILD=BUILD, db=db, args=args)

        self.date = date
        self.pay_period_id = pay_period_id
        self.employee_id = employee_id
        self.punch_in_comment = punch_in_comment
        self.punch_out_comment = punch_out_comment
        self.special_pay_comment = special_pay_comment

    def __save_comment(self, BUILD: str, db: DBInterface, args: tuple):
        db.save_comment(BUILD=BUILD, args=args)

    def __get_comment_id(self, BUILD: str, db: DBInterface, args: tuple):
        result = db._read_comment_id(BUILD=BUILD, args=args)

        return result
