import xlrd
import re
from datetime import datetime

workbook = xlrd.open_workbook('MAIN OFFICE DETAIL PAYROLL REPORT.xls')

weekdays = "[Thu|Fri|Mon|Tue|Wed]"
weekends = "[Sat|Sun]"


class LoggedUserHrs:
    def __init__(self, name, report):
        self.name = str(name)
        self.report = report
        self.hours = self.__get_hrs_wrked()
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

    def __get_hrs_wrked(self):
        '''
            Returns a Dictionary with the date hours were
            logged as the Key and the hours as the Value.

            Example:
                {'Thu 1/30' : 8}
        '''
        weekHrs = dict()
        dates = self.__get_dates()
        hrs = self.__get_hrs()
        for i in range(len(dates)):
            weekHrs.update({dates[i]: hrs[i]})

        return weekHrs


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
            pass

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
        users.append(LoggedUserHrs(currUser[0], currUser[1:]))

gp = users[0]

print("{0}\n".format(
    sum(gp.hours.values())
))

for i in gp.hours.keys():
    print("'{0}', {1},".format(
        i, gp.hours[i]
    ))
