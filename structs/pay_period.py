from datetime import datetime, timedelta

from structs.result import Result
from util.async_db import AsyncDBInterface
from util.logger import CLogger

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class PayPeriod:
    def __init__(self, employee_id: int, start_date: datetime, end_date: datetime, pay_period_id: int):
        self.employee_id = employee_id
        self.start_date = start_date
        self.end_date = end_date
        self.pay_period_id = pay_period_id

    @classmethod
    async def create(cls, employee_id: int, date: datetime):
        start_date = date
        end_date = date + timedelta(days=14)
        args = (employee_id, start_date, end_date)

        async with AsyncDBInterface() as db:
            result = await db.save_pay_period(args=args)

            if result == ERROR:
                raise Exception("Failed to save pay period.")

            id_result = await db._read_pay_period_id(args=args[:2])

            if id_result == ERROR or not id_result:
                raise Exception("Failed to fetch pay period ID.")

            pay_period_id = int(id_result[0][0])

        return cls(employee_id=employee_id, start_date=start_date, end_date=end_date, pay_period_id=pay_period_id)
