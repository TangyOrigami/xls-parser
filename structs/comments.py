from datetime import datetime

from structs.result import Result
from util.async_db import AsyncDBInterface
from util.logger import CLogger

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class Comments:
    def __init__(
        self,
        comment_id: int,
        pay_period_id: int,
        employee_id: int,
        date: datetime,
        punch_in_comment: str,
        punch_out_comment: str,
        special_pay_comment: str,
    ):
        self.comment_id = comment_id
        self.date = date
        self.pay_period_id = pay_period_id
        self.employee_id = employee_id
        self.punch_in_comment = punch_in_comment
        self.punch_out_comment = punch_out_comment
        self.special_pay_comment = special_pay_comment

    @classmethod
    async def create(cls,
                     pay_period_id,
                     employee_id,
                     date,
                     punch_in_comment,
                     punch_out_comment,
                     special_pay_comment,
                     ):

        async with AsyncDBInterface() as db:
            args = (
                pay_period_id,
                employee_id,
                str(date),
                punch_in_comment,
                punch_out_comment,
                special_pay_comment,
            )

            result = await db.save_comment(args=args)

            if result == ERROR or not result:
                log.error(f"Failed to save comment: {args}")
                raise Exception(f"Failed to save comment: {args}")

            args = (
                pay_period_id,
                employee_id,
                str(date),
            )

            id_result = await db._read_comment_id(args=args)

            if id_result == ERROR or not id_result:
                log.error(f"Failed to fetch comment ID. args: {args}")
                raise Exception(f"Failed to fetch comment ID. args: {args}")

            comment_id = int(id_result[0][0])

        return cls(
            comment_id=comment_id,
            pay_period_id=pay_period_id,
            employee_id=employee_id,
            date=date,
            punch_in_comment=punch_in_comment,
            punch_out_comment=punch_out_comment,
            special_pay_comment=special_pay_comment,
        )
