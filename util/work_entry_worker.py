import re
from datetime import datetime, timedelta
from util.db import DBInterface
from util.logger import CLogger
from structs.work_entry import WorkEntry

log = CLogger().get_logger()


class WorkEntryWorker:
    '''
        Worker with an interface to handle Work Entries.
    '''

    def __init__(self, pay_period_id: int, report: list,
                 start_date: datetime, BUILD: str, DB: str):
        '''
            Worker to handle Work Entries.
        '''
        self.db = DBInterface(DB)

        self.pay_period_id = pay_period_id
        self.report = report
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=14)

    def __extract_hrs(self) -> [int, ...]:
        '''
            Returns the Hours that were clocked in by date.
        '''
        hours = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                hours.append(self.report[i][1])
        return hours

    def __extract_report_dates(self) -> [datetime.date, ...]:
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
        '''
            Returns the days of the week that dates.
        '''
        date_names = [i.strftime("%A") for i in dates]

        return date_names

    def extract_hrs_wrked(self) -> {datetime.date: int, }:
        '''
            Returns a Dictionary with the dates of the pay period
            and the hours that were logged per day.

            The hash map follows this format: { Date : Hours }

            Example:

            {datetime.date(2025-1-30): 8.0, datetime.date(2025-1-31): 8.5, ...}
        '''

        weekHrs = dict()
        dates = self.__extract_report_dates()
        hrs = self.__extract_hrs()

        for i in range(len(dates)):
            weekHrs.update({dates[i]: hrs[i]})

        return weekHrs

    def extract_work_entries(self, BUILD: str, DB: str) -> {datetime.date: int}:
        '''
            Returns a list of WorkEntry objects for a given pay period.
        '''
        raw_hrs = self.extract_hrs_wrked()
        counter = 0
        tracker = []

        for i in raw_hrs.keys():
            counter += raw_hrs[i]
            if counter <= 0.00:
                tracker = []
            if counter > 0.00:
                work_entry = WorkEntry(
                    pay_period_id=self.pay_period_id,
                    work_date=i,
                    hours=raw_hrs[i],
                    BUILD=BUILD,
                    DB=DB
                )
                tracker.append(work_entry)

        return tracker

    def extract_weekday_hrs(self) -> {datetime.date: int, }:
        '''
            Returns Pay Period weekday (Monday-Friday) hours.

            The hash map follows this format: { Date : Hours }

            Example:

            {datetime.date(2025-1-30): 8.0, datetime.date(2025-1-31): 8.5, ...}
        '''

        week_day_dates = {}
        all_dates = self.extract_hrs_wrked()
        filter = self.__weekday_filter()

        for date in all_dates.keys():
            if date in filter:
                week_day_dates.update({date: all_dates[date]})

        return week_day_dates

    def extract_weekend_hrs(self) -> {datetime.date: int, }:
        '''
            Returns Pay Period weekend (Sat-Sun) hours.

            The hash map follows this format: { Date : Hours }

            Example:

            {datetime.date(2025-1-30): 8.0, datetime.date(2025-1-31): 8.5, ...}
        '''

        week_end_dates = {}
        all_dates = self.extract_hrs_wrked()
        filter = self.__weekend_filter()

        for date in all_dates.keys():
            if date in filter:
                week_end_dates.update({date: all_dates[date]})

        return week_end_dates

    def extract_ot_logged(self) -> {datetime.date: int}:
        '''
            Returns Over Time that was logged.
        '''
        total = sum(self.extract_hrs_wrked().values())

        if total < 80.0:
            return {}

        otEarned = {}

        for i in self.extract_weekday_hrs().keys():
            curr = self.extract_weekday_hrs()[i]-8.0
            otEarned.update({i: curr})

        return otEarned

    def pay_period_dates(self) -> [datetime.date, ...]:
        dates = []

        for i in range(14):
            dates.append(self.start_date + timedelta(days=i))

        return dates

    def _print_object_info(self):

        pay_period_id = f"\nPPID: \t{self.pay_period_id}\n"
        date = f"Date: \t{self.start_date}\n"
        pay_period = f"PP: \t{str(self.__weekday_filter())}\n"
        total = f"Total: \t{sum(self.extract_hrs_wrked().values())}\n"
        days = f"Days: \t{list(self.extract_hrs_wrked().keys())}\n"
        hours = f"Hours: \t{list(self.extract_hrs_wrked().values())}\n"
        week_day = f"WD: \t{list(self.extract_weekday_hrs())}\n"
        week_end = f"WE: \t{list(self.extract_weekend_hrs())}\n"
        over_time = f"OT: \t{list(self.extract_ot_logged())}\n"

        log.info(pay_period_id + date + pay_period + total +
                 days + hours + week_day + week_end + over_time)
