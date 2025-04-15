from datetime import datetime, timedelta
from util.db import DBInterface
from util.logger import CLogger


logger = CLogger().get_logger()


class Employee:
    '''
        User object that creates an interface
        of the users' logged hours.
    '''

    def __init__(self, name: str, group: str, start_date: datetime,
                 comments: str, BUILD: str, DB: str):
        '''
            User Interface
        '''
        db = DBInterface(DB)

        self.first_name, self.middle_name, self.last_name = self.__split_name(
            name=name, BUILD=BUILD)

        args = (
            self.first_name,
            self.middle_name,
            self.last_name,
            self.group
        )

        self.__save_user(BUILD=BUILD, db=db, args=args)

        self.employee_id = self.__get_employee_id(
            BUILD=BUILD, db=db, args=args)

        self.group = group
        self.comments = comments
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=14)

    def __save_user(self, BUILD: str, db: DBInterface, args: tuple):
        db.save_employee(BUILD=BUILD, args=(args))

    def __get_employee_id(self, BUILD: str, db: DBInterface, args: tuple):
        result = int(db._read_user_id(BUILD=BUILD, args=(args))[0][0])

        return result

    def __split_name(self, name, BUILD):
        first_name = ''
        middle_name = ''
        last_name = ''

        for i in name:
            if i == "Last Name":
                if BUILD == "DEBUG":
                    logger.warn("IN %s MODE", BUILD)
                    logger.info(' '.join(name[i]))

                last_name = ' '.join(name[i]).strip()

            elif i == "Middle Name":
                if name[i] == "":
                    pass

                else:
                    if BUILD == "DEBUG":
                        logger.warn("IN %s MODE", BUILD)
                        logger.info(name[i])

                    middle_name = name[i].strip()

            else:
                if BUILD == "DEBUG":
                    logger.warn("IN %s MODE", BUILD)
                    logger.info(name[i])

                first_name = name[i].strip()

        return first_name, middle_name, last_name
