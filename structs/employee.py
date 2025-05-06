from util.db import DBInterface
from util.logger import CLogger

log = CLogger().get_logger()


class Employee:
    """
    User object that creates an interface
    of the users' logged hours.
    """

    def __init__(self, name: str, group: str, BUILD: str):
        """
        User Interface
        """
        db = DBInterface()

        self.first_name, self.middle_name, self.last_name = self.__split_name(
            name=name, BUILD=BUILD
        )

        self.group = group

        args = (self.first_name, self.middle_name, self.last_name, self.group)

        self.__save_user(BUILD=BUILD, db=db, args=args)

        self.employee_id = self.__get_employee_id(BUILD=BUILD, db=db, args=args[:3])

    def __save_user(self, BUILD: str, db: DBInterface, args: tuple):
        db.save_employee(BUILD=BUILD, args=(args))

    def __get_employee_id(self, BUILD: str, db: DBInterface, args: tuple):
        result = int(db._read_employee_id(BUILD=BUILD, args=(args))[0][0])

        return result

    def __split_name(self, name, BUILD):
        first_name = ""
        middle_name = ""
        last_name = ""

        for i in name:
            if i == "Last Name":
                last_name = " ".join(name[i]).strip()

            elif i == "Middle Name":
                if name[i] == "":
                    pass

                else:
                    middle_name = name[i].strip()

            else:
                first_name = name[i].strip()

        return first_name, middle_name, last_name

    def _print_object_info(self):

        first_name = f"\nFirst Name: \t{self.first_name}\n"
        middle_name = f"Middle Name: \t{self.middle_name}\n"
        last_name = f"Last Name: \t{self.last_name}\n"
        employee_id = f"EID: \t{self.employee_id}\n"
        group = f"Group: \t{self.group}\n"

        log.info(first_name + middle_name + last_name + employee_id + group)
