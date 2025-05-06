from structs.result import Result as r
from util.db import DBInterface
from util.logger import CLogger

log = CLogger().get_logger()


class PayPeriodManager:
    def __init__(self, build: str):
        self.db = DBInterface()
        self.BUILD = build

    def get_pay_period_dates(self) -> list[str]:
        dates = self.db._read_pay_period_dates(self.BUILD)
        if dates == r.ERROR:
            raise RuntimeError("Failed to retrieve pay period dates")
        return [d[0] for d in dates]

    def get_employee_names_by_date(self, date: str) -> list[str]:
        pp_ids = self._get_pay_period_ids_by_date(date)
        names = []

        for pp_id in pp_ids:
            emp_ids = self._get_employee_ids_by_pp(pp_id)
            for emp_id in emp_ids:
                name_tuple = self._get_employee_name_by_id(emp_id)
                full_name = " ".join(" ".join(name_tuple).split())
                names.append(full_name)

        return names

    def get_employee_id(self, full_name: tuple) -> int:
        result = self.db._read_employee_id(args=full_name, BUILD=self.BUILD)
        if result == r.ERROR or not result:
            raise RuntimeError(f"Failed to find employee ID for {full_name}")
        return result[0][0]

    def get_pay_period_id(self, emp_id: int, date: str) -> int:
        result = self.db._read_pay_period_id(args=(emp_id, date), BUILD=self.BUILD)
        if result == r.ERROR or not result:
            raise RuntimeError("Failed to find pay period ID")
        return result[0][0]

    def get_work_entries(self, pp_id: int) -> list[tuple[str, float]]:
        result = self.db._read_work_entries(args=(pp_id,), BUILD=self.BUILD)
        if result == r.ERROR:
            raise RuntimeError(f"Failed to read work entries for PayPeriodID {pp_id}")
        return result

    def get_default_date(self) -> str:
        result = self.db._default_date(self.BUILD)
        if result == r.ERROR or not result:
            raise RuntimeError("Failed to retrieve default pay period date")
        return result[0][0]

    def get_default_employee(self) -> str:
        result = self.db._default_employee(self.BUILD)
        if result == r.ERROR or not result:
            raise RuntimeError("Failed to retrieve default pay period date")
        return result[0]

    # 🔒 Private helpers

    def _get_pay_period_ids_by_date(self, date: str) -> list[int]:
        result = self.db._read_pay_period_ids(args=(date,), BUILD=self.BUILD)
        if result == r.ERROR or not result:
            raise RuntimeError(f"Failed to get pay period IDs for {date}")
        return [pp_id[0] for pp_id in result]

    def _get_employee_ids_by_pp(self, pp_id: int) -> list[int]:
        result = self.db._read_employee_ids(args=(pp_id,), BUILD=self.BUILD)
        if result == r.ERROR or not result:
            raise RuntimeError(f"Failed to get employee IDs for PayPeriod {pp_id}")
        return [eid[0] for eid in result]

    def _get_employee_name_by_id(self, emp_id: int) -> tuple[str, str, str]:
        result = self.db._read_employee_name(args=(emp_id,), BUILD=self.BUILD)
        if result == r.ERROR or not result:
            raise RuntimeError(f"Failed to get name for EmployeeID {emp_id}")
        return result[0]
