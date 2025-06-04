from structs.result import Result
from util.async_db import AsyncDBInterface
from util.logger import CLogger

log = CLogger().get_logger()

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS


class Employee:
    def __init__(self, first_name, middle_name, last_name, group, employee_id):
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.group = group
        self.employee_id = employee_id

    @classmethod
    async def create(cls, name: dict, group: str):
        first_name, middle_name, last_name = cls.__split_name(name)

        args = (first_name, middle_name, last_name, group)

        async with AsyncDBInterface() as db:
            result = await db.save_employee(args=args)

            if result == ERROR:
                raise Exception("Failed to save user.")

            id_result = await db._read_employee_id(args=args[:3])

            if id_result == ERROR or not id_result:
                raise Exception("Failed to fetch user ID.")

            employee_id = int(id_result[0][0])

        return cls(first_name, middle_name, last_name, group, employee_id)

    @staticmethod
    def __split_name(name: dict):
        first_name = name.get("First Name", "").strip()
        middle_name = name.get("Middle Name", "").strip()
        last_name = " ".join(name.get("Last Name", [])).strip()
        return first_name, middle_name, last_name
