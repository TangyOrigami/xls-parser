import xlrd
import re
from datetime import datetime

workbook = xlrd.open_workbook('MAIN OFFICE DETAIL PAYROLL REPORT.xls')

control = 8


class LoggedUserHrs:
    def __init__(self, name, report):
        self.name = str(name)
        self.report = report
        self.date = datetime.now().strftime("%m-%d-%Y")

    def getHrs(self):
        '''
            Returns the Hours that were clocked in.
        '''
        hours = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                hours.append(self.report[i][1])
        return hours

    def getDates(self):
        '''
            Returns the Dates where hours were clocked in.
        '''
        dates = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                dates.append(self.report[i][0])
        return dates

    def getOT(self):
        '''
            Returns OT(Over Time) hours that were clocked in.

            TODO:
                getOT() needs to account for the days they are earned for this
                to work properly
        '''

        totalHrs = self.getHrs()
        otHrs = list()
        for i in range(len(totalHrs)):
            otHrs.append(totalHrs[i]-8)
        return otHrs

    def getRT(self):
        '''
            Returns RT(Regular Time) hours that were clocked in.

            WARNING:
                Need getOT() to work poperly
        '''

        totalHrs = self.getHrs()
        otHrs = self.getOT()
        rtHrs = list()
        for i in range(len(self.report)):
            if re.search("[0-9]", self.report[i][0]) is not None:
                rtHrs.append(self.report[i][1]-otHrs[i])
        return rtHrs


def dailyHrs(sheet, control):
    for i in range(32, sheet.nrows):
        if sheet.cell_value(rowx=i, colx=25) == "":
            pass
        else:
            print("{0}, 25, \"{1}\", \"{2}\"".format(
                i, sheet.cell_value(rowx=i, colx=25), control))
            control = + 8


def hrsFormatter(arr):
    if arr == "":
        return 0

    else:
        arr = arr.split(":")
        heap = [float(i) for i in arr]

        if heap[1] == 15:
            heap[1] = .25
        elif heap[1] == 30:
            heap[1] = .50
        elif heap[1] == 45:
            heap[1] = .75

        return heap[0] + heap[1]


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


print("\"{0}\", \"{1}\", {2}".format(
    users[2].date, users[2].name, users[2].getDates()
))

for i in range(len(users)):
    print("{0}".format(
        users[i].getRT()
    ))
