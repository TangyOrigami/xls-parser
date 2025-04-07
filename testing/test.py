import xlrd
from util.user import User
from util.parser import Parser as p

workbook = xlrd.open_workbook('../sample-data/payroll-1.xls')

newUsers = []

for i in range(0, workbook.nsheets):
    currentSheet = workbook.sheet_by_index(i)
    date = p.xlsParser(sheet=currentSheet, mincolx=0, minrowy=0,
                       maxcolx=25, maxrowy=25, target="[0-9].(AM|PM)",
                       xbuff=None)

    name = p.xlsParser(sheet=currentSheet, mincolx=0, minrowy=0,
                       maxcolx=35, maxrowy=35, target="User Name:", xbuff=2)

    dailyHrsCol = p.xlsParser(sheet=currentSheet,
                              mincolx=0, minrowy=0,
                              maxcolx=currentSheet.ncols,
                              maxrowy=currentSheet.nrows,
                              target="DAILY",
                              xbuff=None)[1]

    temp = []

    temp.append(p.xlsParser(sheet=currentSheet,
                            mincolx=dailyHrsCol[1], minrowy=dailyHrsCol[0]+1,
                            maxcolx=dailyHrsCol[1]+1,
                            maxrowy=currentSheet.nrows,
                            target="[0-9]*:[0-9]*",
                            xbuff=None)
                )

    dates = []
    hrs = []
    datesNhrs = []

    for i in range(0, len(temp[0]), 2):
        hrs.append(p.hrsFormatter(temp[0][i]))

    for i in range(1, len(temp[0]), 2):
        currDate = [temp[0][i][0], 1]
        dates.append(
            f"{currentSheet.cell_value(rowx=currDate[0], colx=currDate[1])}")

    for i in range(len(dates)):
        datesNhrs.append([dates[i], hrs[i]])

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
