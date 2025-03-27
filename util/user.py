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
                dates.append(str(datetime.strptime(
                    curr_date, "%m/%d/%Y").date()))
        return dates

    def get_hrs_wrked(self) -> {}:
        '''
            Returns a Dictionary with the dates of the pay period
            and the hours that were logged per day.

            The hash map follows this format: { Date : Hours }

            Example:
                {'2025-1-30' : 8.0, '2025-1-31' : 8.5, ...}
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
        '''
        weekDayHrs = {}

        for i in self.get_hrs_wrked().keys():
            if re.search("(Thu|Fri|Mon|Tue|Wed)", i) is not None:
                weekDayHrs.update({
                    i: self.get_hrs_wrked()[i]
                })

        return weekDayHrs

    def get_weekend_hrs(self) -> {}:
        '''
            Returns Pay Period weekend (Sat-Sun) hours.
        '''
        weekEndHrs = {}

        for i in self.get_hrs_wrked().keys():
            if re.search("(Sat|Sun)", i) is not None:
                weekEndHrs.update({
                    i: self.get_hrs_wrked()[i]
                })

        return weekEndHrs

    def get_ot_logged(self) -> {}:
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

    def pay_period_dates(self) -> []:
        dates = []

        for i in range(14):
            dates.append(str(self.start_date + timedelta(days=i)))

        return dates
