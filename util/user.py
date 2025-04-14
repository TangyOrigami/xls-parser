import re
from datetime import datetime, timedelta
from util.db import DBInterface
from util.logger import CLogger

logger = CLogger().get_logger()


class User:
    '''
        User object that creates an interface
        of the users' logged hours.
    '''

    def __init__(self, name, group, report, start_date, comments, BUILD, DB):
        '''
            User Interface
        '''
        self.db = DBInterface(DB)

        # USER DETAILS
        self.name, self.first_name, self.middle_name, self.last_name = self.get_full_name(
            name, BUILD)

        self.group = group
        self.report = report
        self.comments = comments
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=14)

        self.args = (self.first_name, self.middle_name,
                     self.last_name, self.group)

        self.__save_user(BUILD)

        self.id = self.__employee_id(BUILD)

        self.__save_pay_period(BUILD)

        logger.info(self.__save_work_entry(BUILD))

    def __save_user(self, BUILD):

        self.db.save_employee(BUILD=BUILD,
                              args=self.args)

    def __employee_id(self, BUILD):

        result = int(self.db._read_user_id(BUILD=BUILD, args=self.args)[0][0])

        return result

    def __save_pay_period(self, BUILD):
        this = (self.id,
                str(self.start_date),
                str(self.end_date))

        for i in this:
            logger.warn(i)

        self.db.save_pay_period(BUILD=BUILD,
                                args=(self.id,
                                      str(self.start_date),
                                      str(self.end_date))
                                )

    def __save_work_entry(self, BUILD):
        self.db._read_pay_period_id(BUILD=BUILD, args=(
            self.id, str(self.start_date), str(self.end_date)))

    def __get_hrs(self) -> [int, ...]:
        '''
            Returns the Hours that were clocked in by date.
        '''
        hours = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                hours.append(self.report[i][1])
        return hours

    def __get_report_dates(self) -> [datetime.date, ...]:
        '''
            Returns the Dates where hours were clocked in.
        '''
        dates = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                curr_date = self.report[i][0].split(
                    " ", 1)[1] + "/"+str(self.start_date.year)
                dates.append(datetime.strptime(
                    curr_date, "%m/%d/%Y").date())
        return dates

    def __weekday_filter(self) -> [datetime, ...]:
        '''
            Returns a list of the weekday dates.
        '''
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        filtered_dates = []

        for i in self.pay_period_dates():
            if i.strftime("%A") in days:
                filtered_dates.append(i)

        return filtered_dates

    def __weekend_filter(self) -> [datetime, ...]:
        '''
            Returns a list of the weekend dates.
        '''
        days = ["Saturday", "Sunday"]
        filtered_dates = []

        for i in self.pay_period_dates():
            if i.strftime("%A") in days:
                filtered_dates.append(i)

        return filtered_dates

    def __date_name(self, dates) -> [str, ...]:
        date_names = [i.strftime("%A") for i in dates]

        return date_names

    def get_hrs_wrked(self) -> {datetime.date: int, }:
        '''
            Returns a Dictionary with the dates of the pay period
            and the hours that were logged per day.

            The hash map follows this format: { Date : Hours }

            Example:

            {datetime.date(2025-1-30): 8.0, datetime.date(2025-1-31): 8.5, ...}
        '''
        weekHrs = dict()
        dates = self.__get_report_dates()
        hrs = self.__get_hrs()
        for i in range(len(dates)):
            weekHrs.update({dates[i]: hrs[i]})

        return weekHrs

    def get_weekday_hrs(self) -> {datetime.date: int, }:
        '''
            Returns Pay Period weekday (Monday-Friday) hours.

            The hash map follows this format: { Date : Hours }

            Example:

            {datetime.date(2025-1-30): 8.0, datetime.date(2025-1-31): 8.5, ...}
        '''

        week_day_dates = {}
        all_dates = self.get_hrs_wrked()
        filter = self.__weekday_filter()

        for date in all_dates.keys():
            if date in filter:
                week_day_dates.update({date: all_dates[date]})

        return week_day_dates

    def get_weekend_hrs(self) -> {datetime.date: int, }:
        '''
            Returns Pay Period weekend (Sat-Sun) hours.

            The hash map follows this format: { Date : Hours }

            Example:

            {datetime.date(2025-1-30): 8.0, datetime.date(2025-1-31): 8.5, ...}
        '''

        week_end_dates = {}
        all_dates = self.get_hrs_wrked()
        filter = self.__weekend_filter()

        for date in all_dates.keys():
            if date in filter:
                week_end_dates.update({date: all_dates[date]})

        return week_end_dates

    def get_ot_logged(self) -> {datetime.date: int, }:
        '''
            Returns Over Time that was logged.
        '''
        total = sum(self.get_hrs_wrked().values())

        if total < 80.0:
            return {}

        otEarned = {}

        for i in self.get_weekday_hrs().keys():
            curr = self.get_weekday_hrs()[i]-8.0
            otEarned.update({i: curr})

        return otEarned

    def pay_period_dates(self) -> [datetime.date, ...]:
        dates = []

        for i in range(14):
            dates.append(self.start_date + timedelta(days=i))

        return dates

    def get_full_name(self, name, BUILD):
        full_name = ''
        first_name = ''
        middle_name = ''
        last_name = ''

        for i in name:
            if i == "Last Name":
                if BUILD == "DEBUG":
                    logger.warn("IN %s MODE", BUILD)
                    logger.info(' '.join(name[i]))

                last_name = ' '.join(name[i]).strip()
                full_name = full_name + last_name + " "

            elif i == "Middle Name":
                if name[i] == "":
                    pass

                else:
                    if BUILD == "DEBUG":
                        logger.warn("IN %s MODE", BUILD)
                        logger.info(name[i])

                    middle_name = name[i].strip()
                    full_name = full_name + middle_name + " "

            else:
                if BUILD == "DEBUG":
                    logger.warn("IN %s MODE", BUILD)
                    logger.info(name[i])

                first_name = name[i].strip()
                full_name = full_name + first_name + " "

        return full_name.strip(), first_name, middle_name, last_name

    def _print_user_info(self):

        name = f"\nName: \t{self.name.strip()}\n"
        group = f"Group: \t{self.group}\n"
        date = f"Date: \t{self.start_date}\n"
        comments = f"Cmnts: \t{self.comments}\n"
        pay_period = f"PP: \t{str(self.__weekday_filter())}\n"
        total = f"Total: \t{sum(self.get_hrs_wrked().values())}\n"
        days = f"Days: \t{list(self.get_hrs_wrked().keys())}\n"
        hours = f"Hours: \t{list(self.get_hrs_wrked().values())}\n"
        week_day = f"WD: \t{list(self.get_weekday_hrs())}\n"
        week_end = f"WE: \t{list(self.get_weekend_hrs())}\n"
        over_time = f"OT: \t{list(self.get_ot_logged())}\n"

        logger.info(name + group + date + comments + pay_period + total +
                    days + hours + week_day + week_end + over_time)
