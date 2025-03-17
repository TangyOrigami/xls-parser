import xlrd
from user import User
from parser import Parser as p

workbook = xlrd.open_workbook('MAIN OFFICE DETAIL PAYROLL REPORT.xls')


newUsers = []

for i in range(0, workbook.nsheets):
    currentSheet = workbook.sheet_by_index(i)
    date = p.xlsParser(sheet=currentSheet, mincolx=0, minrowy=0,
                       maxcolx=25, maxrowy=25, target="[0-9].(AM)", xbuff=None)

    name = p.xlsParser(sheet=currentSheet, mincolx=0, minrowy=0,
                       maxcolx=35, maxrowy=35, target="User Name:", xbuff=2)

    dailyHrsCol = p.xlsParser(sheet=workbook.sheet_by_index(i),
                              mincolx=0, minrowy=0,
                              maxcolx=currentSheet.ncols,
                              maxrowy=currentSheet.nrows,
                              target="DAILY",
                              xbuff=None)[1]

    temp = []

    temp.append(p.xlsParser(sheet=workbook.sheet_by_index(i),
                            mincolx=dailyHrsCol[1], minrowy=dailyHrsCol[0]+1,
                            maxcolx=dailyHrsCol[1]+1,
                            maxrowy=currentSheet.nrows,
                            target="[0-9]*:[0-9]*",
                            xbuff=None)
                )

    dates = []
    allHrs = []
    datesNhrs = []

    for i in range(0, len(temp[0]), 2):
        allHrs.append(p.hrsFormatter(temp[0][i]))

    for i in range(1, len(temp[0]), 2):
        currDate = [temp[0][i][0], 1]
        dates.append(
            f"{currentSheet.cell_value(rowx=currDate[0], colx=currDate[1])}")

    for i in range(len(dates)):
        datesNhrs.append([dates[i], allHrs[i]])

    newUsers.append(User(name=name[0], date=date[0], report=datesNhrs))


for i in range(len(newUsers)):
    gp = newUsers[i]

    actualWeekly = sum(gp.get_weekday_hrs().values())
    weekend = sum(gp.get_weekend_hrs().values())
    otWeekly = sum(gp.get_ot_logged().values())

    print(f"{i}, '{gp.name}', '{gp.date}'")
    print("Total:\t", sum(gp.get_hrs_wrked().values()),
          "\nRT:\t", actualWeekly - otWeekly,
          "\nOT:\t", otWeekly, "\nWknd:\t", weekend,
          "\nLog:\n", gp.get_hrs_wrked())
    print()

'''
    TODO:

        ?. Design schema for saving data and creating relations, RDBMS.
'''
