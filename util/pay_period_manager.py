from structs.result import Result
from util.async_db import AsyncDBInterface
from util.logger import CLogger

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class PayPeriodManager:
    async def get_pay_period_dates(self) -> list[str]:
        async with AsyncDBInterface() as db:
            dates = await db._read_pay_period_dates()

            if dates == ERROR:
                raise RuntimeError(
                    f"Failed to find dates for {dates}")

        return [d[0] for d in dates]

    async def get_employee_names_by_date(self, date: str) -> list[str]:
        async with AsyncDBInterface() as db:
            pp_ids = await db._read_pay_period_id_by_date(args=date)

            if pp_ids == ERROR:
                raise RuntimeError(
                    f"Failed to find employee ID for {pp_ids}")

            names = []

            for pp_id in pp_ids:
                emp_ids = await db._read_employee_ids(args=pp_id)

                for emp_id in emp_ids:
                    name_tuple = db._read_employee_name(args=emp_id)

                    if name_tuple == ERROR:
                        raise RuntimeError(
                            f"Failed to find employee ID for {pp_ids}")

                    full_name = " ".join(" ".join(name_tuple).split())
                    names.append(full_name)

        return names

    async def get_employee_id(self, full_name: tuple) -> int:
        async with AsyncDBInterface() as db:
            result = await db._read_employee_id(args=full_name)

            if result == ERROR or not result:
                raise RuntimeError(
                    f"Failed to find employee ID for {full_name}")

        return result[0][0]

    async def get_pay_period_id(self, emp_id: int, date: str) -> int:
        async with AsyncDBInterface() as db:
            result = await db._read_pay_period_id(args=(emp_id, date))

            if result == ERROR or not result:
                raise RuntimeError("Failed to find pay period ID")

        return result[0][0]

    async def get_work_entries(self, pp_id: int) -> list[tuple[str, float]]:
        async with AsyncDBInterface() as db:
            result = await db._read_work_entries(args=(pp_id,))

            if result == ERROR:
                raise RuntimeError(
                    f"Failed to read work entries for PayPeriodID: {pp_id}")

        return result

    async def get_default_date(self) -> str:
        async with AsyncDBInterface() as db:
            result = await db._default_date()

            if result == ERROR or not result:
                raise RuntimeError(
                    "Failed to retrieve async default pay period date")

        return result[0][0]

    async def get_default_employee(self) -> str:
        async with AsyncDBInterface() as db:
            result = await db._default_employee()

            if result == ERROR or not result:
                raise RuntimeError(
                    "Failed to retrieve async default pay period date")

        return result[0]

    # 🔒 Private helpers

    async def _get_pay_period_ids_by_date(self, date: str) -> list[int]:
        async with AsyncDBInterface() as db:
            result = await db._read_pay_period_ids(args=(date,))

            if result == ERROR or not result:
                raise RuntimeError(f"Failed to get pay period IDs for {date}")

        return [pp_id[0] for pp_id in result]

    async def _get_employee_ids_by_pp(self, pp_id: int) -> list[int]:
        async with AsyncDBInterface() as db:
            result = await db._read_employee_ids(args=(pp_id,))

            if result == ERROR or not result:
                raise RuntimeError(
                    f"Failed to get employee IDs for PayPeriod {pp_id}")

        return [eid[0] for eid in result]

    async def _get_employee_name_by_id(self, emp_id: int) -> tuple[str, str, str]:
        async with AsyncDBInterface() as db:
            result = await db._read_employee_name(args=(emp_id,))

            if result == ERROR or not result:
                raise RuntimeError(
                    f"Failed to get name for EmployeeID {emp_id}")

        return result[0]
