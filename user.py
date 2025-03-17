import re


class User:
    '''
        User object that creates an interface
        of the users' logged hours.
    '''

    def __init__(self, name, report, date):
        '''
            User Interface
        '''
        self.name = str(name)
        self.report = report
        self.date = date

    def __get_hrs(self) -> []:
        '''
            Returns the Hours that were clocked in by date.
        '''
        hours = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                hours.append(self.report[i][1])
        return hours

    def __get_dates(self) -> []:
        '''
            Returns the Dates where hours were clocked in.
        '''
        dates = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                dates.append(self.report[i][0])
        return dates

    def get_hrs_wrked(self) -> {}:
        '''
            Returns a Dictionary with the date hours were
            logged as the Key as a String type and the
            hours as the Value as a Float.

            Example:
                {'Thu 1/30' : 8.0}
        '''
        weekHrs = dict()
        dates = self.__get_dates()
        hrs = self.__get_hrs()
        for i in range(len(dates)):
            weekHrs.update({dates[i]: hrs[i]})

        return weekHrs

    def get_weekday_hrs(self) -> {}:
        '''
            Returns Pay Period weekday hours.
            Weeks start on Thursday and end on Wednesday.
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
            Returns Pay Period weekend hours.
        '''
        weekEndHrs = {}

        for i in self.get_hrs_wrked().keys():
            if re.search("(Sat|Sun)", i) is not None:
                weekEndHrs.update({
                    i: self.get_hrs_wrked()[i]
                })

        return weekEndHrs

    def get_ot_logged(self) -> {}:
        total = sum(self.get_hrs_wrked().values())

        if total < 80.0:
            return {}

        otEarned = {}

        for i in self.get_weekday_hrs().keys():
            curr = self.get_weekday_hrs()[i]-8.0
            otEarned.update({i: curr})

        return otEarned
