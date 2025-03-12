import xlrd
import re
from datetime import datetime

workbook = xlrd.open_workbook('MAIN OFFICE DETAIL PAYROLL REPORT.xls')


class User:
    '''
        User object that creates an interface
        of the users' logged hours.
    '''

    def __init__(self, name, report):
        '''
            User Interface
        '''
        self.name = str(name)
        self.report = report
        self.date = datetime.now().strftime("%m-%d-%Y")

    def __get_hrs(self):
        '''
            Returns the Hours that were clocked in by date.
        '''
        hours = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                hours.append(self.report[i][1])
        return hours

    def __get_dates(self):
        '''
            Returns the Dates where hours were clocked in.
        '''
        dates = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                dates.append(self.report[i][0])
        return dates

    def get_hrs_wrked(self):
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

    def get_weekday_hrs(self):
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

    def get_weekend_hrs(self):
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

    def get_ot_logged(self):
        total = sum(self.get_hrs_wrked().values())

        if total < 80.0:
            return {}

        otEarned = {}

        for i in self.get_weekday_hrs().keys():
            curr = self.get_weekday_hrs()[i]-8.0
            otEarned.update({i: curr})

        return otEarned


def hrsFormatter(arr):
    if arr == "":
        return 0

    else:
        arr = arr.split(":")
        stack = [float(i) for i in arr]

        if stack[1] == 15:
            stack[1] = .25
        elif stack[1] == 30:
            stack[1] = .50
        elif stack[1] == 45:
            stack[1] = .75

        return stack[0] + stack[1]


def func(sheet):
    weeklyHrs = []
    for i in range(sheet.nrows):
        if sheet.cell_value(rowx=i, colx=1) == "User Name:":
            userStats = [sheet.cell_value(rowx=i, colx=3)]
            tableStart = i

    for i in range(sheet.nrows):
        if sheet.cell_value(rowx=i, colx=1) == "User Name:":
            userStats = [sheet.cell_value(rowx=i, colx=3)]

    for j in range(sheet.ncols):
        if sheet.cell_value(rowx=tableStart+2, colx=j) == "DAILY":
            for k in range(tableStart+3, sheet.nrows):
                unformattedHrs = str(sheet.cell_value(rowx=k, colx=j))
                date = str(sheet.cell_value(rowx=k, colx=1))
                formattedHrs = hrsFormatter(unformattedHrs)
                weeklyHrs.append([date, formattedHrs])

    for i in range(len(weeklyHrs)):
        if weeklyHrs[i][1] != 0 and weeklyHrs[i][1] < 24:
            userStats.append(weeklyHrs[i])

    return userStats


users = []

for i in range(0, workbook.nsheets):
    currUser = func(workbook.sheet_by_index(i))
    if len(currUser) != 1:
        users.append(User(currUser[0], currUser[1:]))

for i in range(len(users)):
    gp = users[i]

    actualWeekly = sum(gp.get_weekday_hrs().values())
    weekend = sum(gp.get_weekend_hrs().values())
    otWeekly = sum(gp.get_ot_logged().values())

    print(f"{i}, '{gp.name}'")
    print("Total:\t", sum(gp.get_hrs_wrked().values()),
          "\nRT:\t", actualWeekly - otWeekly,
          "\nOT:\t", otWeekly, "\nWknd:\t", weekend)
    print()


'''
    TODO:
        1. Make a function that will iterate over the report to find a value.
            a. func will iterate over a range to find target
            b. func(minx, miny, maxx, maxy, target)
            c. this is a nicer abstraction

        2. Get date from report and save it to User object
            - Cell where date is recorded: (33, 18)

        ?. Design schema for saving data and creating relations, RDBMS.
'''
