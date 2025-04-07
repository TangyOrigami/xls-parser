import re
from datetime import datetime, timedelta


class User:
    '''
        User object that creates an interface
        of the users' logged hours.
    '''

    def __init__(self, name, group, report, start_date, comments):
        '''
            User Interface
        '''
        self.name = str(name)
        self.group = str(group)
        self.report = report
        self.comments = comments
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=14)

    def __get_hrs(self) -> []:
        '''
            Returns the Hours that were clocked in by date.
        '''
        hours = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                hours.append(self.report[i][1])
        return hours

    def __get_report_dates(self) -> []:
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

    def get_hrs_wrked(self) -> {}:
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

    def get_weekday_hrs(self) -> {}:
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

    def get_weekend_hrs(self) -> {}:
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

    def get_ot_logged(self) -> {}:
        '''
            Returns Over Time that was logged.
        '''
        pass
        total = sum(self.get_hrs_wrked().values())

        if total < 80.0:
            return {}

        otEarned = {}

        for i in self.get_weekday_hrs().keys():
            curr = self.get_weekday_hrs()[i]-8.0
            otEarned.update({i: curr})

        return otEarned

    def pay_period_dates(self) -> []:
        dates = []

        for i in range(14):
            dates.append(self.start_date + timedelta(days=i))

        return dates

    def __weekday_filter(self) -> [datetime]:
        '''
            Returns a list of the weekday dates.
        '''
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        filtered_dates = []

        for i in self.pay_period_dates():
            if i.strftime("%A") in days:
                filtered_dates.append(i)

        return filtered_dates

    def __weekend_filter(self):
        '''
            Returns a list of the weekend dates.
        '''
        days = ["Saturday", "Sunday"]
        filtered_dates = []

        for i in self.pay_period_dates():
            if i.strftime("%A") in days:
                filtered_dates.append(i)

        return filtered_dates

    def __date_name(self, dates):
        date_names = [i.strftime("%A") for i in dates]

        return date_names

    def _print_user_info(self):
        print()
        print(f"Name: \t{self.name}")
        print(f"Group: \t{self.group}")
        print(f"Date: \t{self.start_date}")
        print(f"Cmnts: \t{self.comments}")
        print(f"PP: \t{str(self.__weekday_filter())}")
        print(f"Total: \t{sum(self.get_hrs_wrked().values())}")
        print(f"Days: \t{self.get_hrs_wrked().keys()}")
        print(f"Hours: \t{self.get_hrs_wrked().values()}")
        print(f"WD: \t{self.get_weekday_hrs()}")
        print(f"WE: \t{self.get_weekend_hrs()}")
